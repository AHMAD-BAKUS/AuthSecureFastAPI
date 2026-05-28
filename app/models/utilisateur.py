# ============================================================
# models/utilisateur.py — Structure de la table "utilisateurs"
# ============================================================
# Ce fichier définit ce que représente un utilisateur en base.
# SQLAlchemy se charge de créer la table automatiquement.

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Utilisateur(Base):
    """
    Table SQL : utilisateurs
    Chaque ligne = un compte utilisateur enregistré
    """
    __tablename__ = "utilisateurs"

    # Identifiant unique auto-incrémenté
    id = Column(Integer, primary_key=True, index=True)

    # Nom d'affichage
    nom = Column(String(100), nullable=False)

    # Email unique (utilisé pour la connexion)
    email = Column(String(255), unique=True, index=True, nullable=False)

    # Mot de passe haché (jamais en clair en base)
    mot_de_passe_hache = Column(String(255), nullable=False)

    # Indique si l'email a été vérifié
    email_verifie = Column(Boolean, default=False)

    # Token de vérification email (usage unique, durée limitée)
    token_verification = Column(String(255), nullable=True)

    # Token de réinitialisation de mot de passe
    token_reset = Column(String(255), nullable=True)

    # Date d'expiration du token de reset (15 minutes)
    expiration_token_reset = Column(DateTime, nullable=True)

    # Compteur de tentatives de connexion échouées (anti brute-force)
    tentatives_echec = Column(Integer, default=0)

    # Compte temporairement verrouillé après trop d'échecs
    verrouille = Column(Boolean, default=False)

    # Date de création du compte
    cree_le = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Utilisateur id={self.id} email={self.email}>"
