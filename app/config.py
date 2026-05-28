# ============================================================
# config.py — Paramètres globaux de l'application
# ============================================================

from pydantic_settings import BaseSettings
import secrets

class Parametres(BaseSettings):
    # Nom de l'application
    NOM_APP: str = "AuthSecure"

    # Clé secrète pour signer les tokens JWT
    # En production : définir via variable d'environnement SECRET_KEY
    CLE_SECRETE: str = secrets.token_hex(32)

    # Algorithme de signature JWT
    ALGORITHME: str = "HS256"

    # Durée de vie du token d'accès (en minutes)
    DUREE_TOKEN_MINUTES: int = 30

    # URL de la base de données SQLite
    URL_BASE_DONNEES: str = "sqlite+aiosqlite:///./auth_app.db"

    class Config:
        env_file = ".env"

# Instance unique des paramètres (utilisée dans toute l'app)
parametres = Parametres()
