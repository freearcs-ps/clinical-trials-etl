#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Application Streamlit pour l'analyse des données d'essais cliniques MongoDB.
Interface interactive pour requêtes avancées et visualisations.

#735252 : Marron/Gris foncé
#3b813b : Vert forêt/Vert foncé
#4aac47 : Vert herbe/Vert clair
#e64f29 : Orange vif/Rouge-orange
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pymongo
from pymongo import MongoClient
import json
import logging
import time
import ssl

# Définition des couleurs de l'entreprise pour une utilisation cohérente
COLORS = {
    "primary": "#735252",  # Marron/Gris foncé
    "secondary": "#3b813b",  # Vert forêt/Vert foncé
    "accent": "#4aac47",  # Vert herbe/Vert clair
    "highlight": "#e64f29",  # Orange vif/Rouge-orange
    "background": "#f9f9f9",  # Fond clair pour meilleur contraste
    "text": "#333333",  # Texte sombre pour lisibilité
}
from datetime import datetime, timedelta
import numpy as np
from collections import Counter
import re
import os
import sys


import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import pymongo


# Configuration de la page
st.set_page_config(
    page_title="Analyseur d'Essais Cliniques",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Application du thème personnalisé avec les couleurs de l'entreprise
st.markdown(
    f"""
<style>
    .stApp {{
        background-color: {COLORS["background"]};
    }}
    .stButton>button {{
        background-color: {COLORS["primary"]};
        color: white;
    }}
    .stButton>button:hover {{
        background-color: {COLORS["secondary"]};
        color: white;
    }}
    h1, h2, h3 {{
        color: {COLORS["primary"]};
    }}
    .stSidebar .sidebar-content {{
        background-color: {COLORS["background"]};
    }}
    .stProgress .st-bo {{
        background-color: {COLORS["accent"]};
    }}
    .stDataFrame tbody tr:nth-child(even) {{
        background-color: {COLORS["background"]};
    }}
    .stSelectbox, .stMultiselect {{
        border-color: {COLORS["secondary"]};
    }}
    .stTabs [data-baseweb="tab-list"] button [data-baseweb="tab"] {{
        color: {COLORS["secondary"]};
    }}
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] [data-baseweb="tab"] {{
        color: {COLORS["primary"]};
    }}
    /* Style pour les éléments mis en évidence avec la couleur orange vif/rouge-orange */
    .highlight {{
        color: {COLORS["highlight"]};
        font-weight: bold;
    }}
    .st-emotion-cache-1gulkj5 {{
        background-color: {COLORS["highlight"]};
        color: white;
    }}
    /* Style pour les métriques */
    .stMetric .st-emotion-cache-16txtl3 {{
        color: {COLORS["highlight"]};
    }}
    /* Style pour les boutons d'action importants */
    .stButton.action-btn>button {{
        background-color: {COLORS["highlight"]};
        color: white;
    }}
    /* Bordures des expanders avec la nouvelle couleur */
    .streamlit-expanderHeader:hover {{
        border-color: {COLORS["highlight"]};
    }}
</style>
""",
    unsafe_allow_html=True,
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ajout du répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TrialAnalytics:
    """Classe pour l'analyse des données d'essais cliniques."""

    def __init__(self, uri: str, database: str):
        self.uri = uri
        self.database = database
        self.client = None
        self.db = None
        self.collection = None

    def connect(self):
        """Établit la connexion à MongoDB avec gestion SSL améliorée."""
        try:
            # Configuration SSL spécifique pour Streamlit Cloud
            import ssl

            # Options de connexion avec SSL/TLS robuste
            client_options = {
                "serverSelectionTimeoutMS": 30000,  # Augmenter le timeout
                "connectTimeoutMS": 30000,
                "socketTimeoutMS": 30000,
                "maxPoolSize": 10,
                "retryWrites": True,
                "w": "majority",
                # Configuration SSL explicite
                "ssl": True,
                "ssl_cert_reqs": ssl.CERT_NONE,  # Désactiver la vérification des certificats
                "ssl_match_hostname": False,
                "tlsAllowInvalidCertificates": True,
                "tlsAllowInvalidHostnames": True,
                # Forcer TLS 1.2+
                "tlsInsecure": True,
            }

            self.client = MongoClient(self.uri, **client_options)
            self.db = self.client[self.database]
            self.collection = self.db.trials  # Nom de collection correct

            # Test de la connexion avec un timeout plus long
            self.client.admin.command("ping")
            return True

        except Exception as e:
            st.error(f"Erreur de connexion MongoDB: {e}")

            # Essayer une connexion de secours avec paramètres simplifiés
            try:
                st.info("🔄 Tentative de connexion de secours...")

                # URI modifiée avec paramètres SSL explicites
                fallback_uri = self.uri
                if "?" in fallback_uri:
                    fallback_uri += "&ssl=true&ssl_cert_reqs=CERT_NONE&tlsAllowInvalidCertificates=true"
                else:
                    fallback_uri += "?ssl=true&ssl_cert_reqs=CERT_NONE&tlsAllowInvalidCertificates=true"

                fallback_options = {
                    "serverSelectionTimeoutMS": 30000,
                    "connectTimeoutMS": 30000,
                    "socketTimeoutMS": 30000,
                }

                self.client = MongoClient(fallback_uri, **fallback_options)
                self.db = self.client[self.database]
                self.collection = self.db.trials

                # Test de la connexion
                self.client.admin.command("ping")
                st.success("✅ Connexion de secours réussie!")
                return True

            except Exception as fallback_error:
                st.error(f"Erreur de connexion de secours: {fallback_error}")
                return False

    def disconnect(self):
        """Ferme la connexion MongoDB."""
        if self.client:
            self.client.close()

    def get_basic_stats(self):
        """Récupère les statistiques de base."""
        try:
            total_trials = self.collection.count_documents({})

            # Statistiques par phase
            phases_pipeline = [
                {
                    "$group": {
                        "_id": "$summary.trial_information.trial_phase",
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"count": -1}},
            ]
            phases = list(self.collection.aggregate(phases_pipeline))

            # Statistiques par pays (Top 10 pour affichage)
            countries_pipeline = [
                {"$unwind": "$locations.countries"},
                {
                    "$group": {
                        "_id": "$locations.countries.country",
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": 10},
            ]
            countries = list(self.collection.aggregate(countries_pipeline))

            # Statistiques par pays (Total complet pour métrique)
            total_countries_pipeline = [
                {"$unwind": "$locations.countries"},
                {"$group": {"_id": "$locations.countries.country"}},
                {"$count": "total"},
            ]
            total_countries_result = list(
                self.collection.aggregate(total_countries_pipeline)
            )
            total_countries = (
                total_countries_result[0]["total"] if total_countries_result else 0
            )

            # Statistiques par conditions médicales
            conditions_pipeline = [
                {
                    "$group": {
                        "_id": "$summary.trial_information.medical_condition",
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": 10},
            ]
            conditions = list(self.collection.aggregate(conditions_pipeline))

            # Toal médical conditions
            total_conditions_pipeline = [
                {
                    "$group": {
                        "_id": "$summary.trial_information.medical_condition",
                    }
                },
                {"$count": "total"},
            ]
            total_conditions_result = list(
                self.collection.aggregate(total_conditions_pipeline)
            )
            total_conditions = (
                total_conditions_result[0]["total"] if total_conditions_result else 0
            )
            # Mise à jour des conditions pour inclure le total

            # Récupération du nombre de domaines thérapeutiques uniques
            total_therapeutic_areas = self.get_therapeutic_areas_count()

            return {
                "total_trials": total_trials,
                "phases": phases,
                "countries": countries,
                "total_countries": total_countries,  # Nouveau: total réel
                "conditions": conditions,
                "total_conditions": total_conditions,  # Nouveau: total réel
                "total_therapeutic_areas": total_therapeutic_areas,  # Nouveau: total des domaines thérapeutiques
            }
        except Exception as e:
            st.error(f"Erreur lors de la récupération des statistiques: {e}")
            return None

    def search_trials_advanced(self, filters):
        """Recherche avancée d'essais cliniques."""
        try:
            query = {}

            # Filtre par phase
            if filters.get("phase") and filters["phase"] != "Toutes":
                query["summary.trial_information.trial_phase"] = {
                    "$regex": filters["phase"],
                    "$options": "i",
                }

            # Filtre par pays
            if filters.get("country") and filters["country"] != "Tous":
                query["locations.countries.country"] = {
                    "$regex": filters["country"],
                    "$options": "i",
                }

            # Filtre par condition médicale
            if filters.get("condition"):
                query["summary.trial_information.medical_condition"] = {
                    "$regex": filters["condition"],
                    "$options": "i",
                }

            # Filtre par sponsor
            if filters.get("sponsor"):
                query["summary.trial_information.sponsor"] = {
                    "$regex": filters["sponsor"],
                    "$options": "i",
                }

            # Filtre par date
            if filters.get("date_from") or filters.get("date_to"):
                date_query = {}
                if filters.get("date_from"):
                    date_query["$gte"] = filters["date_from"].isoformat()
                if filters.get("date_to"):
                    date_query["$lte"] = filters["date_to"].isoformat()
                if date_query:
                    query["date_added"] = date_query

            # Pagination
            skip = filters.get("skip", 0)
            limit = filters.get("limit", 50)

            trials = list(self.collection.find(query).skip(skip).limit(limit))
            total_count = self.collection.count_documents(query)

            return trials, total_count
        except Exception as e:
            st.error(f"Erreur lors de la recherche: {e}")
            return [], 0

    def get_timeline_data(self):
        """Génère des données pour la timeline des essais."""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m",
                                "date": {
                                    "$dateFromString": {"dateString": "$date_added"}
                                },
                            }
                        },
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"_id": 1}},
            ]

            timeline = list(self.collection.aggregate(pipeline))
            return timeline
        except Exception as e:
            st.error(f"Erreur lors de la génération de la timeline: {e}")
            return []

    def get_therapeutic_areas_distribution(self):
        """Analyse la distribution des domaines thérapeutiques."""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$summary.trial_information.therapeutic_area",
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": 15},
            ]

            areas = list(self.collection.aggregate(pipeline))
            return areas
        except Exception as e:
            st.error(f"Erreur lors de l'analyse des domaines thérapeutiques: {e}")
            return []

    def get_therapeutic_areas_count(self):
        """Récupère le nombre total de domaines thérapeutiques uniques."""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$trial_information.trial_details.trial_information.therapeutic_area"
                    }
                },
                {"$match": {"_id": {"$ne": None}}},  # Exclure les valeurs nulles
                {"$count": "total"},
            ]

            result = list(self.collection.aggregate(pipeline))
            return result[0]["total"] if result else 0
        except Exception as e:
            st.error(f"Erreur lors du comptage des domaines thérapeutiques: {e}")
            return 0

    def get_sponsor_analysis(self):
        """Analyse des sponsors d'essais."""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$summary.trial_information.sponsor",
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": 20},
            ]

            sponsors = list(self.collection.aggregate(pipeline))
            return sponsors
        except Exception as e:
            st.error(f"Erreur lors de l'analyse des sponsors: {e}")
            return []

    def get_geographical_distribution(self):
        """Analyse de la distribution géographique."""
        try:
            pipeline = [
                {"$unwind": "$locations.countries"},
                {
                    "$group": {
                        "_id": "$locations.countries.country",
                        "trials_count": {"$sum": 1},
                        "sites_count": {
                            "$sum": {
                                "$toInt": "$locations.countries.competent_authority_sites"
                            }
                        },
                    }
                },
                {"$sort": {"trials_count": -1}},
            ]

            geo_data = list(self.collection.aggregate(pipeline))
            return geo_data
        except Exception as e:
            st.error(f"Erreur lors de l'analyse géographique: {e}")
            return []

    def get_trial_by_euct(self, euct_number):
        """Récupère un essai spécifique par son numéro EUCT."""
        try:
            trial = self.collection.find_one({"header.euct_number": euct_number})
            return trial
        except Exception as e:
            st.error(f"Erreur lors de la recherche de l'essai {euct_number}: {e}")
            return None

    def search_trials_by_pattern(self, pattern, field="header.euct_number", limit=20):
        """Recherche des essais par motif (pour autocomplétion)."""
        try:
            query = {field: {"$regex": pattern, "$options": "i"}}
            trials = list(self.collection.find(query, {field: 1}).limit(limit))
            return trials
        except Exception as e:
            st.error(f"Erreur lors de la recherche par motif: {e}")
            return []

    def get_all_contacts(self):
        """Extrait tous les contacts de tous les essais de la base de données."""
        try:
            # Pipeline d'agrégation pour extraire tous les contacts
            pipeline = [
                {"$unwind": "$locations.countries"},
                {"$unwind": "$locations.countries.sites"},
                {
                    "$match": {
                        "locations.countries.sites.contact": {
                            "$exists": True,
                            "$ne": {},
                        }
                    }
                },
                {
                    "$project": {
                        "euct_number": "$header.euct_number",
                        "trial_title": "$header.title",
                        "country": "$locations.countries.country",
                        "site_name": "$locations.countries.sites.name",
                        "city": "$locations.countries.sites.city",
                        "department": "$locations.countries.sites.department",
                        "address": "$locations.countries.sites.address",
                        "post_code": "$locations.countries.sites.post_code",
                        "contact": "$locations.countries.sites.contact",
                    }
                },
            ]

            contacts_data = list(self.collection.aggregate(pipeline))

            # Transformation en format DataFrame
            all_contacts = []
            for item in contacts_data:
                contact = item.get("contact", {})
                contact_info = {
                    "EUCT Number": item.get("euct_number", "N/A"),
                    "Titre de l'essai": (
                        item.get("trial_title", "N/A")[:50] + "..."
                        if len(str(item.get("trial_title", ""))) > 50
                        else item.get("trial_title", "N/A")
                    ),
                    "Pays": item.get("country", "N/A"),
                    "Site": item.get("site_name", "N/A"),
                    "Ville": item.get("city", "N/A"),
                    "Département": item.get("department", "N/A"),
                    "Titre": contact.get("title", ""),
                    "Prénom": contact.get("first_name", ""),
                    "Nom": contact.get("last_name", ""),
                    "Téléphone": contact.get("phone", ""),
                    "Email": contact.get("email", ""),
                    "Adresse": item.get("address", "N/A"),
                    "Code postal": item.get("post_code", "N/A"),
                }
                all_contacts.append(contact_info)

            return all_contacts
        except Exception as e:
            st.error(f"Erreur lors de l'extraction des contacts: {e}")
            return []

    def get_all_contacts(self):
        """Extrait tous les contacts de tous les essais de la base de données."""
        try:
            # Pipeline d'agrégation pour extraire tous les contacts
            pipeline = [
                {"$unwind": "$locations.countries"},
                {"$unwind": "$locations.countries.sites"},
                {
                    "$match": {
                        "locations.countries.sites.contact": {
                            "$exists": True,
                            "$ne": {},
                        }
                    }
                },
                {
                    "$project": {
                        "euct_number": "$header.euct_number",
                        "trial_title": "$header.title",
                        "country": "$locations.countries.country",
                        "site_name": "$locations.countries.sites.name",
                        "city": "$locations.countries.sites.city",
                        "department": "$locations.countries.sites.department",
                        "address": "$locations.countries.sites.address",
                        "post_code": "$locations.countries.sites.post_code",
                        "contact": "$locations.countries.sites.contact",
                    }
                },
            ]

            contacts_data = list(self.collection.aggregate(pipeline))

            # Transformation en format DataFrame
            all_contacts = []
            for item in contacts_data:
                contact = item.get("contact", {})
                contact_info = {
                    "EUCT Number": item.get("euct_number", "N/A"),
                    "Titre de l'essai": (
                        item.get("trial_title", "N/A")[:50] + "..."
                        if len(str(item.get("trial_title", ""))) > 50
                        else item.get("trial_title", "N/A")
                    ),
                    "Pays": item.get("country", "N/A"),
                    "Site": item.get("site_name", "N/A"),
                    "Ville": item.get("city", "N/A"),
                    "Département": item.get("department", "N/A"),
                    "Titre": contact.get("title", ""),
                    "Prénom": contact.get("first_name", ""),
                    "Nom": contact.get("last_name", ""),
                    "Téléphone": contact.get("phone", ""),
                    "Email": contact.get("email", ""),
                    "Adresse": item.get("address", "N/A"),
                    "Code postal": item.get("post_code", "N/A"),
                }
                all_contacts.append(contact_info)

            return all_contacts
        except Exception as e:
            st.error(f"Erreur lors de l'extraction des contacts: {e}")
            return []


def get_mongodb_connection_params():
    """Retourne les paramètres de connexion MongoDB depuis les variables d'environnement.

    Ces valeurs sont récupérées depuis les secrets Streamlit ou les variables d'environnement
    pour sécuriser les informations de connexion.
    """
    try:
        # Tentative de récupération depuis les secrets Streamlit Cloud
        uri = st.secrets["MONGODB_URI"]
        database = st.secrets["MONGODB_DATABASE"]
    except (KeyError, FileNotFoundError):
        # Fallback vers les variables d'environnement pour le développement local
        import os

        uri = os.getenv("MONGODB_URI", "")
        database = os.getenv("MONGODB_DATABASE", "clinical_trials_db")

        if not uri:
            st.error("⚠️ Paramètres de connexion MongoDB manquants!")
            st.error(
                "Veuillez configurer MONGODB_URI dans les secrets Streamlit ou les variables d'environnement."
            )
            st.stop()

    return uri, database


def test_mongodb_connection(uri, database):
    """Teste la connexion à MongoDB sans affichage à l'utilisateur.

    Returns:
        bool: True si la connexion a réussi, False sinon.
    """
    analytics = TrialAnalytics(uri, database)
    return analytics.connect()


def create_sidebar():
    """Crée la barre latérale avec le logo."""
    # Ajout du favicon avec le nom de l'entreprise au-dessus du titre
    st.sidebar.image("logo-freearcs_fav-icon.png", width=150, use_container_width=False)

    # Récupération des paramètres de connexion sans les afficher dans l'UI
    uri, database = get_mongodb_connection_params()

    return uri, database


def display_overview_dashboard(analytics):
    """Affiche le tableau de bord général."""
    # st.markdown(
    #     f"<h1 style='color:{COLORS['primary']};'>📊 Vue d'ensemble</h1>",
    #     unsafe_allow_html=True,
    # )

    # # Bannière colorée avec style personnalisé utilisant la couleur highlight
    # st.markdown(
    #     f"""
    # <div style="background-color:{COLORS['highlight']}; padding:10px; border-radius:10px; margin:10px 0px 20px 0px;">
    #     <h3 style="color:white; margin:0;">Analyseur d'Essais Cliniques - Tableau de Bord Principal</h3>
    # </div>
    # """,
    #     unsafe_allow_html=True,
    # )

    # Récupération des statistiques avec progress bar stylisé
    progress_placeholder = st.empty()

    # Affiche une barre de progression stylisée avant de commencer le chargement
    progress_placeholder.markdown(
        f"""
    <div style="width:100%; height:10px; background-color:#f0f0f0; border-radius:5px; margin-bottom:10px;">
        <div style="width:10%; height:10px; background: linear-gradient(90deg, {COLORS['secondary']} 0%, {COLORS['highlight']} 100%); border-radius:5px;"></div>
    </div>
    <p style="text-align:center; color:{COLORS['primary']};">Chargement des statistiques...</p>
    """,
        unsafe_allow_html=True,
    )

    # Chargement des données
    stats = analytics.get_basic_stats()

    # Mise à jour de la barre de progression à la fin
    progress_placeholder.markdown(
        f"""
    <div style="width:100%; height:10px; background-color:#f0f0f0; border-radius:5px; margin-bottom:10px;">
        <div style="width:100%; height:10px; background: linear-gradient(90deg, {COLORS['secondary']} 0%, {COLORS['highlight']} 100%); border-radius:5px;"></div>
    </div>
    <p style="text-align:center; color:{COLORS['primary']};">Données chargées avec succès!</p>
    """,
        unsafe_allow_html=True,
    )

    # Efface l'indicateur après un court délai
    time.sleep(1)
    progress_placeholder.empty()

    if not stats:
        st.error("Impossible de charger les statistiques")
        return

    # Métriques principales avec style card PowerBI
    # CSS pour créer des cartes style PowerBI
    st.markdown(
        """
    <style>
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.3s;
        height: 100%;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .metric-icon {
        font-size: 28px;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 36px;
        font-weight: bold;
        margin: 10px 0;
        color: """
        + COLORS["highlight"]
        + """;
    }
    .metric-label {
        font-size: 16px;
        color: """
        + COLORS["primary"]
        + """;
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Conteneur avec espacement
    st.markdown("<div style='padding: 10px;'></div>", unsafe_allow_html=True)

    # Création des colonnes avec un peu d'espace entre elles
    col1, spacer1, col2, spacer2, col3, spacer3, col4 = st.columns(
        [5, 0.5, 5, 0.5, 5, 0.5, 5]
    )

    # Métrique 1: Total des essais
    with col1:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-icon">📋</div>
            <div class="metric-value">{stats["total_trials"]}</div>
            <div class="metric-label">Total des essais</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Métrique 2: Conditions médicales
    with col2:
        total_conditions = stats.get("total_conditions", len(stats["conditions"]))
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-icon">🏥</div>
            <div class="metric-value">{total_conditions}</div>
            <div class="metric-label">Conditions médicales</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Métrique 3: Pays impliqués
    with col3:
        total_countries = stats.get("total_countries", len(stats["countries"]))
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-icon">🌍</div>
            <div class="metric-value">{total_countries}</div>
            <div class="metric-label">Pays impliqués</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Métrique 4: Phases différentes
    with col4:
        phases_count = len(stats["phases"])
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-icon">🧪</div>
            <div class="metric-value">{phases_count}</div>
            <div class="metric-label">Phases différentes</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Espace après les métriques
    st.markdown("<div style='padding: 15px;'></div>", unsafe_allow_html=True)

    # Ajout d'une nouvelle rangée pour les domaines thérapeutiques
    st.markdown(
        """
    <h4 style="color:#735252; margin-bottom: 15px;">Domaines Thérapeutiques</h4>
    """,
        unsafe_allow_html=True,
    )

    # Affichage du KPI pour les domaines thérapeutiques
    total_therapeutic_areas = stats.get("total_therapeutic_areas", 0)
    st.markdown(
        f"""
    <div class="metric-card">
        <div class="metric-icon">🧬</div>
        <div class="metric-value">{total_therapeutic_areas}</div>
        <div class="metric-label">Domaines thérapeutiques uniques</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # # Récupération des données des domaines thérapeutiques
    # therapeutic_areas = analytics.get_therapeutic_areas_distribution()

    # # Création d'une nouvelle ligne de colonnes
    # area_col1, area_spacer1, area_col2, area_spacer2, area_col3 = st.columns(
    #     [10, 0.5, 10, 0.5, 10]
    # )

    # # Affichage des domaines thérapeutiques (top 3)
    # if therapeutic_areas:
    #     for i, (col, area) in enumerate(zip([area_col1, area_col2, area_col3], therapeutic_areas[:3])):
    #         with col:
    #             area_name = area["_id"] if area["_id"] else "Non spécifié"
    #             # Tronquer le nom s'il est trop long
    #             if len(area_name) > 40:
    #                 area_name = area_name[:37] + "..."

    #             area_count = area["count"]
    #             icon = "🔬"  # Icône par défaut

    #             # Attribution d'icônes en fonction des mots-clés dans le nom
    #             if "Neoplasms" in area_name or "Cancer" in area_name:
    #                 icon = "🩺"
    #             elif "Cardiovascular" in area_name or "Heart" in area_name:
    #                 icon = "❤️"
    #             elif "Nervous" in area_name or "Brain" in area_name:
    #                 icon = "🧠"
    #             elif "Immune" in area_name:
    #                 icon = "🛡️"
    #             elif "Digestive" in area_name:
    #                 icon = "🧪"

    #             st.markdown(
    #                 f"""
    #             <div class="metric-card">
    #                 <div class="metric-icon">{icon}</div>
    #                 <div class="metric-value">{area_count}</div>
    #                 <div class="metric-label" title="{area_name}">{area_name}</div>
    #             </div>
    #             """,
    #                 unsafe_allow_html=True,
    #             )

    # # Espace après les domaines thérapeutiques
    # st.markdown("<div style='padding: 15px;'></div>", unsafe_allow_html=True)

    # Graphiques
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribution par Phase")
        if stats["phases"]:
            phases_df = pd.DataFrame(stats["phases"])
            phases_df["_id"] = phases_df["_id"].fillna("Non spécifié")

            # Create a custom color sequence that uses all 4 colors from the palette
            color_sequence = [
                COLORS["primary"],  # Marron/Gris foncé
                COLORS["secondary"],  # Vert forêt/Vert foncé
                COLORS["accent"],  # Vert herbe/Vert clair
                COLORS["highlight"],  # Orange vif/Rouge-orange
            ]

            # For more than 4 phases, create a pattern with these colors
            extended_colors = color_sequence * (len(phases_df) // 4 + 1)

            fig = px.pie(
                phases_df,
                values="count",
                names="_id",
                title="Répartition des essais par phase",
                color_discrete_sequence=extended_colors[: len(phases_df)],
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(
                title_font_color=COLORS["primary"],
                font_color=COLORS["text"],
                paper_bgcolor=COLORS["background"],
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Top 10 Pays")
        if stats["countries"]:
            countries_df = pd.DataFrame(stats["countries"])
            countries_df["_id"] = countries_df["_id"].fillna("Non spécifié")

            fig = px.bar(
                countries_df.head(10),
                x="count",
                y="_id",
                orientation="h",
                title="Nombre d'essais par pays (Top 10)",
                color_discrete_sequence=[COLORS["secondary"]],
            )
            fig.update_layout(
                yaxis={"categoryorder": "total ascending"},
                title_font_color=COLORS["primary"],
                font_color=COLORS["text"],
                paper_bgcolor=COLORS["background"],
                plot_bgcolor=COLORS["background"],
            )
            st.plotly_chart(fig, use_container_width=True)

            # Note explicative
            total_countries = stats.get("total_countries", len(stats["countries"]))
            st.caption(
                f"💡 Affichage du top 10 sur {total_countries} pays au total. Voir la section 'Analyses avancées' pour la liste complète."
            )

    # Conditions médicales
    st.subheader("Top 10 Conditions Médicales")
    if stats["conditions"]:
        conditions_df = pd.DataFrame(stats["conditions"])
        conditions_df["_id"] = conditions_df["_id"].fillna("Non spécifié")

        fig = px.bar(
            conditions_df.head(10),
            x="_id",
            y="count",
            title="Nombre d'essais par condition médicale",
            color="count",  # Utiliser count pour coloration
            color_continuous_scale=[
                [0, COLORS["accent"]],
                [0.5, COLORS["secondary"]],
                [1, COLORS["highlight"]],
            ],
        )
        fig.update_layout(
            xaxis_tickangle=20,
            title_font_color=COLORS["primary"],
            font_color=COLORS["text"],
            paper_bgcolor=COLORS["background"],
            plot_bgcolor=COLORS["background"],
            coloraxis_showscale=False,  # Cacher la barre d'échelle
        )
        st.plotly_chart(fig, use_container_width=True)

    # Contacts de tous les essais
    st.subheader("📞 Tous les Contacts des Sites d'Essais")
    with st.spinner("Extraction de tous les contacts..."):
        all_contacts = analytics.get_all_contacts()

    if all_contacts:
        st.write(
            f"**{len(all_contacts)} contact(s) trouvé(s) dans la base de données:**"
        )

        # Créer le DataFrame des contacts
        contacts_df = pd.DataFrame(all_contacts)

        # Réorganiser les colonnes pour un meilleur affichage
        columns_order = [
            "EUCT Number",
            "Titre de l'essai",
            "Pays",
            "Site",
            "Ville",
            "Département",
            "Titre",
            "Prénom",
            "Nom",
            "Téléphone",
            "Email",
            "Adresse",
            "Code postal",
        ]

        # S'assurer que toutes les colonnes existent
        for col in columns_order:
            if col not in contacts_df.columns:
                contacts_df[col] = ""

        contacts_df = contacts_df[columns_order]

        # Filtre par pays pour améliorer l'expérience utilisateur
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            # Filtre par pays
            unique_countries = sorted(contacts_df["Pays"].unique().tolist())
            selected_country = st.selectbox(
                "Filtrer par pays:",
                ["Tous"] + unique_countries,
                key="contact_country_filter",
            )

        with col2:
            # Filtre par nombre d'entrées à afficher
            display_limit = st.selectbox(
                "Nombre d'entrées:",
                [50, 100, 200, 500, "Tous"],
                index=1,
                key="contact_display_limit",
            )

        with col3:
            # Recherche par nom/email
            search_term = st.text_input(
                "Rechercher (nom, email, site):", key="contact_search"
            )

        # Appliquer les filtres
        filtered_df = contacts_df.copy()

        if selected_country != "Tous":
            filtered_df = filtered_df[filtered_df["Pays"] == selected_country]

        if search_term:
            # Recherche dans plusieurs colonnes
            search_mask = (
                filtered_df["Nom"].str.contains(search_term, case=False, na=False)
                | filtered_df["Prénom"].str.contains(search_term, case=False, na=False)
                | filtered_df["Email"].str.contains(search_term, case=False, na=False)
                | filtered_df["Site"].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[search_mask]

        if display_limit != "Tous":
            filtered_df = filtered_df.head(int(display_limit))

        # Afficher le DataFrame avec possibilité de tri
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=min(500, len(filtered_df) * 35 + 100),  # Hauteur dynamique
            column_config={
                "EUCT Number": st.column_config.TextColumn("EUCT", width="medium"),
                "Titre de l'essai": st.column_config.TextColumn("Essai", width="large"),
                "Email": st.column_config.TextColumn("Email", width="medium"),
                "Téléphone": st.column_config.TextColumn("Téléphone", width="medium"),
                "Site": st.column_config.TextColumn("Site", width="large"),
                "Adresse": st.column_config.TextColumn("Adresse", width="large"),
            },
        )

        # Statistiques des contacts
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total contacts", len(all_contacts))
        with col2:
            st.metric("Contacts affichés", len(filtered_df))
        with col3:
            contacts_with_email = len(filtered_df[filtered_df["Email"] != ""])
            st.metric("Avec email", contacts_with_email)
        with col4:
            contacts_with_phone = len(filtered_df[filtered_df["Téléphone"] != ""])
            st.metric("Avec téléphone", contacts_with_phone)

        # Option de téléchargement
        col1, col2 = st.columns([1, 3])
        with col1:
            # Utilisation d'un conteneur div pour appliquer la classe CSS au bouton
            with st.container():
                st.markdown(
                    """
                <style>
                    div[data-testid="stButton"]:nth-of-type(1) > button {
                        background-color: """
                    + COLORS["highlight"]
                    + """;
                        color: white;
                    }
                </style>
                """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    "💾 Télécharger les contacts (CSV)", key="download_all_contacts"
                ):
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Télécharger CSV",
                        data=csv,
                        file_name=f"tous_contacts_essais_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="download_csv_all_contacts",
                    )

        with col2:
            st.caption(
                "💡 Utilisez les filtres pour affiner votre recherche. Cliquez sur les en-têtes de colonnes pour trier les données."
            )

    else:
        st.info("Aucun contact trouvé dans la base de données.")


def display_advanced_search(analytics):
    """Affiche l'interface de recherche avancée."""
    st.header("🔍 Recherche Avancée")

    # Formulaire de recherche
    with st.form("advanced_search"):
        col1, col2, col3 = st.columns(3)

        with col1:
            phase = st.selectbox(
                "Phase de l'essai",
                [
                    "Toutes",
                    "Phase I",
                    "Phase II",
                    "Phase III",
                    "Phase IV",
                    "Phase I/II",
                    "Phase II/III",
                ],
            )

            condition = st.text_input("Condition médicale (recherche partielle)")

        with col2:
            country = st.selectbox(
                "Pays",
                [
                    "Tous",
                    "France",
                    "Germany",
                    "Spain",
                    "Italy",
                    "United Kingdom",
                    "Netherlands",
                ],
            )

            sponsor = st.text_input("Sponsor (recherche partielle)")

        with col3:
            date_from = st.date_input("Date de début", value=None)
            date_to = st.date_input("Date de fin", value=None)

            limit = st.number_input(
                "Nombre max de résultats", min_value=10, max_value=500, value=50
            )

        search_button = st.form_submit_button("🔍 Rechercher")

    if search_button:
        filters = {
            "phase": phase,
            "country": country,
            "condition": condition,
            "sponsor": sponsor,
            "date_from": date_from,
            "date_to": date_to,
            "limit": limit,
        }

        with st.spinner("Recherche en cours..."):
            trials, total_count = analytics.search_trials_advanced(filters)

        st.success(f"🎯 {len(trials)} essais trouvés sur {total_count} au total")

        if trials:
            # Affichage des résultats
            for i, trial in enumerate(trials):
                with st.expander(
                    f"#{i+1} - {trial.get('header', {}).get('euct_number', 'N/A')}"
                ):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(
                            "**Titre:**", trial.get("header", {}).get("title", "N/A")
                        )
                        st.write(
                            "**Phase:**",
                            trial.get("summary", {})
                            .get("trial_information", {})
                            .get("trial_phase", "N/A"),
                        )
                        # Mise en évidence de la condition médicale avec la couleur highlight
                        condition = (
                            trial.get("summary", {})
                            .get("trial_information", {})
                            .get("medical_condition", "N/A")
                        )
                        st.markdown(
                            f"**Condition:** <span style='color:{COLORS['highlight']};font-weight:bold;'>{condition}</span>",
                            unsafe_allow_html=True,
                        )

                    with col2:
                        st.write(
                            "**Sponsor:**",
                            trial.get("summary", {})
                            .get("trial_information", {})
                            .get("sponsor", "N/A"),
                        )
                        st.write(
                            "**Domaine thérapeutique:**",
                            trial.get("summary", {})
                            .get("trial_information", {})
                            .get("therapeutic_area", "N/A"),
                        )

                        # Pays participants
                        countries_data = trial.get("locations", {}).get("countries", [])
                        if countries_data:
                            countries = [
                                country.get("country", "N/A")
                                for country in countries_data
                            ]
                            st.write(
                                "**Pays:**",
                                ", ".join(countries[:3])
                                + ("..." if len(countries) > 3 else ""),
                            )


def display_analytics_dashboard(analytics):
    """Affiche le tableau de bord d'analyses avancées."""
    st.header("📈 Analyses Avancées")

    # Timeline des essais
    st.subheader("📅 Timeline des Essais")
    with st.spinner("Génération de la timeline..."):
        timeline_data = analytics.get_timeline_data()

    if timeline_data:
        timeline_df = pd.DataFrame(timeline_data)
        timeline_df["date"] = pd.to_datetime(timeline_df["_id"])
        timeline_df = timeline_df.sort_values("date")

        fig = px.line(
            timeline_df,
            x="date",
            y="count",
            title="Évolution du nombre d'essais dans le temps",
            markers=True,
            color_discrete_sequence=[COLORS["secondary"]],
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Nombre d'essais",
            title_font_color=COLORS["primary"],
            font_color=COLORS["text"],
            paper_bgcolor=COLORS["background"],
            plot_bgcolor=COLORS["background"],
        )
        # Ajouter une ligne de tendance en couleur accent
        fig.add_scatter(
            x=timeline_df["date"],
            y=timeline_df["count"].rolling(3, center=True).mean(),
            mode="lines",
            line=dict(color=COLORS["accent"], dash="dot"),
            name="Tendance",
        )
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    # Domaines thérapeutiques
    with col1:
        st.subheader("🧬 Domaines Thérapeutiques")
        with st.spinner("Analyse des domaines thérapeutiques..."):
            therapeutic_areas = analytics.get_therapeutic_areas_distribution()

        if therapeutic_areas:
            areas_df = pd.DataFrame(therapeutic_areas)
            areas_df["_id"] = areas_df["_id"].fillna("Non spécifié")

            # Traitement des noms longs
            areas_df["short_name"] = areas_df["_id"].apply(
                lambda x: x[:30] + "..." if len(str(x)) > 30 else x
            )

            # Créer un graphique treemap pour les domaines thérapeutiques
            fig = px.treemap(
                areas_df.head(10),
                path=["short_name"],
                values="count",
                title="Distribution des domaines thérapeutiques",
                color="count",
                color_continuous_scale=[
                    [0, COLORS["accent"]],
                    [0.5, COLORS["secondary"]],
                    [1, COLORS["highlight"]],
                ],
            )
            fig.update_layout(
                title_font_color=COLORS["primary"],
                font_color=COLORS["text"],
                paper_bgcolor=COLORS["background"],
                coloraxis_showscale=False,  # Cacher l'échelle de couleur
            )
            st.plotly_chart(fig, use_container_width=True)

            # Optionnellement, ajouter un graphique radar pour une visualisation alternative
            with st.expander("🔄 Voir visualisation alternative (Radar)"):
                # Préparer les données pour le radar (top 6 pour lisibilité)
                top_areas = areas_df.head(6).copy()

                fig_radar = go.Figure()

                fig_radar.add_trace(
                    go.Scatterpolar(
                        r=top_areas["count"],
                        theta=top_areas["short_name"],
                        fill="toself",
                        line=dict(color=COLORS["highlight"], width=2),
                        fillcolor=f'rgba({int(COLORS["highlight"][1:3], 16)}, {int(COLORS["highlight"][3:5], 16)}, {int(COLORS["highlight"][5:7], 16)}, 0.3)',
                        # fill="toself",
                        # line=dict(color=COLORS["highlight"]),
                        # fillcolor=f'rgba({int(COLORS["highlight"][1:3], 16)}, {int(COLORS["highlight"][3:5], 16)}, {int(COLORS["highlight"][5:7], 16)}, 0.3)',
                    )
                )

                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True, range=[0, max(top_areas["count"]) * 1.1]
                        )
                    ),
                    showlegend=False,
                    title="Top 6 domaines thérapeutiques (Radar)",
                    title_font_color=COLORS["primary"],
                    paper_bgcolor=COLORS["background"],
                )

                st.plotly_chart(fig_radar, use_container_width=True)

    # Analyse des sponsors
    with col2:
        st.subheader("🏢 Top Sponsors")
        with st.spinner("Analyse des sponsors..."):
            sponsors = analytics.get_sponsor_analysis()

        if sponsors:
            sponsors_df = pd.DataFrame(sponsors)
            sponsors_df["_id"] = sponsors_df["_id"].fillna("Non spécifié")

            fig = px.bar(
                sponsors_df.head(10),
                x="count",
                y="_id",
                orientation="h",
                title="Sponsors les plus actifs",
                color="count",
                color_continuous_scale=[
                    [0, COLORS["secondary"]],
                    [0.7, COLORS["accent"]],
                    [1, COLORS["highlight"]],
                ],
            )
            fig.update_layout(
                yaxis={"categoryorder": "total ascending"},
                title_font_color=COLORS["primary"],
                font_color=COLORS["text"],
                paper_bgcolor=COLORS["background"],
                plot_bgcolor=COLORS["background"],
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig, use_container_width=True)

            fig = px.bar(
                sponsors_df.head(10),
                x="count",
                y="_id",
                orientation="h",
                title="Sponsors les plus actifs",
                color_discrete_sequence=[COLORS["primary"]],
            )
            fig.update_layout(
                yaxis={"categoryorder": "total ascending"},
                title_font_color=COLORS["primary"],
                font_color=COLORS["text"],
                paper_bgcolor=COLORS["background"],
                plot_bgcolor=COLORS["background"],
            )
            st.plotly_chart(fig, use_container_width=True)

    # Distribution géographique
    st.markdown(
        f"""
    <div style="background-color:{COLORS['primary']}; padding:5px; border-radius:5px; margin:10px 0px 15px 0px;">
        <h3 style="color:white; margin:0; text-align:center;">🗺️ Distribution Géographique</h3>
    </div>
    """,
        unsafe_allow_html=True,
    )

    with st.spinner("Analyse géographique..."):
        geo_data = analytics.get_geographical_distribution()

    if geo_data:
        geo_df = pd.DataFrame(geo_data)
        geo_df["_id"] = geo_df["_id"].fillna("Non spécifié")

        col1, col2 = st.columns(2)

        with col1:
            fig = px.choropleth(
                geo_df,
                locations="_id",
                color="trials_count",
                hover_name="_id",
                color_continuous_scale=[
                    [0, COLORS["secondary"]],
                    [0.5, COLORS["accent"]],
                    [1, COLORS["highlight"]],
                ],
                title="Nombre d'essais par pays",
                locationmode="country names",
            )
            fig.update_layout(
                title_font_color=COLORS["primary"],
                font_color=COLORS["text"],
                paper_bgcolor=COLORS["background"],
                geo=dict(
                    showframe=True,
                    framecolor=COLORS["primary"],
                    showcoastlines=True,
                    coastlinecolor=COLORS["secondary"],
                ),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Header stylisé
            st.markdown(
                f"""
            <h4 style="color:{COLORS['primary']};">Détails par pays</h4>
            """,
                unsafe_allow_html=True,
            )

            # Métriques clés avec la couleur highlight
            total_trials = geo_df["trials_count"].sum()
            total_sites = geo_df["sites_count"].sum()
            top_country = geo_df.sort_values("trials_count", ascending=False).iloc[0]

            st.markdown(
                f"""
            <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
                <div style="text-align:center; padding:10px; background-color:white; border-radius:5px; box-shadow:0 0 5px rgba(0,0,0,0.1); flex:1; margin-right:5px;">
                    <p style="font-size:14px; margin:0;">Total d'essais</p>
                    <p style="font-size:24px; color:{COLORS['highlight']}; font-weight:bold; margin:0;">{total_trials}</p>
                </div>
                <div style="text-align:center; padding:10px; background-color:white; border-radius:5px; box-shadow:0 0 5px rgba(0,0,0,0.1); flex:1; margin-left:5px;">
                    <p style="font-size:14px; margin:0;">Total de sites</p>
                    <p style="font-size:24px; color:{COLORS['highlight']}; font-weight:bold; margin:0;">{total_sites}</p>
                </div>
            </div>
            <div style="text-align:center; padding:10px; background-color:white; border-radius:5px; box-shadow:0 0 5px rgba(0,0,0,0.1); margin-bottom:15px;">
                <p style="font-size:14px; margin:0;">Pays le plus actif</p>
                <p style="font-size:20px; color:{COLORS['highlight']}; font-weight:bold; margin:0;">{top_country['_id']} ({top_country['trials_count']} essais)</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Table des données
            geo_df_sorted = geo_df.sort_values("trials_count", ascending=False)
            st.dataframe(
                geo_df_sorted[["_id", "trials_count", "sites_count"]].rename(
                    columns={
                        "_id": "Pays",
                        "trials_count": "Nombre d'essais",
                        "sites_count": "Nombre de sites",
                    }
                ),
                use_container_width=True,
                height=300,
            )


def display_individual_trial_analysis(analytics):
    """Affiche l'analyse détaillée d'un essai individuel."""
    st.header("🔍 Analyse d'Essai Individuel")

    # Interface de recherche d'essai
    st.subheader("📋 Recherche d'Essai")

    col1, col2 = st.columns([3, 1])

    with col1:
        euct_number = st.text_input(
            "Numéro EUCT",
            value="2022-500013-32-01",
            help="Entrez le numéro EUCT de l'essai à analyser",
            placeholder="YYYY-NNNNNN-NN-NN",
        )

    with col2:
        search_button = st.button("🔍 Rechercher l'essai")

    # Recherche automatique ou manuelle
    if search_button or euct_number:
        with st.spinner(f"Recherche de l'essai {euct_number}..."):
            trial = analytics.get_trial_by_euct(euct_number)

        if trial:
            st.success(f"✅ Essai {euct_number} trouvé!")

            # Affichage des informations de l'essai
            display_trial_details(trial)
        else:
            st.error(f"❌ Aucun essai trouvé avec le numéro EUCT: {euct_number}")

            # Suggestions d'essais similaires
            st.subheader("💡 Suggestions d'essais similaires")
            if len(euct_number) >= 4:
                pattern = euct_number[:4]  # Recherche par année
                similar_trials = analytics.search_trials_by_pattern(pattern)

                if similar_trials:
                    st.write("**Essais de la même année:**")
                    for trial_ref in similar_trials[:10]:
                        euct = trial_ref.get("header", {}).get("euct_number", "N/A")
                        if st.button(f"📋 {euct}", key=f"similar_{euct}"):
                            st.experimental_rerun()


def display_trial_details(trial):
    """Affiche les détails complets d'un essai."""

    # Informations principales
    st.subheader("📋 Informations Principales")

    header = trial.get("header", {})
    summary = trial.get("summary", {})
    trial_info = summary.get("trial_information", {})

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Numéro EUCT:**", header.get("euct_number", "N/A"))
        st.write("**Code protocole:**", header.get("protocol_code", "N/A"))
        st.write("**Titre:**", header.get("title", "N/A"))
        st.write("**Phase:**", trial_info.get("trial_phase", "N/A"))
        st.write("**Condition médicale:**", trial_info.get("medical_condition", "N/A"))
        st.write(
            "**Domaine thérapeutique:**", trial_info.get("therapeutic_area", "N/A")
        )

    with col2:
        st.write("**Sponsor:**", trial_info.get("sponsor", "N/A"))

        # Statut général de l'essai
        overall_status = summary.get("overall_trial_status", {})
        st.write("**Statut:**", overall_status.get("status", "N/A"))
        st.write("**Date de début:**", overall_status.get("start_date", "N/A"))

        # Dates importantes
        trial_duration = summary.get("trial_duration", {})
        st.write(
            "**Début de recrutement:**",
            trial_duration.get("estimated_recruitment_start", "N/A"),
        )
        st.write("**Fin estimée:**", trial_duration.get("estimated_end_date", "N/A"))
        st.write(
            "**Fin globale estimée:**",
            trial_duration.get("estimated_global_end_date", "N/A"),
        )

    # Objectifs de l'essai
    st.subheader("🎯 Objectifs de l'Essai")

    # L'objectif principal est dans trial_information.main_objective
    main_objective = trial_info.get("main_objective", "")

    if main_objective:
        st.write("**Objectif principal:**")
        st.write(main_objective)
    else:
        # Fallback vers l'ancienne structure si elle existe
        objectives = summary.get("trial_objectives", {})
        if objectives:
            primary_obj = objectives.get("primary_objective", "Non spécifié")
            secondary_obj = objectives.get("secondary_objectives", "Non spécifié")

            st.write("**Objectif principal:**")
            st.write(primary_obj)

            if secondary_obj and secondary_obj != "Non spécifié":
                st.write("**Objectifs secondaires:**")
                st.write(secondary_obj)
        else:
            st.info("Aucun objectif spécifié pour cet essai.")

    # Statut détaillé par pays
    st.subheader("📊 Statut Détaillé par Pays")
    overall_status = summary.get("overall_trial_status", {})
    application_trial_status = overall_status.get("application_trial_status", [])

    if application_trial_status:
        st.write("**Statut dans chaque État membre:**")

        # Créer un DataFrame pour le statut par pays
        status_data = []
        for status_info in application_trial_status:
            status_data.append(
                {
                    "État membre": status_info.get("member_state", "N/A"),
                    "Statut": status_info.get("application_trial_status", "N/A"),
                    "Date de décision": status_info.get("decision_date", "N/A"),
                }
            )

        if status_data:
            status_df = pd.DataFrame(status_data)
            st.dataframe(
                status_df,
                use_container_width=True,
                height=min(300, len(status_df) * 35 + 100),  # Hauteur dynamique
                column_config={
                    "État membre": st.column_config.TextColumn(
                        "État membre", width="medium"
                    ),
                    "Statut": st.column_config.TextColumn("Statut", width="large"),
                    "Date de décision": st.column_config.DateColumn(
                        "Date de décision", width="medium"
                    ),
                },
            )

        # Statistiques du statut global
        if overall_status.get("status"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("**Statut global**", overall_status.get("status", "N/A"))
            with col2:
                st.metric(
                    "**Date de début global**", overall_status.get("start_date", "N/A")
                )
    else:
        st.info("Aucune information de statut détaillé disponible.")

    # Population de l'essai
    st.subheader("👥 Population de l'Essai")
    population = summary.get("population", {})
    if population:
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Âge:**", population.get("age", "N/A"))
            st.write("**Genre:**", population.get("gender", "N/A"))
            st.write(
                "**Nombre de sujets:**", population.get("number_of_subjects", "N/A")
            )

        with col2:
            st.write("**Critères d'inclusion:**")
            inclusion = population.get("inclusion_criteria", "Non spécifié")
            st.write(
                inclusion[:500] + "..." if len(str(inclusion)) > 500 else inclusion
            )

    # Géolocalisation et sites
    st.subheader("🌍 Géolocalisation et Sites")
    locations = trial.get("locations", {})
    countries = locations.get("countries", [])

    if countries:
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Pays participants:**")
            countries_data = []
            for country in countries:
                country_name = country.get("country", "N/A")
                sites_count = country.get("competent_authority_sites", "0")
                countries_data.append({"Pays": country_name, "Sites": sites_count})

            countries_df = pd.DataFrame(countries_data)
            st.dataframe(countries_df, use_container_width=True)

        with col2:
            if len(countries_data) > 1:
                # Graphique des sites par pays
                fig = px.bar(
                    countries_df, x="Pays", y="Sites", title="Nombre de sites par pays"
                )
                fig.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

    # Médicament investigationnel
    st.subheader("💊 Médicament Investigationnel")
    imp = summary.get("investigational_medicinal_product", {})
    if imp:
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Nom du produit:**", imp.get("product_name", "N/A"))
            st.write("**Substance active:**", imp.get("active_substance", "N/A"))
            st.write("**Code ATC:**", imp.get("atc_code", "N/A"))

        with col2:
            st.write("**Forme pharmaceutique:**", imp.get("pharmaceutical_form", "N/A"))
            st.write(
                "**Voie d'administration:**", imp.get("route_of_administration", "N/A")
            )
            st.write("**Concentration:**", imp.get("concentration", "N/A"))

    # Design de l'essai
    st.subheader("🔬 Design de l'Essai")
    design = summary.get("trial_design", {})
    if design:
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Type de contrôle:**", design.get("controlled", "N/A"))
            st.write("**Randomisé:**", design.get("randomised", "N/A"))
            st.write("**Aveugle:**", design.get("blinded", "N/A"))

        with col2:
            st.write(
                "**Groupes de traitement:**", design.get("treatment_groups", "N/A")
            )
            st.write("**Allocation:**", design.get("allocation", "N/A"))

    # Données de contact
    st.subheader("📞 Contacts des Sites")

    # Extraction des contacts des sites
    site_contacts = extract_site_contacts(trial)

    if site_contacts:
        st.write(
            f"**{len(site_contacts)} contact(s) trouvé(s) dans les sites de l'essai:**"
        )

        # Affichage sous forme de DataFrame
        contacts_df = pd.DataFrame(site_contacts)

        # Réorganiser les colonnes pour un meilleur affichage
        columns_order = [
            "Pays",
            "Site",
            "Ville",
            "Département",
            "Titre",
            "Prénom",
            "Nom",
            "Téléphone",
            "Email",
            "Adresse",
            "Code postal",
        ]

        # S'assurer que toutes les colonnes existent
        for col in columns_order:
            if col not in contacts_df.columns:
                contacts_df[col] = ""

        contacts_df = contacts_df[columns_order]

        # Afficher le DataFrame avec possibilité de tri
        st.dataframe(
            contacts_df,
            use_container_width=True,
            height=min(400, len(contacts_df) * 35 + 100),  # Hauteur dynamique
            column_config={
                "Email": st.column_config.TextColumn("Email", width="medium"),
                "Téléphone": st.column_config.TextColumn("Téléphone", width="medium"),
                "Site": st.column_config.TextColumn("Site", width="large"),
                "Adresse": st.column_config.TextColumn("Adresse", width="large"),
            },
        )

        # Option de téléchargement des contacts
        if st.button("💾 Télécharger les contacts (CSV)"):
            csv = contacts_df.to_csv(index=False)
            st.download_button(
                label="📥 Télécharger CSV",
                data=csv,
                file_name=f"contacts_essai_{trial.get('header', {}).get('euct_number', 'unknown')}.csv",
                mime="text/csv",
            )
    else:
        st.info("Aucune information de contact disponible pour les sites de cet essai.")

    # Contacts généraux (s'ils existent dans la structure traditionnelle)
    contacts = trial.get("contacts", {})
    if contacts:
        with st.expander("📞 Autres contacts (structure traditionnelle)"):
            # Contact principal
            main_contact = contacts.get("main_contact", {})
            if main_contact:
                st.write("**Contact principal:**")
                st.write(f"- Nom: {main_contact.get('name', 'N/A')}")
                st.write(f"- Email: {main_contact.get('email', 'N/A')}")
                st.write(f"- Téléphone: {main_contact.get('phone', 'N/A')}")

            # Contact scientifique
            scientific_contact = contacts.get("scientific_contact", {})
            if scientific_contact:
                st.write("**Contact scientifique:**")
                st.write(f"- Nom: {scientific_contact.get('name', 'N/A')}")
                st.write(f"- Email: {scientific_contact.get('email', 'N/A')}")

    # Données brutes (optionnel)
    with st.expander("🔧 Données brutes (JSON)"):
        st.json(trial)


def extract_site_contacts(trial):
    """Extrait tous les contacts des sites de l'essai."""
    contacts_list = []

    locations = trial.get("locations", {})
    countries = locations.get("countries", [])

    for country in countries:
        country_name = country.get("country", "N/A")
        sites = country.get("sites", [])

        for site in sites:
            contact = site.get("contact", {})
            if contact:  # Seulement si des informations de contact existent
                contact_info = {
                    "Pays": country_name,
                    "Site": site.get("name", "N/A"),
                    "Ville": site.get("city", "N/A"),
                    "Département": site.get("department", "N/A"),
                    "Titre": contact.get("title", ""),
                    "Prénom": contact.get("first_name", ""),
                    "Nom": contact.get("last_name", ""),
                    "Téléphone": contact.get("phone", ""),
                    "Email": contact.get("email", ""),
                    "Adresse": site.get("address", "N/A"),
                    "Code postal": site.get("post_code", "N/A"),
                }
                contacts_list.append(contact_info)

    return contacts_list


def display_custom_queries(analytics):
    """Interface pour les requêtes MongoDB personnalisées."""
    st.header("⚙️ Requêtes Personnalisées")

    st.info(
        "Exécutez des requêtes MongoDB personnalisées pour des analyses spécifiques."
    )

    # Exemples de requêtes prédéfinies
    st.subheader("📝 Exemples de requêtes")

    query_examples = {
        "Essais par phase": {
            "description": "Compter les essais par phase",
            "query": '[\n  {"$group": {"_id": "$summary.trial_information.trial_phase", "count": {"$sum": 1}}},\n  {"$sort": {"count": -1}}\n]',
        },
        "Essais récents": {
            "description": "Essais ajoutés dans les 30 derniers jours",
            "query": '{\n  "date_added": {\n    "$gte": "'
            + (datetime.now() - timedelta(days=30)).isoformat()
            + '"\n  }\n}',
        },
        "Essais par sponsor": {
            "description": "Top 10 des sponsors les plus actifs",
            "query": '[\n  {"$group": {"_id": "$summary.trial_information.sponsor", "count": {"$sum": 1}}},\n  {"$sort": {"count": -1}},\n  {"$limit": 10}\n]',
        },
    }

    selected_example = st.selectbox(
        "Choisir un exemple", ["Personnalisé"] + list(query_examples.keys())
    )

    if selected_example != "Personnalisé":
        example = query_examples[selected_example]
        st.write(f"**Description:** {example['description']}")
        default_query = example["query"]
    else:
        default_query = "{}"

    # Interface de requête
    col1, col2 = st.columns([2, 1])

    with col1:
        query_text = st.text_area(
            "Requête MongoDB (JSON)",
            value=default_query,
            height=200,
            help="Entrez une requête MongoDB valide en format JSON",
        )

    with col2:
        query_type = st.radio(
            "Type de requête",
            ["find", "aggregate"],
            help="find: requête simple, aggregate: pipeline d'agrégation",
        )

        limit_results = st.number_input(
            "Limite de résultats", min_value=1, max_value=1000, value=100
        )

        execute_button = st.button("▶️ Exécuter", type="primary")

    if execute_button:
        try:
            # Parsing de la requête JSON
            if query_type == "find":
                query = json.loads(query_text)
                cursor = analytics.collection.find(query).limit(limit_results)
                results = list(cursor)
            else:  # aggregate
                pipeline = json.loads(query_text)
                results = list(analytics.collection.aggregate(pipeline))

            st.success(f"✅ Requête exécutée avec succès - {len(results)} résultat(s)")

            if results:
                # Affichage des résultats
                st.subheader("📊 Résultats")

                # Tentative de création d'un DataFrame pour l'affichage
                try:
                    df = pd.json_normalize(results)
                    st.dataframe(df, use_container_width=True, height=400)
                except:
                    # Affichage JSON si la normalisation échoue
                    st.json(results[:10])  # Limite à 10 pour éviter l'encombrement
                    if len(results) > 10:
                        st.info(
                            f"Affichage des 10 premiers résultats sur {len(results)}"
                        )

                # Option de téléchargement
                if st.button("💾 Télécharger les résultats (JSON)"):
                    results_json = json.dumps(
                        results, indent=2, default=str, ensure_ascii=False
                    )
                    st.download_button(
                        label="📥 Télécharger",
                        data=results_json,
                        file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                    )
            else:
                st.warning("Aucun résultat trouvé")

        except json.JSONDecodeError as e:
            st.error(f"❌ Erreur de parsing JSON: {e}")
        except Exception as e:
            st.error(f"❌ Erreur lors de l'exécution de la requête: {e}")


def main():
    """Fonction principale de l'application Streamlit."""

    # En-tête stylisé avec bandeau aux couleurs de l'entreprise
    st.markdown(
        f"""
    <div style="background: linear-gradient(90deg, {COLORS['primary']} 0%, {COLORS['secondary']} 50%, {COLORS['highlight']} 100%); 
                padding: 20px; border-radius: 10px; margin-bottom: 20px; display: flex; align-items: center;">
        <div style="background-color: white; padding: 10px; border-radius: 50%; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center;">
            <span style="font-size: 30px;">🔬</span>
        </div>
        <div style="flex: 1; text-align: center;">
            <h1 style="color: white; margin: 0;">Analyseur d'Essais Cliniques</h1>
            <p style="color: white; margin: 0; font-size: 16px;">Plateforme d'analyse et de visualisation des données d'essais cliniques</p>
        </div>
        <div style="background-color: white; padding: 10px; border-radius: 50%; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center;">
            <span style="font-size: 30px;">🧪</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Configuration de la barre latérale
    uri, database = create_sidebar()

    # Test de connexion silencieux au démarrage
    connection_status = test_mongodb_connection(uri, database)
    if not connection_status:
        st.sidebar.error(
            "⚠️ Connexion à la base de données impossible. Veuillez contacter votre administrateur système.",
            icon="⚠️",
        )

    # Navigation
    st.sidebar.markdown("---")
    st.sidebar.title("📱 Navigation")

    pages = {
        "Vue d'ensemble": "📊",
        "Recherche avancée": "🔍",
        "Analyses avancées": "📈",
        "Analyse individuelle": "🔍",
        "Requêtes personnalisées": "⚙️",
    }

    selected_page = st.sidebar.radio(
        "Choisir une page", list(pages.keys()), format_func=lambda x: f"{pages[x]} {x}"
    )

    # Initialisation de la connexion
    analytics = TrialAnalytics(uri, database)

    if not analytics.connect():
        st.error(
            "❌ Impossible de se connecter à MongoDB. Vérifiez vos paramètres de connexion."
        )
        st.stop()

    try:
        # Affichage de la page sélectionnée
        if selected_page == "Vue d'ensemble":
            display_overview_dashboard(analytics)
        elif selected_page == "Recherche avancée":
            display_advanced_search(analytics)
        elif selected_page == "Analyses avancées":
            display_analytics_dashboard(analytics)
        elif selected_page == "Analyse individuelle":
            display_individual_trial_analysis(analytics)
        elif selected_page == "Requêtes personnalisées":
            display_custom_queries(analytics)

    except Exception as e:
        st.error(f"❌ Erreur dans l'application: {e}")
        logger.error(f"Erreur application: {e}")

    finally:
        analytics.disconnect()

    # Pied de page dans la barre latérale
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"""
    <div style="background-color: {COLORS['primary']}; padding: 10px; border-radius: 5px; margin-top: 15px;">
        <h4 style="color: white; margin: 0; text-align: center;">💡 Conseils d'utilisation</h4>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Liste stylisée
    st.sidebar.markdown(
        f"""
    <ul style="list-style-type: none; padding-left: 5px;">
      <li style="margin-bottom: 8px;">
        <span style="color: {COLORS['highlight']};">•</span> Testez la connexion avant utilisation
      </li>
      <li style="margin-bottom: 8px;">
        <span style="color: {COLORS['highlight']};">•</span> Utilisez les filtres pour affiner vos recherches
      </li>
      <li style="margin-bottom: 8px;">
        <span style="color: {COLORS['highlight']};">•</span> Les requêtes personnalisées permettent des analyses spécifiques
      </li>
      <li style="margin-bottom: 8px;">
        <span style="color: {COLORS['highlight']};">•</span> Téléchargez les résultats pour analyses externes
      </li>
    </ul>
    """,
        unsafe_allow_html=True,
    )

    # Pied de page général en bas de l'application
    st.markdown("---")
    st.markdown(
        f"""
    <div style="text-align: center; margin-top: 30px; padding: 20px; background-color: {COLORS['background']};">
        <div style="display: flex; justify-content: center; margin-bottom: 10px;">
            <div style="width: 20px; height: 20px; background-color: {COLORS['primary']}; margin: 0 5px; border-radius: 3px;"></div>
            <div style="width: 20px; height: 20px; background-color: {COLORS['secondary']}; margin: 0 5px; border-radius: 3px;"></div>
            <div style="width: 20px; height: 20px; background-color: {COLORS['accent']}; margin: 0 5px; border-radius: 3px;"></div>
            <div style="width: 20px; height: 20px; background-color: {COLORS['highlight']}; margin: 0 5px; border-radius: 3px;"></div>
        </div>
        <p style="color: {COLORS['secondary']}; font-size: 14px; margin: 5px 0;">Analyseur d'Essais Cliniques © 2025</p>
        <p style="color: {COLORS['primary']}; font-size: 12px;">Version 1.0 | Dernière mise à jour : 22 juin 2025</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
