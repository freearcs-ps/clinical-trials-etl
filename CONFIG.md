# Configuration des Variables d'Environnement

## Configuration pour le Développement Local

1. Copiez le fichier `.env.example` vers `.env` :
   ```bash
   cp .env.example .env
   ```

2. Éditez le fichier `.env` avec vos vraies valeurs MongoDB :
   ```
   MONGODB_URI=mongodb+srv://votre_username:votre_password@cluster.mongodb.net/?retryWrites=true&w=majority&appName=VotreApp
   MONGODB_DATABASE=clinical_trials_db
   ```

## Configuration pour Streamlit Cloud

### Méthode 1 : Via l'interface web Streamlit Cloud

1. Allez sur [share.streamlit.io](https://share.streamlit.io)
2. Sélectionnez votre application
3. Cliquez sur "Settings" > "Secrets"
4. Ajoutez vos secrets au format TOML :
   ```toml
   MONGODB_URI = "mongodb+srv://votre_username:votre_password@cluster.mongodb.net/?retryWrites=true&w=majority&appName=VotreApp"
   MONGODB_DATABASE = "clinical_trials_db"
   ```

### Méthode 2 : Via le fichier secrets.toml (pour test local)

1. Créez le dossier `.streamlit/` s'il n'existe pas
2. Copiez le fichier d'exemple :
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
3. Éditez le fichier `.streamlit/secrets.toml` avec vos vraies valeurs

## ⚠️ Sécurité

- **JAMAIS** de commiter les fichiers `.env` ou `.streamlit/secrets.toml` dans Git
- Ces fichiers sont déjà dans le `.gitignore`
- Utilisez des mots de passe forts pour MongoDB
- Restreignez l'accès réseau à votre cluster MongoDB si possible

## Test de la Configuration

L'application vérifie automatiquement la présence des variables d'environnement au démarrage et affiche une erreur claire si elles sont manquantes.
