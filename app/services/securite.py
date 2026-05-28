# ============================================================
# services/securite.py — Hachage des mots de passe + JWT
# ============================================================
# Ce fichier centralise toute la logique de sécurité :
#   - Hachage et vérification des mots de passe (bcrypt)
#   - Création et décodage des tokens JWT
#   - Vérification de la politique de mot de passe

import re
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import parametres

# Contexte de hachage utilisant bcrypt
contexte_hachage = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Mots de passe ──────────────────────────────────────────

def hacher_mot_de_passe(mot_de_passe: str) -> str:
    """Transforme un mot de passe en clair en hash bcrypt."""
    return contexte_hachage.hash(mot_de_passe)


def verifier_mot_de_passe(mot_de_passe_clair: str, hash_stocke: str) -> bool:
    """Vérifie qu'un mot de passe correspond au hash stocké en base."""
    return contexte_hachage.verify(mot_de_passe_clair, hash_stocke)


def valider_politique_mdp(mot_de_passe: str) -> list[str]:
    """
    Vérifie la politique de mot de passe.
    Retourne une liste d'erreurs (vide si tout est valide).

    Règles :
      - Minimum 8 caractères
      - Au moins une lettre majuscule
      - Au moins un chiffre
      - Au moins un caractère spécial
    """
    erreurs = []

    if len(mot_de_passe) < 8:
        erreurs.append("Au moins 8 caractères requis")
    if not re.search(r"[A-Z]", mot_de_passe):
        erreurs.append("Au moins une lettre majuscule requise")
    if not re.search(r"\d", mot_de_passe):
        erreurs.append("Au moins un chiffre requis")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-]", mot_de_passe):
        erreurs.append("Au moins un caractère spécial requis (!@#$%...)")

    return erreurs


# ── Tokens JWT ─────────────────────────────────────────────

def creer_token_acces(donnees: dict) -> str:
    """
    Génère un token JWT signé avec la clé secrète.
    Le token expire après DUREE_TOKEN_MINUTES minutes.
    """
    contenu = donnees.copy()
    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=parametres.DUREE_TOKEN_MINUTES
    )
    contenu.update({"exp": expiration})

    return jwt.encode(
        contenu,
        parametres.CLE_SECRETE,
        algorithm=parametres.ALGORITHME,
    )


def decoder_token(token: str) -> dict | None:
    """
    Décode et valide un token JWT.
    Retourne les données du token ou None si invalide/expiré.
    """
    try:
        donnees = jwt.decode(
            token,
            parametres.CLE_SECRETE,
            algorithms=[parametres.ALGORITHME],
        )
        return donnees
    except JWTError:
        return None


# ── Tokens aléatoires (vérification email, reset) ──────────

def generer_token_securise() -> str:
    """
    Génère un token aléatoire cryptographiquement sûr (64 hex chars).
    Utilisé pour la vérification email et la réinitialisation du mdp.
    """
    return secrets.token_urlsafe(32)
