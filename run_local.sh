#!/bin/bash

# Script pour configurer les variables d'environnement pour le développement local
# Utilisez ce script au lieu de créer un fichier .env si vous préférez

export MONGODB_URI="mongodb+srv://votre_username:votre_password@cluster.mongodb.net/?retryWrites=true&w=majority&appName=VotreApp"
export MONGODB_DATABASE="clinical_trials_db"

echo "Variables d'environnement configurées pour MongoDB"
echo "MONGODB_DATABASE: $MONGODB_DATABASE"
echo "MONGODB_URI configuré (URI masqué pour sécurité)"

# Lancer l'application Streamlit
echo "Lancement de l'application Streamlit..."
streamlit run st_trial_analytics.py
