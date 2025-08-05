# Configuration des Variables d'Environnement

## 🚨 Problème SSL sur Streamlit Cloud ?

**Consultez le guide complet : [SSL_TROUBLESHOOTING.md](SSL_TROUBLESHOOTING.md)**

## Configuration pour le Développement Local

1. Copiez le fichier `.env.example` vers `.env` :
   ```bash
   cp .env.example .env
   ```

2. Éditez le fichier `.env` avec vos vraies valeurs MongoDB (URI optimisée pour SSL) :
   ```
   MONGODB_URI=mongodb+srv://votre_username:votre_password@cluster.mongodb.net/?retryWrites=true&w=majority&appName=VotreApp&ssl=true&tlsAllowInvalidCertificates=true&connectTimeoutMS=30000&serverSelectionTimeoutMS=30000
   MONGODB_DATABASE=clinical_trials_db
   ```

## Configuration pour Streamlit Cloud

### Méthode 1 : Via l'interface web Streamlit Cloud (RECOMMANDÉE)

1. Allez sur [share.streamlit.io](https://share.streamlit.io)
2. Sélectionnez votre application
3. Cliquez sur "Settings" > "Secrets"
4. Ajoutez vos secrets au format TOML avec l'URI optimisée SSL :
   ```toml
   MONGODB_URI = "mongodb+srv://votre_username:votre_password@cluster.mongodb.net/?retryWrites=true&w=majority&appName=VotreApp&ssl=true&tlsAllowInvalidCertificates=true&connectTimeoutMS=30000&serverSelectionTimeoutMS=30000"
   MONGODB_DATABASE = "clinical_trials_db"
   ```

### Méthode 2 : Via le fichier secrets.toml (pour test local)

1. Créez le dossier `.streamlit/` s'il n'existe pas
2. Copiez le fichier d'exemple :
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
3. Éditez le fichier `.streamlit/secrets.toml` avec vos vraies valeurs

## 🔧 Paramètres SSL Importants

L'URI MongoDB inclut maintenant des paramètres SSL spécifiques pour résoudre les problèmes de connexion sur Streamlit Cloud :

- `ssl=true` : Force l'utilisation de SSL
- `tlsAllowInvalidCertificates=true` : Permet les certificats auto-signés
- `connectTimeoutMS=30000` : Timeout de connexion étendu (30s)
- `serverSelectionTimeoutMS=30000` : Timeout de sélection serveur étendu (30s)

## 🛡️ Configuration MongoDB Atlas

1. **Network Access** : Ajoutez `0.0.0.0/0` pour permettre l'accès depuis Streamlit Cloud
2. **Database User** : Vérifiez que l'utilisateur a les permissions de lecture
3. **Cluster** : Assurez-vous que le cluster est actif

## ⚠️ Sécurité

- **JAMAIS** de commiter les fichiers `.env` ou `.streamlit/secrets.toml` dans Git
- Ces fichiers sont déjà dans le `.gitignore`
- Utilisez des mots de passe forts pour MongoDB
- Restreignez l'accès réseau à votre cluster MongoDB si possible

## 🧪 Test de la Configuration

L'application vérifie automatiquement la présence des variables d'environnement au démarrage et :
- Affiche une erreur claire si elles sont manquantes
- Tente une connexion de secours en cas d'échec SSL
- Affiche des messages de debug pour diagnostiquer les problèmes

## 📋 Versions Requises

Assurez-vous d'avoir les bonnes versions dans `requirements.txt` :
```
pymongo>=4.6.0
dnspython>=2.6.1
streamlit>=1.47.1
```

Les anciennes versions de pymongo peuvent causer des problèmes SSL sur Streamlit Cloud.
