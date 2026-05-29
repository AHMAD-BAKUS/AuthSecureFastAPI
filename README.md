# 🔐 AuthSecure — TP Flux d'Authentification (FastAPI)

## Équipe

| # | Nom | Rôle |
|---|-----|------|
| 1 | AHMAD | Backend & Sécurité |
| 2 | Membre 2 | Routes & Logique métier |
| 3 | Membre 3 | Frontend & Déploiement | 

---

Application web d'authentification complète développée avec **FastAPI**, couvrant les 4 flux du TP :

| Flux | Description |
|------|-------------|
| **01 Inscription** | Politique mot de passe, vérification email, anti-énumération |
| **02 Connexion** | Anti brute-force, compteur de tentatives, message générique |
| **03 Réinitialisation** | Token usage unique, expiration 15 min, réponse neutre |
| **04 Déconnexion** | Invalidation côté serveur, suppression cookie httpOnly |

---

## Structure du projet

```
auth_tp/
├── main.py                     # Point d'entrée FastAPI
├── requirements.txt            # Dépendances Python
├── app/
│   ├── config.py               # Paramètres globaux (JWT, BDD...)
│   ├── database.py             # Connexion SQLite + session async
│   ├── models/
│   │   └── utilisateur.py      # Table utilisateurs (SQLAlchemy)
│   ├── routes/
│   │   └── auth.py             # Toutes les routes d'authentification
│   └── services/
│       ├── securite.py         # Hachage bcrypt + JWT + validation mdp
│       └── email.py            # Simulation envoi email (affichage console)
├── templates/                  # Pages HTML (Jinja2)
│   ├── base.html               # Layout commun à toutes les pages
│   ├── inscription.html        # Flux 01
│   ├── connexion.html          # Flux 02
│   ├── demande_reset.html      # Flux 03 — étape 1
│   ├── nouveau_mdp.html        # Flux 03 — étape 2
│   ├── tableau_de_bord.html    # Page protégée (après connexion)
│   └── message.html            # Page de confirmation générique
└── static/                     # CSS et JS additionnels (dossier prêt)
```

---

## Installation et lancement

### 1. Cloner le projet

```bash
git clone <url-du-repo>
cd auth_tp
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

> ⚠️ Si erreur bcrypt : `pip install bcrypt==4.0.1`

### 4. Lancer l'application

```bash
python main.py
```

Puis ouvrir : **http://127.0.0.1:8000**

---

## Tester les 4 flux

### Flux 01 — Inscription
1. Aller sur http://127.0.0.1:8000/auth/inscription
2. Remplir le formulaire (tester un mot de passe faible pour voir la validation)
3. Après soumission → **copier le lien de vérification affiché dans la console**
4. Coller le lien dans le navigateur pour activer le compte

### Flux 02 — Connexion
1. Aller sur http://127.0.0.1:8000/auth/connexion
2. Se connecter avec email + mot de passe
3. Tester 5 mauvaises tentatives → voir le verrouillage du compte

### Flux 03 — Réinitialisation
1. Aller sur http://127.0.0.1:8000/auth/demande-reset
2. Entrer votre email → **copier le lien affiché en console**
3. Coller le lien → saisir un nouveau mot de passe
4. Tester le lien une 2e fois → voir "lien déjà utilisé"
5. Attendre 15 min (ou modifier `DUREE_TOKEN_MINUTES` dans config.py pour tester)

### Flux 04 — Déconnexion
1. Se connecter et accéder au tableau de bord
2. Cliquer "Se déconnecter" → le cookie JWT est supprimé côté serveur
3. Tenter d'accéder à http://127.0.0.1:8000/auth/tableau-de-bord → redirection automatique

---

## Sécurités implémentées

| Mécanisme | Détail |
|-----------|--------|
| **Hachage bcrypt** | Les mots de passe ne sont jamais stockés en clair |
| **Anti-énumération** | Réponse identique que l'email existe ou non (inscription + reset) |
| **Anti brute-force** | Compteur de tentatives, verrouillage après 5 échecs |
| **Message générique** | "Identifiants invalides" sans préciser lequel est faux |
| **Token à usage unique** | Token reset invalidé immédiatement après utilisation |
| **Expiration du token** | Lien de reset valable 15 minutes seulement |
| **Cookie httpOnly** | Le token JWT est inaccessible au JavaScript (protection XSS) |
| **Politique de mot de passe** | 8 car. min., majuscule, chiffre, caractère spécial |
| **Vérification email** | Le compte n'est actif qu'après clic sur le lien envoyé |

---

## Variables d'environnement (optionnel)

Créer un fichier `.env` à la racine :

```env
CLE_SECRETE=votre_cle_secrete_tres_longue_ici
DUREE_TOKEN_MINUTES=30
```

---

## Technologies utilisées

- **FastAPI** — Framework web asynchrone
- **SQLAlchemy + aiosqlite** — ORM async + base SQLite
- **Passlib + bcrypt** — Hachage des mots de passe
- **python-jose** — Gestion des tokens JWT
- **Jinja2** — Moteur de templates HTML
- **Uvicorn** — Serveur ASGI
