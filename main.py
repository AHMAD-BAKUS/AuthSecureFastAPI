# ============================================================
# main.py — Point d'entrée de l'application FastAPI
# ============================================================

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.database import initialiser_base
from app.routes.auth import routeur as routeur_auth
from app.config import parametres

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("auth_app")


@asynccontextmanager
async def duree_de_vie(app: FastAPI):
    """
    Actions au démarrage et à l'arrêt de l'application.
    Démarrage : création des tables en base de données.
    """
    logger.info("Démarrage de l'application — initialisation de la base...")
    await initialiser_base()
    logger.info("Base de données prête.")
    yield
    logger.info("Arrêt de l'application.")


# Création de l'application FastAPI
app = FastAPI(
    title=parametres.NOM_APP,
    description="TP Sécurité — Flux d'authentification complets avec FastAPI",
    version="1.0.0",
    lifespan=duree_de_vie,
)

# Fichiers statiques (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Enregistrement des routes d'authentification
app.include_router(routeur_auth)


@app.get("/")
async def accueil():
    """Redirige la racine vers la page de connexion."""
    return RedirectResponse(url="/auth/connexion")


# ── Lancement direct avec "python main.py" ──
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)