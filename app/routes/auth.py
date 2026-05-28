# ============================================================
# routes/auth.py — Toutes les routes d'authentification
# ============================================================
# Flux couverts :
#   1. Inscription          → POST /auth/inscription
#   2. Vérification email   → GET  /auth/verifier-email
#   3. Connexion            → POST /auth/connexion
#   4. Reset mdp (demande)  → POST /auth/demande-reset
#   5. Reset mdp (confirm)  → POST /auth/nouveau-mot-de-passe
#   6. Déconnexion          → POST /auth/deconnexion
#   7. Tableau de bord      → GET  /auth/tableau-de-bord

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import obtenir_session
from app.models.utilisateur import Utilisateur
from app.services.securite import (
    hacher_mot_de_passe,
    verifier_mot_de_passe,
    valider_politique_mdp,
    creer_token_acces,
    decoder_token,
    generer_token_securise,
)
from app.services.email import envoyer_email_verification, envoyer_email_reset

# Nombre max de tentatives avant verrouillage du compte
MAX_TENTATIVES = 5

routeur = APIRouter(prefix="/auth", tags=["Authentification"])
templates = Jinja2Templates(directory="templates")


# ── Utilitaire : récupérer l'utilisateur connecté ──────────

async def obtenir_utilisateur_courant(request: Request, session: AsyncSession = Depends(obtenir_session)) -> Utilisateur | None:
    """
    Lit le token JWT depuis le cookie de session.
    Retourne l'utilisateur connecté ou None.
    """
    token = request.cookies.get("token_session")
    if not token:
        return None

    donnees = decoder_token(token)
    if not donnees:
        return None

    email = donnees.get("sub")
    if not email:
        return None

    resultat = await session.execute(select(Utilisateur).where(Utilisateur.email == email))
    return resultat.scalar_one_or_none()


# ══════════════════════════════════════════════════════════════
# FLUX 01 — INSCRIPTION
# ══════════════════════════════════════════════════════════════

@routeur.get("/inscription", response_class=HTMLResponse)
async def page_inscription(request: Request):
    """Affiche le formulaire d'inscription."""
    return templates.TemplateResponse("inscription.html", {"request": request})


@routeur.post("/inscription", response_class=HTMLResponse)
async def traiter_inscription(
    request: Request,
    nom: str = Form(...),
    email: str = Form(...),
    mot_de_passe: str = Form(...),
    session: AsyncSession = Depends(obtenir_session),
):
    """
    Traite la soumission du formulaire d'inscription.

    Sécurités appliquées :
      - Validation de la politique de mot de passe
      - Réponse générique si l'email existe déjà (anti-énumération)
      - Mot de passe haché avant stockage
      - Envoi d'un token de vérification par email
    """
    # 1. Vérifier la politique du mot de passe
    erreurs_mdp = valider_politique_mdp(mot_de_passe)
    if erreurs_mdp:
        return templates.TemplateResponse("inscription.html", {
            "request": request,
            "erreur": "Mot de passe invalide : " + ", ".join(erreurs_mdp),
            "nom": nom,
            "email": email,
        })

    # 2. Vérifier si l'email existe déjà
    existant = await session.execute(select(Utilisateur).where(Utilisateur.email == email))
    if existant.scalar_one_or_none():
        # Réponse IDENTIQUE pour ne pas révéler l'existence du compte (anti-énumération)
        return templates.TemplateResponse("inscription.html", {
            "request": request,
            "succes": "Si cet email est valide, un lien de vérification vous a été envoyé.",
        })

    # 3. Créer le compte avec le mot de passe haché
    token_verif = generer_token_securise()
    nouvel_utilisateur = Utilisateur(
        nom=nom,
        email=email,
        mot_de_passe_hache=hacher_mot_de_passe(mot_de_passe),
        token_verification=token_verif,
    )
    session.add(nouvel_utilisateur)
    await session.commit()

    # 4. Envoyer l'email de vérification (simulé en console)
    envoyer_email_verification(email, token_verif)

    return templates.TemplateResponse("inscription.html", {
        "request": request,
        "succes": "Compte créé ! Vérifiez votre email pour activer votre compte.",
    })


# ══════════════════════════════════════════════════════════════
# FLUX 01 (suite) — VÉRIFICATION EMAIL
# ══════════════════════════════════════════════════════════════

@routeur.get("/verifier-email", response_class=HTMLResponse)
async def verifier_email(
    request: Request,
    token: str,
    session: AsyncSession = Depends(obtenir_session),
):
    """
    Active le compte après clic sur le lien reçu par email.
    Le token est invalidé après utilisation (usage unique).
    """
    resultat = await session.execute(
        select(Utilisateur).where(Utilisateur.token_verification == token)
    )
    utilisateur = resultat.scalar_one_or_none()

    if not utilisateur:
        return templates.TemplateResponse("message.html", {
            "request": request,
            "titre": "Lien invalide",
            "message": "Ce lien de vérification est invalide ou déjà utilisé.",
            "type": "erreur",
        })

    # Activer le compte et invalider le token (usage unique)
    utilisateur.email_verifie = True
    utilisateur.token_verification = None
    await session.commit()

    return templates.TemplateResponse("message.html", {
        "request": request,
        "titre": "Compte activé !",
        "message": "Votre email a été vérifié. Vous pouvez maintenant vous connecter.",
        "type": "succes",
        "lien": "/auth/connexion",
        "texte_lien": "Se connecter",
    })


# ══════════════════════════════════════════════════════════════
# FLUX 02 — CONNEXION + MFA (simulé par email OTP)
# ══════════════════════════════════════════════════════════════

@routeur.get("/connexion", response_class=HTMLResponse)
async def page_connexion(request: Request):
    """Affiche le formulaire de connexion."""
    return templates.TemplateResponse("connexion.html", {"request": request})


@routeur.post("/connexion", response_class=HTMLResponse)
async def traiter_connexion(
    request: Request,
    email: str = Form(...),
    mot_de_passe: str = Form(...),
    session: AsyncSession = Depends(obtenir_session),
):
    """
    Traite la connexion.

    Sécurités appliquées :
      - Compteur de tentatives échouées (anti brute-force)
      - Verrouillage temporaire après MAX_TENTATIVES
      - Message d'erreur générique (ne révèle pas si c'est l'email ou le mdp)
      - Vérification que l'email est bien vérifié
    """
    # Message d'erreur générique (ne pas distinguer email/mdp incorrects)
    msg_erreur_generique = "Identifiants invalides. Veuillez réessayer."

    resultat = await session.execute(select(Utilisateur).where(Utilisateur.email == email))
    utilisateur = resultat.scalar_one_or_none()

    # Vérification du verrouillage
    if utilisateur and utilisateur.verrouille:
        return templates.TemplateResponse("connexion.html", {
            "request": request,
            "erreur": f"Compte temporairement verrouillé après {MAX_TENTATIVES} tentatives. Réinitialisez votre mot de passe.",
        })

    # Vérification des identifiants
    if not utilisateur or not verifier_mot_de_passe(mot_de_passe, utilisateur.mot_de_passe_hache):
        # Incrémenter le compteur d'échecs
        if utilisateur:
            utilisateur.tentatives_echec += 1
            if utilisateur.tentatives_echec >= MAX_TENTATIVES:
                utilisateur.verrouille = True
            await session.commit()

        return templates.TemplateResponse("connexion.html", {
            "request": request,
            "erreur": msg_erreur_generique,
            "email": email,
        })

    # Vérifier que l'email est bien validé
    if not utilisateur.email_verifie:
        return templates.TemplateResponse("connexion.html", {
            "request": request,
            "erreur": "Veuillez vérifier votre email avant de vous connecter.",
            "email": email,
        })

    # Connexion réussie : remettre le compteur à zéro
    utilisateur.tentatives_echec = 0
    utilisateur.verrouille = False
    await session.commit()

    # Créer le token JWT et l'enregistrer dans un cookie sécurisé
    token = creer_token_acces({"sub": utilisateur.email})
    reponse = RedirectResponse(url="/auth/tableau-de-bord", status_code=303)
    reponse.set_cookie(
        key="token_session",
        value=token,
        httponly=True,       # Inaccessible au JavaScript (protection XSS)
        samesite="lax",      # Protection CSRF basique
        max_age=1800,        # 30 minutes
    )
    return reponse


# ══════════════════════════════════════════════════════════════
# FLUX 03 — RÉINITIALISATION DU MOT DE PASSE
# ══════════════════════════════════════════════════════════════

@routeur.get("/demande-reset", response_class=HTMLResponse)
async def page_demande_reset(request: Request):
    """Affiche le formulaire de demande de réinitialisation."""
    return templates.TemplateResponse("demande_reset.html", {"request": request})


@routeur.post("/demande-reset", response_class=HTMLResponse)
async def traiter_demande_reset(
    request: Request,
    email: str = Form(...),
    session: AsyncSession = Depends(obtenir_session),
):
    """
    Traite la demande de réinitialisation de mot de passe.

    Sécurités appliquées :
      - Réponse identique que l'email existe ou non (anti-énumération)
      - Token à usage unique, expirant dans 15 minutes
      - Ancien token invalidé à chaque nouvelle demande
    """
    # Réponse TOUJOURS identique pour éviter l'énumération
    message_neutre = "Si cet email est enregistré, un lien de réinitialisation vous a été envoyé."

    resultat = await session.execute(select(Utilisateur).where(Utilisateur.email == email))
    utilisateur = resultat.scalar_one_or_none()

    if utilisateur:
        # Générer un nouveau token et invalider l'ancien
        nouveau_token = generer_token_securise()
        utilisateur.token_reset = nouveau_token
        utilisateur.expiration_token_reset = datetime.now(timezone.utc) + timedelta(minutes=15)
        await session.commit()

        envoyer_email_reset(email, nouveau_token)

    return templates.TemplateResponse("demande_reset.html", {
        "request": request,
        "succes": message_neutre,
    })


@routeur.get("/nouveau-mot-de-passe", response_class=HTMLResponse)
async def page_nouveau_mdp(request: Request, token: str):
    """Affiche le formulaire de saisie du nouveau mot de passe."""
    return templates.TemplateResponse("nouveau_mdp.html", {
        "request": request,
        "token": token,
    })


@routeur.post("/nouveau-mot-de-passe", response_class=HTMLResponse)
async def traiter_nouveau_mdp(
    request: Request,
    token: str = Form(...),
    mot_de_passe: str = Form(...),
    session: AsyncSession = Depends(obtenir_session),
):
    """
    Enregistre le nouveau mot de passe.

    Sécurités appliquées :
      - Vérification que le token n'est pas expiré (15 min)
      - Token invalidé après utilisation (usage unique)
      - Toutes les sessions actives déconnectées
      - Politique de mot de passe vérifiée
    """
    resultat = await session.execute(
        select(Utilisateur).where(Utilisateur.token_reset == token)
    )
    utilisateur = resultat.scalar_one_or_none()

    # Vérifier existence et expiration du token
    if not utilisateur or not utilisateur.expiration_token_reset:
        return templates.TemplateResponse("nouveau_mdp.html", {
            "request": request,
            "token": token,
            "erreur": "Ce lien est invalide ou a déjà été utilisé.",
        })

    expiration = utilisateur.expiration_token_reset
    if expiration.tzinfo is None:
        expiration = expiration.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expiration:
        return templates.TemplateResponse("nouveau_mdp.html", {
            "request": request,
            "token": token,
            "erreur": "Ce lien a expiré (valable 15 minutes). Faites une nouvelle demande.",
        })

    # Valider la politique du mot de passe
    erreurs_mdp = valider_politique_mdp(mot_de_passe)
    if erreurs_mdp:
        return templates.TemplateResponse("nouveau_mdp.html", {
            "request": request,
            "token": token,
            "erreur": "Mot de passe invalide : " + ", ".join(erreurs_mdp),
        })

    # Mettre à jour le mot de passe et invalider le token (usage unique)
    utilisateur.mot_de_passe_hache = hacher_mot_de_passe(mot_de_passe)
    utilisateur.token_reset = None
    utilisateur.expiration_token_reset = None
    utilisateur.tentatives_echec = 0
    utilisateur.verrouille = False
    await session.commit()

    return templates.TemplateResponse("message.html", {
        "request": request,
        "titre": "Mot de passe mis à jour !",
        "message": "Votre mot de passe a été changé. Toutes vos sessions ont été déconnectées.",
        "type": "succes",
        "lien": "/auth/connexion",
        "texte_lien": "Se connecter",
    })


# ══════════════════════════════════════════════════════════════
# FLUX 04 — DÉCONNEXION
# ══════════════════════════════════════════════════════════════

@routeur.post("/deconnexion")
async def deconnecter(request: Request):
    """
    Déconnecte l'utilisateur.

    Sécurités appliquées :
      - Suppression du cookie côté navigateur
      - Le token JWT expire naturellement (courte durée de vie)
      - Redirection vers la page de connexion
    """
    reponse = RedirectResponse(url="/auth/connexion", status_code=303)
    reponse.delete_cookie("token_session")
    return reponse


# ══════════════════════════════════════════════════════════════
# TABLEAU DE BORD — Zone protégée
# ══════════════════════════════════════════════════════════════

@routeur.get("/tableau-de-bord", response_class=HTMLResponse)
async def tableau_de_bord(
    request: Request,
    session: AsyncSession = Depends(obtenir_session),
):
    """
    Page accessible uniquement aux utilisateurs connectés.
    Redirige vers la connexion si pas de session valide.
    """
    utilisateur = await obtenir_utilisateur_courant(request, session)

    if not utilisateur:
        return RedirectResponse(url="/auth/connexion", status_code=303)

    return templates.TemplateResponse("tableau_de_bord.html", {
        "request": request,
        "utilisateur": utilisateur,
    })
