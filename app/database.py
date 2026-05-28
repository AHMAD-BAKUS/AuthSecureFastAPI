# ============================================================
# database.py — Connexion et initialisation de la base SQLite
# ============================================================

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import parametres


# Moteur de base de données asynchrone
moteur = create_async_engine(
    parametres.URL_BASE_DONNEES,
    echo=False,  # Mettre True pour afficher les requêtes SQL en console
)

# Fabrique de sessions asynchrones
SessionLocale = async_sessionmaker(
    bind=moteur,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    """Classe de base dont héritent tous les modèles SQLAlchemy"""
    pass


async def initialiser_base():
    """
    Crée toutes les tables en base si elles n'existent pas encore.
    Appelée au démarrage de l'application.
    """
    # Import nécessaire pour que SQLAlchemy découvre les modèles
    from app.models import utilisateur  # noqa

    async with moteur.begin() as connexion:
        await connexion.run_sync(Base.metadata.create_all)


async def obtenir_session():
    """
    Dépendance FastAPI : fournit une session de base de données
    à chaque requête, puis la ferme proprement.
    """
    async with SessionLocale() as session:
        yield session
