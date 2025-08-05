#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Streamlit application for MongoDB clinical trials data analysis.
Interactive interface for advanced queries and visualizations.

#735252 : Brown/Dark gray
#3b813b : Forest green/Dark green
#4aac47 : Grass green/Light green
#e64f29 : Bright orange/Red-orange
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

# Definition of company colors for consistent use
COLORS = {
    "primary": "#735252",  # Brown/Dark gray
    "secondary": "#3b813b",  # Forest green/Dark green
    "accent": "#4aac47",  # Grass green/Light green
    "highlight": "#e64f29",  # Bright orange/Red-orange
    "background": "#f9f9f9",  # Light background for better contrast
    "text": "#333333",  # Dark text for readability
}

# Constants for common text
NOT_SPECIFIED = "Not specified"
NOT_SPECIFIED_FR = "Non spécifié"

# Column name constants
MEMBER_STATE = "Member State"
DECISION_DATE = "Decision Date"
STATUS = "Status"
COUNTRY = "Country"
SITE = "Site"
CITY = "City"
DEPARTMENT = "Department"
TITLE = "Title"
FIRST_NAME = "First Name"
LAST_NAME = "Last Name"
PHONE = "Phone"
EMAIL = "Email"
ADDRESS = "Address"
POSTAL_CODE = "Postal Code"
SITES = "Sites"
from datetime import datetime, timedelta
import numpy as np
from collections import Counter
import re
import os
import sys


import logging
from datetime import datetime
import pymongo


# Page configuration
st.set_page_config(
    page_title="Clinical Trials Analyzer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom theme with company colors
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
    /* Style for highlighted elements with bright orange/red-orange color */
    .highlight {{
        color: {COLORS["highlight"]};
        font-weight: bold;
    }}
    .st-emotion-cache-1gulkj5 {{
        background-color: {COLORS["highlight"]};
        color: white;
    }}
    /* Style for metrics */
    .stMetric .st-emotion-cache-16txtl3 {{
        color: {COLORS["highlight"]};
    }}
    /* Style for important action buttons */
    .stButton.action-btn>button {{
        background-color: {COLORS["highlight"]};
        color: white;
    }}
    /* Expander borders with the new color */
    .streamlit-expanderHeader:hover {{
        border-color: {COLORS["highlight"]};
    }}
</style>
""",
    unsafe_allow_html=True,
)

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TrialAnalytics:
    """Class for clinical trials data analysis."""

    def __init__(self, uri: str, database: str):
        self.uri = uri
        self.database = database
        self.client = None
        self.db = None
        self.collection = None

    def connect(self):
        """Establishes connection to MongoDB."""
        try:
            # Optimized configuration for MongoDB Atlas
            connection_options = {
                "serverSelectionTimeoutMS": 30000,
                "connectTimeoutMS": 30000,
                "socketTimeoutMS": 30000,
                "retryWrites": True,
                "w": "majority",
            }

            self.client = MongoClient(self.uri, **connection_options)
            self.db = self.client[self.database]
            self.collection = self.db.trials

            # Test connection
            self.client.admin.command("ping")
            return True

        except Exception as e:
            # In case of error, try basic connection
            try:
                self.client = MongoClient(
                    self.uri,
                    serverSelectionTimeoutMS=30000,
                    connectTimeoutMS=30000,
                )
                self.db = self.client[self.database]
                self.collection = self.db.trials
                self.client.admin.command("ping")
                return True
            except Exception:
                logger.error(f"MongoDB connection error: {str(e)}")
                if hasattr(self, "client") and self.client:
                    try:
                        self.client.close()
                    except:
                        pass
                return False

    def disconnect(self):
        """Closes MongoDB connection."""
        if self.client:
            self.client.close()

    def get_basic_stats(self):
        """Retrieves basic statistics."""
        try:
            total_trials = self.collection.count_documents({})

            # Statistics by phase
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

            # Statistics by country (Top 10 for display)
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

            # Statistics by country (Complete total for metric)
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

            # Statistics by medical conditions
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

            # Total medical conditions
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
            # Update conditions to include total

            # Retrieve unique therapeutic areas count
            total_therapeutic_areas = self.get_therapeutic_areas_count()

            return {
                "total_trials": total_trials,
                "phases": phases,
                "countries": countries,
                "total_countries": total_countries,  # New: real total
                "conditions": conditions,
                "total_conditions": total_conditions,  # New: real total
                "total_therapeutic_areas": total_therapeutic_areas,  # New: total therapeutic areas
            }
        except Exception as e:
            st.error(f"Error retrieving statistics: {e}")
            return None

    def search_trials_advanced(self, filters):
        """Advanced search for clinical trials."""
        try:
            query = {}

            # Filter by phase
            if filters.get("phase") and filters["phase"] != "All":
                query["summary.trial_information.trial_phase"] = {
                    "$regex": filters["phase"],
                    "$options": "i",
                }

            # Filter by country
            if filters.get("country") and filters["country"] != "All":
                query["locations.countries.country"] = {
                    "$regex": filters["country"],
                    "$options": "i",
                }

            # Filter by medical condition
            if filters.get("condition"):
                query["summary.trial_information.medical_condition"] = {
                    "$regex": filters["condition"],
                    "$options": "i",
                }

            # Filter by sponsor
            if filters.get("sponsor"):
                query["summary.trial_information.sponsor"] = {
                    "$regex": filters["sponsor"],
                    "$options": "i",
                }

            # Filter by date
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
            st.error(f"Error during search: {e}")
            return [], 0

    def get_timeline_data(self):
        """Generates data for trials timeline."""
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
            st.error(f"Error generating timeline: {e}")
            return []

    def get_therapeutic_areas_distribution(self):
        """Analyzes therapeutic areas distribution."""
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
            st.error(f"Error analyzing therapeutic areas: {e}")
            return []

    def get_therapeutic_areas_count(self):
        """Retrieves total number of unique therapeutic areas."""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$trial_information.trial_details.trial_information.therapeutic_area"
                    }
                },
                {"$match": {"_id": {"$ne": None}}},  # Exclude null values
                {"$count": "total"},
            ]

            result = list(self.collection.aggregate(pipeline))
            return result[0]["total"] if result else 0
        except Exception as e:
            st.error(f"Error counting therapeutic areas: {e}")
            return 0

    def get_sponsor_analysis(self):
        """Analysis of trial sponsors."""
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
            st.error(f"Error analyzing sponsors: {e}")
            return []

    def get_geographical_distribution(self):
        """Analysis of geographical distribution."""
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
            st.error(f"Error in geographical analysis: {e}")
            return []

    def get_trial_by_euct(self, euct_number):
        """Retrieves a specific trial by its EUCT number."""
        try:
            trial = self.collection.find_one({"header.euct_number": euct_number})
            return trial
        except Exception as e:
            st.error(f"Error searching for trial {euct_number}: {e}")
            return None

    def search_trials_by_pattern(self, pattern, field="header.euct_number", limit=20):
        """Searches trials by pattern (for autocomplete)."""
        try:
            query = {field: {"$regex": pattern, "$options": "i"}}
            trials = list(self.collection.find(query, {field: 1}).limit(limit))
            return trials
        except Exception as e:
            st.error(f"Error searching by pattern: {e}")
            return []

    def get_all_contacts(self):
        """Extracts all contacts from all trials in the database."""
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

            # Transform to DataFrame format
            all_contacts = []
            for item in contacts_data:
                contact = item.get("contact", {})
                contact_info = {
                    "EUCT Number": item.get("euct_number", "N/A"),
                    "Trial Title": (
                        item.get("trial_title", "N/A")[:50] + "..."
                        if len(str(item.get("trial_title", ""))) > 50
                        else item.get("trial_title", "N/A")
                    ),
                    "Country": item.get("country", "N/A"),
                    "Site": item.get("site_name", "N/A"),
                    "City": item.get("city", "N/A"),
                    "Department": item.get("department", "N/A"),
                    "Title": contact.get("title", ""),
                    "First Name": contact.get("first_name", ""),
                    "Last Name": contact.get("last_name", ""),
                    "Phone": contact.get("phone", ""),
                    "Email": contact.get("email", ""),
                    "Address": item.get("address", "N/A"),
                    "Postal Code": item.get("post_code", "N/A"),
                }
                all_contacts.append(contact_info)

            return all_contacts
        except Exception as e:
            st.error(f"Error extracting contacts: {e}")
            return []

    def get_all_contacts(self):
        """Extracts all contacts from all trials in the database."""
        try:
            # Aggregation pipeline to extract all contacts
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

            # Transform to DataFrame format
            all_contacts = []
            for item in contacts_data:
                contact = item.get("contact", {})
                contact_info = {
                    "EUCT Number": item.get("euct_number", "N/A"),
                    "Trial Title": (
                        item.get("trial_title", "N/A")[:50] + "..."
                        if len(str(item.get("trial_title", ""))) > 50
                        else item.get("trial_title", "N/A")
                    ),
                    "Country": item.get("country", "N/A"),
                    "Site": item.get("site_name", "N/A"),
                    "City": item.get("city", "N/A"),
                    "Department": item.get("department", "N/A"),
                    "Title": contact.get("title", ""),
                    "First Name": contact.get("first_name", ""),
                    "Last Name": contact.get("last_name", ""),
                    "Phone": contact.get("phone", ""),
                    "Email": contact.get("email", ""),
                    "Address": item.get("address", "N/A"),
                    "Postal Code": item.get("post_code", "N/A"),
                }
                all_contacts.append(contact_info)

            return all_contacts
        except Exception as e:
            st.error(f"Error extracting contacts: {e}")
            return []


def get_mongodb_connection_params():
    """Returns MongoDB connection parameters from environment variables.

    These values are retrieved from Streamlit secrets or environment variables
    to secure connection information.
    """
    try:
        # Attempt to retrieve from Streamlit Cloud secrets
        uri = st.secrets["MONGODB_URI"]
        database = st.secrets["MONGODB_DATABASE"]
    except (KeyError, FileNotFoundError):
        # Fallback to environment variables for local development
        import os

        uri = os.getenv("MONGODB_URI", "")
        database = os.getenv("MONGODB_DATABASE", "clinical_trials_db")

        if not uri:
            # Log the error without user display
            logger.error("MONGODB_URI missing in configuration")
            st.stop()

    return uri, database


def test_mongodb_connection(uri, database):
    """Tests MongoDB connection without displaying to user.

    Returns:
        bool: True if connection succeeded, False otherwise.
    """
    try:
        analytics = TrialAnalytics(uri, database)
        return analytics.connect()
    except Exception as e:
        logger.error(f"Connection test error: {str(e)}")
        return False


def create_sidebar():
    """Creates the sidebar with logo."""
    # Add favicon with company name above title
    st.sidebar.image("logo-freearcs_fav-icon.png", width=150, use_container_width=False)

    # Retrieve connection parameters without displaying in UI
    uri, database = get_mongodb_connection_params()

    return uri, database


def display_overview_dashboard(analytics):
    """Displays the general dashboard."""
    # st.markdown(
    #     f"<h1 style='color:{COLORS['primary']};'>📊 Overview</h1>",
    #     unsafe_allow_html=True,
    # )

    # # Colored banner with custom style using highlight color
    # st.markdown(
    #     f"""
    # <div style="background-color:{COLORS['highlight']}; padding:10px; border-radius:10px; margin:10px 0px 20px 0px;">
    #     <h3 style="color:white; margin:0;">Clinical Trials Analyzer - Main Dashboard</h3>
    # </div>
    # """,
    #     unsafe_allow_html=True,
    # )

    # Retrieve statistics with stylized progress bar
    progress_placeholder = st.empty()

    # Display a stylized progress bar before starting loading
    progress_placeholder.markdown(
        f"""
    <div style="width:100%; height:10px; background-color:#f0f0f0; border-radius:5px; margin-bottom:10px;">
        <div style="width:10%; height:10px; background: linear-gradient(90deg, {COLORS['secondary']} 0%, {COLORS['highlight']} 100%); border-radius:5px;"></div>
    </div>
    <p style="text-align:center; color:{COLORS['primary']};">Loading statistics...</p>
    """,
        unsafe_allow_html=True,
    )

    # Load data
    stats = analytics.get_basic_stats()

    # Update progress bar at the end
    progress_placeholder.markdown(
        f"""
    <div style="width:100%; height:10px; background-color:#f0f0f0; border-radius:5px; margin-bottom:10px;">
        <div style="width:100%; height:10px; background: linear-gradient(90deg, {COLORS['secondary']} 0%, {COLORS['highlight']} 100%); border-radius:5px;"></div>
    </div>
    <p style="text-align:center; color:{COLORS['primary']};">Data loaded successfully!</p>
    """,
        unsafe_allow_html=True,
    )

    # Clear indicator after short delay
    time.sleep(1)
    progress_placeholder.empty()

    if not stats:
        st.error("Unable to load statistics")
        return

    # Main metrics with PowerBI style cards
    # CSS to create PowerBI style cards
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

    # Container with spacing
    st.markdown("<div style='padding: 10px;'></div>", unsafe_allow_html=True)

    # Create columns with some space between them
    col1, spacer1, col2, spacer2, col3, spacer3, col4, spacer4, col5 = st.columns(
        [4, 0.3, 4, 0.3, 4, 0.3, 4, 0.3, 4]
    )

    # Metric 1: Total trials
    with col1:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-icon">📋</div>
            <div class="metric-value">{stats["total_trials"]}</div>
            <div class="metric-label">Total Trials</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Metric 2: Medical conditions
    with col2:
        total_conditions = stats.get("total_conditions", len(stats["conditions"]))
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-icon">🏥</div>
            <div class="metric-value">{total_conditions}</div>
            <div class="metric-label">Medical Conditions</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Metric 3: Countries involved
    with col3:
        total_countries = stats.get("total_countries", len(stats["countries"]))
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-icon">🌍</div>
            <div class="metric-value">{total_countries}</div>
            <div class="metric-label">Countries Involved</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Metric 4: Different phases
    with col4:
        phases_count = len(stats["phases"])
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-icon">🧪</div>
            <div class="metric-value">{phases_count}</div>
            <div class="metric-label">Different Phases</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Metric 5: Therapeutic areas
    with col5:
        total_therapeutic_areas = stats.get("total_therapeutic_areas", 0)
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-icon">🧬</div>
            <div class="metric-value">{total_therapeutic_areas}</div>
            <div class="metric-label">Therapeutic Areas</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Espace après les métriques
    st.markdown("<div style='padding: 15px;'></div>", unsafe_allow_html=True)

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
        st.subheader("Distribution by Phase")
        if stats["phases"]:
            phases_df = pd.DataFrame(stats["phases"])
            phases_df["_id"] = phases_df["_id"].fillna("Not specified")

            # Create a custom color sequence that uses all 4 colors from the palette
            color_sequence = [
                COLORS["primary"],  # Brown/Dark gray
                COLORS["secondary"],  # Forest green/Dark green
                COLORS["accent"],  # Grass green/Light green
                COLORS["highlight"],  # Bright orange/Red-orange
            ]

            # For more than 4 phases, create a pattern with these colors
            extended_colors = color_sequence * (len(phases_df) // 4 + 1)

            fig = px.pie(
                phases_df,
                values="count",
                names="_id",
                title="Distribution of trials by phase",
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
        st.subheader("Top 10 Countries")
        if stats["countries"]:
            countries_df = pd.DataFrame(stats["countries"])
            countries_df["_id"] = countries_df["_id"].fillna("Not specified")

            fig = px.bar(
                countries_df.head(10),
                x="count",
                y="_id",
                orientation="h",
                title="Number of trials by country (Top 10)",
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

            # Explanatory note
            total_countries = stats.get("total_countries", len(stats["countries"]))
            st.caption(
                f"💡 Displaying top 10 out of {total_countries} countries total. See 'Advanced Analytics' section for complete list."
            )

    # Medical conditions
    st.subheader("Top 10 Medical Conditions")
    if stats["conditions"]:
        conditions_df = pd.DataFrame(stats["conditions"])
        conditions_df["_id"] = conditions_df["_id"].fillna("Not specified")

        fig = px.bar(
            conditions_df.head(10),
            x="_id",
            y="count",
            title="Number of trials by medical condition",
            color="count",  # Use count for coloring
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
            coloraxis_showscale=False,  # Hide color scale bar
        )
        st.plotly_chart(fig, use_container_width=True)

    # Contacts from all trials
    st.subheader("📞 All Trial Site Contacts")
    with st.spinner("Extracting all contacts..."):
        all_contacts = analytics.get_all_contacts()

    if all_contacts:
        st.write(f"**{len(all_contacts)} contact(s) found in the database:**")

        # Create contact DataFrame
        contacts_df = pd.DataFrame(all_contacts)

        # Reorganize columns for better display
        columns_order = [
            "EUCT Number",
            "Trial Title",
            "Country",
            "Site",
            "City",
            "Department",
            "Title",
            "First Name",
            "Last Name",
            "Phone",
            "Email",
            "Address",
            "Postal Code",
        ]

        # Ensure all columns exist
        for col in columns_order:
            if col not in contacts_df.columns:
                contacts_df[col] = ""

        contacts_df = contacts_df[columns_order]

        # Filter by country to improve user experience
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            # Filter by country
            unique_countries = sorted(contacts_df["Country"].unique().tolist())
            selected_country = st.selectbox(
                "Filter by country:",
                ["All"] + unique_countries,
                key="contact_country_filter",
            )

        with col2:
            # Filter by number of entries to display
            display_limit = st.selectbox(
                "Number of entries:",
                [50, 100, 200, 500, "All"],
                index=1,
                key="contact_display_limit",
            )

        with col3:
            # Search by name/email
            search_term = st.text_input(
                "Search (name, email, site):", key="contact_search"
            )

        # Apply filters
        filtered_df = contacts_df.copy()

        if selected_country != "All":
            filtered_df = filtered_df[filtered_df["Country"] == selected_country]

        if search_term:
            # Search in multiple columns
            search_mask = (
                filtered_df["Last Name"].str.contains(search_term, case=False, na=False)
                | filtered_df["First Name"].str.contains(
                    search_term, case=False, na=False
                )
                | filtered_df["Email"].str.contains(search_term, case=False, na=False)
                | filtered_df["Site"].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[search_mask]

        if display_limit != "All":
            filtered_df = filtered_df.head(int(display_limit))

        # Display DataFrame with sorting possibility
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=min(500, len(filtered_df) * 35 + 100),  # Dynamic height
            column_config={
                "EUCT Number": st.column_config.TextColumn("EUCT", width="medium"),
                "Trial Title": st.column_config.TextColumn("Trial", width="large"),
                "Email": st.column_config.TextColumn("Email", width="medium"),
                "Phone": st.column_config.TextColumn("Phone", width="medium"),
                "Site": st.column_config.TextColumn("Site", width="large"),
                "Address": st.column_config.TextColumn("Address", width="large"),
            },
        )

        # Contact statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total contacts", len(all_contacts))
        with col2:
            st.metric("Displayed contacts", len(filtered_df))
        with col3:
            contacts_with_email = len(filtered_df[filtered_df["Email"] != ""])
            st.metric("With email", contacts_with_email)
        with col4:
            contacts_with_phone = len(filtered_df[filtered_df["Phone"] != ""])
            st.metric("With phone", contacts_with_phone)

        # Download option
        col1, col2 = st.columns([1, 3])
        with col1:
            # Use a div container to apply CSS class to button
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

                if st.button("💾 Download contacts (CSV)", key="download_all_contacts"):
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"all_trial_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="download_csv_all_contacts",
                    )

        with col2:
            st.caption(
                "💡 Use filters to refine your search. Click on column headers to sort data."
            )

    else:
        st.info("No contacts found in the database.")


def display_advanced_search(analytics):
    """Displays the advanced search interface."""
    st.header("🔍 Advanced Search")

    # Search form
    with st.form("advanced_search"):
        col1, col2, col3 = st.columns(3)

        with col1:
            phase = st.selectbox(
                "Trial phase",
                [
                    "All",
                    "Phase I",
                    "Phase II",
                    "Phase III",
                    "Phase IV",
                    "Phase I/II",
                    "Phase II/III",
                ],
            )

            condition = st.text_input("Medical condition (partial search)")

        with col2:
            country = st.selectbox(
                "Country",
                [
                    "All",
                    "France",
                    "Germany",
                    "Spain",
                    "Italy",
                    "United Kingdom",
                    "Netherlands",
                ],
            )

            sponsor = st.text_input("Sponsor (partial search)")

        with col3:
            date_from = st.date_input("Start date", value=None)
            date_to = st.date_input("End date", value=None)

            limit = st.number_input(
                "Max number of results", min_value=10, max_value=500, value=50
            )

        search_button = st.form_submit_button("🔍 Search")

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

        with st.spinner("Search in progress..."):
            trials, total_count = analytics.search_trials_advanced(filters)

        st.success(f"🎯 {len(trials)} trials found out of {total_count} total")

        if trials:
            # Display results
            for i, trial in enumerate(trials):
                with st.expander(
                    f"#{i+1} - {trial.get('header', {}).get('euct_number', 'N/A')}"
                ):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(
                            "**Title:**", trial.get("header", {}).get("title", "N/A")
                        )
                        st.write(
                            "**Phase:**",
                            trial.get("summary", {})
                            .get("trial_information", {})
                            .get("trial_phase", "N/A"),
                        )
                        # Highlight medical condition with highlight color
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
                            "**Therapeutic area:**",
                            trial.get("summary", {})
                            .get("trial_information", {})
                            .get("therapeutic_area", "N/A"),
                        )

                        # Participating countries
                        countries_data = trial.get("locations", {}).get("countries", [])
                        if countries_data:
                            countries = [
                                country.get("country", "N/A")
                                for country in countries_data
                            ]
                            st.write(
                                "**Countries:**",
                                ", ".join(countries[:3])
                                + ("..." if len(countries) > 3 else ""),
                            )


def display_analytics_dashboard(analytics):
    """Displays the advanced analytics dashboard."""
    st.header("📈 Advanced Analytics")

    # Trial timeline
    st.subheader("📅 Trial Timeline")
    with st.spinner("Generating timeline..."):
        timeline_data = analytics.get_timeline_data()

    if timeline_data:
        timeline_df = pd.DataFrame(timeline_data)
        timeline_df["date"] = pd.to_datetime(timeline_df["_id"])
        timeline_df = timeline_df.sort_values("date")

        fig = px.line(
            timeline_df,
            x="date",
            y="count",
            title="Evolution of trial numbers over time",
            markers=True,
            color_discrete_sequence=[COLORS["secondary"]],
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of trials",
            title_font_color=COLORS["primary"],
            font_color=COLORS["text"],
            paper_bgcolor=COLORS["background"],
            plot_bgcolor=COLORS["background"],
        )
        # Add trend line in accent color
        fig.add_scatter(
            x=timeline_df["date"],
            y=timeline_df["count"].rolling(3, center=True).mean(),
            mode="lines",
            line=dict(color=COLORS["accent"], dash="dot"),
            name="Trend",
        )
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    # Therapeutic areas
    with col1:
        st.subheader("🧬 Therapeutic Areas")
        with st.spinner("Analyzing therapeutic areas..."):
            therapeutic_areas = analytics.get_therapeutic_areas_distribution()

        if therapeutic_areas:
            areas_df = pd.DataFrame(therapeutic_areas)
            areas_df["_id"] = areas_df["_id"].fillna("Not specified")

            # Handle long names
            areas_df["short_name"] = areas_df["_id"].apply(
                lambda x: x[:30] + "..." if len(str(x)) > 30 else x
            )

            # Create treemap chart for therapeutic areas
            fig = px.treemap(
                areas_df.head(10),
                path=["short_name"],
                values="count",
                title="Distribution of therapeutic areas",
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
                coloraxis_showscale=False,  # Hide color scale
            )
            st.plotly_chart(fig, use_container_width=True)

            # Optionally, add radar chart for alternative visualization
            with st.expander("🔄 See alternative visualization (Radar)"):
                # Prepare data for radar (top 6 for readability)
                top_areas = areas_df.head(6).copy()

                fig_radar = go.Figure()

                fig_radar.add_trace(
                    go.Scatterpolar(
                        r=top_areas["count"],
                        theta=top_areas["short_name"],
                        fill="toself",
                        line=dict(color=COLORS["highlight"], width=2),
                        fillcolor=f'rgba({int(COLORS["highlight"][1:3], 16)}, {int(COLORS["highlight"][3:5], 16)}, {int(COLORS["highlight"][5:7], 16)}, 0.3)',
                    )
                )

                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True, range=[0, max(top_areas["count"]) * 1.1]
                        )
                    ),
                    showlegend=False,
                    title="Top 6 therapeutic areas (Radar)",
                    title_font_color=COLORS["primary"],
                    paper_bgcolor=COLORS["background"],
                )

                st.plotly_chart(fig_radar, use_container_width=True)

    # Sponsor analysis
    with col2:
        st.subheader("🏢 Top Sponsors")
        with st.spinner("Analyzing sponsors..."):
            sponsors = analytics.get_sponsor_analysis()

        if sponsors:
            sponsors_df = pd.DataFrame(sponsors)
            sponsors_df["_id"] = sponsors_df["_id"].fillna("Not specified")

            fig = px.bar(
                sponsors_df.head(10),
                x="count",
                y="_id",
                orientation="h",
                title="Most active sponsors",
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

    # Geographic distribution
    st.markdown(
        f"""
    <div style="background-color:{COLORS['primary']}; padding:5px; border-radius:5px; margin:10px 0px 15px 0px;">
        <h3 style="color:white; margin:0; text-align:center;">🗺️ Geographic Distribution</h3>
    </div>
    """,
        unsafe_allow_html=True,
    )

    with st.spinner("Geographic analysis..."):
        geo_data = analytics.get_geographical_distribution()

    if geo_data:
        geo_df = pd.DataFrame(geo_data)
        geo_df["_id"] = geo_df["_id"].fillna("Not specified")

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
                title="Number of trials by country",
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
            # Styled header
            st.markdown(
                f"""
            <h4 style="color:{COLORS['primary']};">Details by country</h4>
            """,
                unsafe_allow_html=True,
            )

            # Key metrics with highlight color
            total_trials = geo_df["trials_count"].sum()
            total_sites = geo_df["sites_count"].sum()
            top_country = geo_df.sort_values("trials_count", ascending=False).iloc[0]

            st.markdown(
                f"""
            <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
                <div style="text-align:center; padding:10px; background-color:white; border-radius:5px; box-shadow:0 0 5px rgba(0,0,0,0.1); flex:1; margin-right:5px;">
                    <p style="font-size:14px; margin:0;">Total trials</p>
                    <p style="font-size:24px; color:{COLORS['highlight']}; font-weight:bold; margin:0;">{total_trials}</p>
                </div>
                <div style="text-align:center; padding:10px; background-color:white; border-radius:5px; box-shadow:0 0 5px rgba(0,0,0,0.1); flex:1; margin-left:5px;">
                    <p style="font-size:14px; margin:0;">Total sites</p>
                    <p style="font-size:24px; color:{COLORS['highlight']}; font-weight:bold; margin:0;">{total_sites}</p>
                </div>
            </div>
            <div style="text-align:center; padding:10px; background-color:white; border-radius:5px; box-shadow:0 0 5px rgba(0,0,0,0.1); margin-bottom:15px;">
                <p style="font-size:14px; margin:0;">Most active country</p>
                <p style="font-size:20px; color:{COLORS['highlight']}; font-weight:bold; margin:0;">{top_country['_id']} ({top_country['trials_count']} trials)</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Data table
            geo_df_sorted = geo_df.sort_values("trials_count", ascending=False)
            st.dataframe(
                geo_df_sorted[["_id", "trials_count", "sites_count"]].rename(
                    columns={
                        "_id": "Country",
                        "trials_count": "Number of trials",
                        "sites_count": "Number of sites",
                    }
                ),
                use_container_width=True,
                height=300,
            )


def display_individual_trial_analysis(analytics):
    """Displays detailed analysis of an individual trial."""
    st.header("🔍 Individual Trial Analysis")

    # Trial search interface
    st.subheader("📋 Trial Search")

    col1, col2 = st.columns([3, 1])

    with col1:
        euct_number = st.text_input(
            "EUCT Number",
            value="2022-500013-32-01",
            help="Enter the EUCT number of the trial to analyze",
            placeholder="YYYY-NNNNNN-NN-NN",
        )

    with col2:
        search_button = st.button("🔍 Search trial")

    # Automatic or manual search
    if search_button or euct_number:
        with st.spinner(f"Searching for trial {euct_number}..."):
            trial = analytics.get_trial_by_euct(euct_number)

        if trial:
            st.success(f"✅ Trial {euct_number} found!")

            # Display trial information
            display_trial_details(trial)
        else:
            st.error(f"❌ No trial found with EUCT number: {euct_number}")

            # Similar trial suggestions
            st.subheader("💡 Similar trial suggestions")
            if len(euct_number) >= 4:
                pattern = euct_number[:4]  # Search by year
                similar_trials = analytics.search_trials_by_pattern(pattern)

                if similar_trials:
                    st.write("**Trials from the same year:**")
                    for trial_ref in similar_trials[:10]:
                        euct = trial_ref.get("header", {}).get("euct_number", "N/A")
                        if st.button(f"📋 {euct}", key=f"similar_{euct}"):
                            st.experimental_rerun()


def display_trial_details(trial):
    """Displays the complete details of a trial."""

    # Main information
    st.subheader("📋 Main Information")

    header = trial.get("header", {})
    summary = trial.get("summary", {})
    trial_info = summary.get("trial_information", {})

    col1, col2 = st.columns(2)

    with col1:
        st.write("**EUCT Number:**", header.get("euct_number", NOT_SPECIFIED))
        st.write("**Protocol Code:**", header.get("protocol_code", NOT_SPECIFIED))
        st.write("**Title:**", header.get("title", NOT_SPECIFIED))
        st.write("**Phase:**", trial_info.get("trial_phase", NOT_SPECIFIED))
        st.write(
            "**Medical Condition:**", trial_info.get("medical_condition", NOT_SPECIFIED)
        )
        st.write(
            "**Therapeutic Area:**", trial_info.get("therapeutic_area", NOT_SPECIFIED)
        )

    with col2:
        st.write("**Sponsor:**", trial_info.get("sponsor", NOT_SPECIFIED))

        # Overall trial status
        overall_status = summary.get("overall_trial_status", {})
        st.write("**Status:**", overall_status.get("status", NOT_SPECIFIED))
        st.write("**Start Date:**", overall_status.get("start_date", NOT_SPECIFIED))

        # Important dates
        trial_duration = summary.get("trial_duration", {})
        st.write(
            "**Recruitment Start:**",
            trial_duration.get("estimated_recruitment_start", NOT_SPECIFIED),
        )
        st.write(
            "**Estimated End:**",
            trial_duration.get("estimated_end_date", NOT_SPECIFIED),
        )
        st.write(
            "**Estimated Global End:**",
            trial_duration.get("estimated_global_end_date", NOT_SPECIFIED),
        )

    # Trial objectives
    st.subheader("🎯 Trial Objectives")

    # Main objective is in trial_information.main_objective
    main_objective = trial_info.get("main_objective", "")

    if main_objective:
        st.write("**Primary Objective:**")
        st.write(main_objective)
    else:
        # Fallback to old structure if it exists
        objectives = summary.get("trial_objectives", {})
        if objectives:
            primary_obj = objectives.get("primary_objective", NOT_SPECIFIED)
            secondary_obj = objectives.get("secondary_objectives", NOT_SPECIFIED)

            st.write("**Primary Objective:**")
            st.write(primary_obj)

            if secondary_obj and secondary_obj != NOT_SPECIFIED:
                st.write("**Secondary Objectives:**")
                st.write(secondary_obj)
        else:
            st.info("No objectives specified for this trial.")

    # Detailed status by country
    st.subheader("📊 Detailed Status by Country")
    overall_status = summary.get("overall_trial_status", {})
    application_trial_status = overall_status.get("application_trial_status", [])

    if application_trial_status:
        st.write("**Status in each Member State:**")

        # Create DataFrame for status by country
        status_data = []
        for status_info in application_trial_status:
            status_data.append(
                {
                    "Member State": status_info.get("member_state", NOT_SPECIFIED),
                    "Status": status_info.get(
                        "application_trial_status", NOT_SPECIFIED
                    ),
                    "Decision Date": status_info.get("decision_date", NOT_SPECIFIED),
                }
            )

        if status_data:
            status_df = pd.DataFrame(status_data)
            st.dataframe(
                status_df,
                use_container_width=True,
                height=min(300, len(status_df) * 35 + 100),  # Dynamic height
                column_config={
                    "Member State": st.column_config.TextColumn(
                        "Member State", width="medium"
                    ),
                    "Status": st.column_config.TextColumn("Status", width="large"),
                    "Decision Date": st.column_config.DateColumn(
                        "Decision Date", width="medium"
                    ),
                },
            )

        # Global status statistics
        if overall_status.get("status"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "**Global Status**", overall_status.get("status", NOT_SPECIFIED)
                )
            with col2:
                st.metric(
                    "**Global Start Date**",
                    overall_status.get("start_date", NOT_SPECIFIED),
                )
    else:
        st.info("No detailed status information available.")

    # Trial population
    st.subheader("👥 Trial Population")
    population = summary.get("population", {})
    if population:
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Age:**", population.get("age", NOT_SPECIFIED))
            st.write("**Gender:**", population.get("gender", NOT_SPECIFIED))
            st.write(
                "**Number of subjects:**",
                population.get("number_of_subjects", NOT_SPECIFIED),
            )

        with col2:
            st.write("**Inclusion criteria:**")
            inclusion = population.get("inclusion_criteria", NOT_SPECIFIED)
            st.write(
                inclusion[:500] + "..." if len(str(inclusion)) > 500 else inclusion
            )

    # Geolocation and sites
    st.subheader("🌍 Geolocation and Sites")
    locations = trial.get("locations", {})
    countries = locations.get("countries", [])

    if countries:
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Participating countries:**")
            countries_data = []
            for country in countries:
                country_name = country.get("country", NOT_SPECIFIED)
                sites_count = country.get("competent_authority_sites", "0")
                countries_data.append({COUNTRY: country_name, SITES: sites_count})

            countries_df = pd.DataFrame(countries_data)
            st.dataframe(countries_df, use_container_width=True)

        with col2:
            if len(countries_data) > 1:
                # Chart of sites by country
                fig = px.bar(
                    countries_df, x=COUNTRY, y=SITES, title="Number of sites by country"
                )
                fig.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

    # Investigational medicinal product
    st.subheader("💊 Investigational Medicinal Product")
    imp = summary.get("investigational_medicinal_product", {})
    if imp:
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Product name:**", imp.get("product_name", NOT_SPECIFIED))
            st.write(
                "**Active substance:**", imp.get("active_substance", NOT_SPECIFIED)
            )
            st.write("**ATC code:**", imp.get("atc_code", NOT_SPECIFIED))

        with col2:
            st.write(
                "**Pharmaceutical form:**",
                imp.get("pharmaceutical_form", NOT_SPECIFIED),
            )
            st.write(
                "**Route of administration:**",
                imp.get("route_of_administration", NOT_SPECIFIED),
            )
            st.write("**Concentration:**", imp.get("concentration", NOT_SPECIFIED))

    # Trial design
    st.subheader("🔬 Trial Design")
    design = summary.get("trial_design", {})
    if design:
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Control type:**", design.get("controlled", NOT_SPECIFIED))
            st.write("**Randomized:**", design.get("randomised", NOT_SPECIFIED))
            st.write("**Blinded:**", design.get("blinded", NOT_SPECIFIED))

        with col2:
            st.write(
                "**Treatment groups:**", design.get("treatment_groups", NOT_SPECIFIED)
            )
            st.write("**Allocation:**", design.get("allocation", NOT_SPECIFIED))

    # Contact data
    st.subheader("📞 Site Contacts")

    # Extract site contacts
    site_contacts = extract_site_contacts(trial)

    if site_contacts:
        st.write(f"**{len(site_contacts)} contact(s) found in trial sites:**")

        # Display as DataFrame
        contacts_df = pd.DataFrame(site_contacts)

        # Reorganize columns for better display
        columns_order = [
            COUNTRY,
            SITE,
            CITY,
            DEPARTMENT,
            TITLE,
            FIRST_NAME,
            LAST_NAME,
            PHONE,
            EMAIL,
            ADDRESS,
            POSTAL_CODE,
        ]

        # Ensure all columns exist
        for col in columns_order:
            if col not in contacts_df.columns:
                contacts_df[col] = ""

        contacts_df = contacts_df[columns_order]

        # Display DataFrame with sorting capability
        st.dataframe(
            contacts_df,
            use_container_width=True,
            height=min(400, len(contacts_df) * 35 + 100),  # Dynamic height
            column_config={
                EMAIL: st.column_config.TextColumn(EMAIL, width="medium"),
                PHONE: st.column_config.TextColumn(PHONE, width="medium"),
                SITE: st.column_config.TextColumn(SITE, width="large"),
                ADDRESS: st.column_config.TextColumn(ADDRESS, width="large"),
            },
        )

        # Contact download option
        if st.button("💾 Download contacts (CSV)"):
            csv = contacts_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"trial_contacts_{trial.get('header', {}).get('euct_number', 'unknown')}.csv",
                mime="text/csv",
            )
    else:
        st.info("No contact information available for this trial's sites.")

    # General contacts (if they exist in traditional structure)
    contacts = trial.get("contacts", {})
    if contacts:
        with st.expander("📞 Other contacts (traditional structure)"):
            # Main contact
            main_contact = contacts.get("main_contact", {})
            if main_contact:
                st.write("**Main contact:**")
                st.write(f"- Name: {main_contact.get('name', NOT_SPECIFIED)}")
                st.write(f"- Email: {main_contact.get('email', NOT_SPECIFIED)}")
                st.write(f"- Phone: {main_contact.get('phone', NOT_SPECIFIED)}")

            # Scientific contact
            scientific_contact = contacts.get("scientific_contact", {})
            if scientific_contact:
                st.write("**Scientific contact:**")
                st.write(f"- Name: {scientific_contact.get('name', NOT_SPECIFIED)}")
                st.write(f"- Email: {scientific_contact.get('email', NOT_SPECIFIED)}")

    # Raw data (optional)
    with st.expander("🔧 Raw data (JSON)"):
        st.json(trial)


def extract_site_contacts(trial):
    """Extracts all contacts from trial sites."""
    contacts_list = []

    locations = trial.get("locations", {})
    countries = locations.get("countries", [])

    for country in countries:
        country_name = country.get("country", NOT_SPECIFIED)
        sites = country.get("sites", [])

        for site in sites:
            contact = site.get("contact", {})
            if contact:  # Only if contact information exists
                contact_info = {
                    COUNTRY: country_name,
                    SITE: site.get("name", NOT_SPECIFIED),
                    CITY: site.get("city", NOT_SPECIFIED),
                    DEPARTMENT: site.get("department", NOT_SPECIFIED),
                    TITLE: contact.get("title", ""),
                    FIRST_NAME: contact.get("first_name", ""),
                    LAST_NAME: contact.get("last_name", ""),
                    PHONE: contact.get("phone", ""),
                    EMAIL: contact.get("email", ""),
                    ADDRESS: site.get("address", NOT_SPECIFIED),
                    POSTAL_CODE: site.get("post_code", NOT_SPECIFIED),
                }
                contacts_list.append(contact_info)

    return contacts_list


def display_custom_queries(analytics):
    """Interface for custom MongoDB queries."""
    st.header("⚙️ Custom Queries")

    st.info("Execute custom MongoDB queries for specific analyses.")

    # Predefined query examples
    st.subheader("📝 Query Examples")

    query_examples = {
        "Trials by phase": {
            "description": "Count trials by phase",
            "query": '[\n  {"$group": {"_id": "$summary.trial_information.trial_phase", "count": {"$sum": 1}}},\n  {"$sort": {"count": -1}}\n]',
        },
        "Recent trials": {
            "description": "Trials added in the last 30 days",
            "query": '{\n  "date_added": {\n    "$gte": "'
            + (datetime.now() - timedelta(days=30)).isoformat()
            + '"\n  }\n}',
        },
        "Trials by sponsor": {
            "description": "Top 10 most active sponsors",
            "query": '[\n  {"$group": {"_id": "$summary.trial_information.sponsor", "count": {"$sum": 1}}},\n  {"$sort": {"count": -1}},\n  {"$limit": 10}\n]',
        },
    }

    selected_example = st.selectbox(
        "Choose an example", ["Custom"] + list(query_examples.keys())
    )

    if selected_example != "Custom":
        example = query_examples[selected_example]
        st.write(f"**Description:** {example['description']}")
        default_query = example["query"]
    else:
        default_query = "{}"

    # Query interface
    col1, col2 = st.columns([2, 1])

    with col1:
        query_text = st.text_area(
            "MongoDB Query (JSON)",
            value=default_query,
            height=200,
            help="Enter a valid MongoDB query in JSON format",
        )

    with col2:
        query_type = st.radio(
            "Query type",
            ["find", "aggregate"],
            help="find: simple query, aggregate: aggregation pipeline",
        )

        limit_results = st.number_input(
            "Results limit", min_value=1, max_value=1000, value=100
        )

        execute_button = st.button("▶️ Execute", type="primary")

    if execute_button:
        try:
            # JSON query parsing
            if query_type == "find":
                query = json.loads(query_text)
                cursor = analytics.collection.find(query).limit(limit_results)
                results = list(cursor)
            else:  # aggregate
                pipeline = json.loads(query_text)
                results = list(analytics.collection.aggregate(pipeline))

            st.success(f"✅ Query executed successfully - {len(results)} result(s)")

            if results:
                # Display results
                st.subheader("📊 Results")

                # Attempt to create DataFrame for display
                try:
                    df = pd.json_normalize(results)
                    st.dataframe(df, use_container_width=True, height=400)
                except:
                    # JSON display if normalization fails
                    st.json(results[:10])  # Limit to 10 to avoid clutter
                    if len(results) > 10:
                        st.info(f"Displaying first 10 results out of {len(results)}")

                # Download option
                if st.button("💾 Download results (JSON)"):
                    results_json = json.dumps(
                        results, indent=2, default=str, ensure_ascii=False
                    )
                    st.download_button(
                        label="📥 Download",
                        data=results_json,
                        file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                    )
            else:
                st.warning("No results found")

        except json.JSONDecodeError as e:
            st.error(f"❌ JSON parsing error: {e}")
        except Exception as e:
            st.error(f"❌ Error executing query: {e}")


def main():
    """Main function of the Streamlit application."""

    # Styled header with company colored banner
    st.markdown(
        f"""
    <div style="background: linear-gradient(90deg, {COLORS['primary']} 0%, {COLORS['secondary']} 50%, {COLORS['highlight']} 100%); 
                padding: 20px; border-radius: 10px; margin-bottom: 20px; display: flex; align-items: center;">
        <div style="background-color: white; padding: 10px; border-radius: 50%; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center;">
            <span style="font-size: 30px;">🔬</span>
        </div>
        <div style="flex: 1; text-align: center;">
            <h1 style="color: white; margin: 0;">Clinical Trials Analyzer</h1>
            <p style="color: white; margin: 0; font-size: 16px;">Clinical trials data analysis and visualization platform</p>
        </div>
        <div style="background-color: white; padding: 10px; border-radius: 50%; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center;">
            <span style="font-size: 30px;">🧪</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Sidebar configuration
    uri, database = create_sidebar()

    # Silent connection test at startup
    connection_status = test_mongodb_connection(uri, database)
    if not connection_status:
        # Log the problem without user display
        logger.warning("MongoDB connection impossible during initial test")

    # Navigation
    st.sidebar.markdown("---")
    st.sidebar.title("📱 Navigation")

    pages = {
        "Overview": "📊",
        "Advanced Search": "🔍",
        "Advanced Analytics": "📈",
        "Individual Analysis": "🔍",
        "Custom Queries": "⚙️",
    }

    selected_page = st.sidebar.radio(
        "Choose a page", list(pages.keys()), format_func=lambda x: f"{pages[x]} {x}"
    )

    # Connection initialization
    analytics = TrialAnalytics(uri, database)

    if not analytics.connect():
        st.error("❌ Service temporarily unavailable. Please try again later.")
        st.stop()

    try:
        # Display selected page
        if selected_page == "Overview":
            display_overview_dashboard(analytics)
        elif selected_page == "Advanced Search":
            display_advanced_search(analytics)
        elif selected_page == "Advanced Analytics":
            display_analytics_dashboard(analytics)
        elif selected_page == "Individual Analysis":
            display_individual_trial_analysis(analytics)
        elif selected_page == "Custom Queries":
            display_custom_queries(analytics)

    except Exception as e:
        st.error(f"❌ Application error: {e}")
        logger.error(f"Application error: {e}")

    finally:
        analytics.disconnect()

    # Sidebar footer
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"""
    <div style="background-color: {COLORS['primary']}; padding: 10px; border-radius: 5px; margin-top: 15px;">
        <h4 style="color: white; margin: 0; text-align: center;">💡 Usage Tips</h4>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Styled list
    st.sidebar.markdown(
        f"""
    <ul style="list-style-type: none; padding-left: 5px;">
      <li style="margin-bottom: 8px;">
        <span style="color: {COLORS['highlight']};">•</span> Test connection before use
      </li>
      <li style="margin-bottom: 8px;">
        <span style="color: {COLORS['highlight']};">•</span> Use filters to refine your searches
      </li>
      <li style="margin-bottom: 8px;">
        <span style="color: {COLORS['highlight']};">•</span> Custom queries allow specific analyses
      </li>
      <li style="margin-bottom: 8px;">
        <span style="color: {COLORS['highlight']};">•</span> Download results for external analysis
      </li>
    </ul>
    """,
        unsafe_allow_html=True,
    )

    # General footer at bottom of application
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
        <p style="color: {COLORS['secondary']}; font-size: 14px; margin: 5px 0;">Clinical Trials Analyzer © 2025</p>
        <p style="color: {COLORS['primary']}; font-size: 12px;">Version 1.0 | Last updated: June 22, 2025</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
