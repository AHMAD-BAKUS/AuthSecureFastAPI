# ============================================================
# services/email.py — Simulation du service d'envoi d'emails
# ============================================================
# Dans ce TP, les emails sont simulés : ils s'affichent dans
# la console au lieu d'être vraiment envoyés.
# En production, on remplacerait par SMTP (smtplib, SendGrid…)

import logging

logger = logging.getLogger("auth_app.email")


def envoyer_email_verification(email: str, token: str, base_url: str = "http://127.0.0.1:8000"):
    """
    Simule l'envoi d'un email de vérification de compte.
    Le lien s'affiche dans la console.
    """
    lien = f"{base_url}/auth/verifier-email?token={token}"

    logger.info("=" * 60)
    logger.info("📧  EMAIL DE VÉRIFICATION (simulé)")
    logger.info(f"   Destinataire : {email}")
    logger.info(f"   Lien         : {lien}")
    logger.info("   Ce lien expire dans 24 heures.")
    logger.info("=" * 60)

    # Affichage console pour faciliter les tests
    print("\n" + "="*60)
    print("📧  EMAIL DE VÉRIFICATION (simulé — copier ce lien)")
    print(f"   → {lien}")
    print("="*60 + "\n")


def envoyer_email_reset(email: str, token: str, base_url: str = "http://127.0.0.1:8000"):
    """
    Simule l'envoi d'un email de réinitialisation de mot de passe.
    Le lien s'affiche dans la console.
    """
    lien = f"{base_url}/auth/nouveau-mot-de-passe?token={token}"

    logger.info("=" * 60)
    logger.info("🔑  EMAIL DE RÉINITIALISATION (simulé)")
    logger.info(f"   Destinataire : {email}")
    logger.info(f"   Lien         : {lien}")
    logger.info("   Ce lien expire dans 15 minutes.")
    logger.info("=" * 60)

    print("\n" + "="*60)
    print("🔑  EMAIL DE RÉINITIALISATION (simulé — copier ce lien)")
    print(f"   → {lien}")
    print("="*60 + "\n")
