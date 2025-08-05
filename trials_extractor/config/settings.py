"""
Paramètres généraux de configuration pour l'extracteur de données d'essais cliniques.
"""

import os
from pathlib import Path

# Chemins de base
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = os.path.join(BASE_DIR.parent, "output")

# Formats d'export disponibles
EXPORT_FORMATS = ["json", "csv"]

# Paramètres d'export JSON
JSON_SETTINGS = {
    "indent": 4,
    "ensure_ascii": False,
}

# Paramètres d'export CSV
CSV_SETTINGS = {
    "delimiter": ",",
    "quotechar": '"',
    "quoting": 1,  # csv.QUOTE_ALL
    "encoding": "utf-8",
}

# Sections disponibles pour l'extraction
AVAILABLE_SECTIONS = [
    "header",
    "summary",
    "trial_info",
    "results",
    "locations",
]

# Paramètres de journalisation
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
        "simple": {"format": "%(levelname)s - %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "verbose",
            "filename": os.path.join(BASE_DIR.parent, "extraction.log"),
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "DEBUG",
    },
}

# Paramètres de normalisation des données
NORMALIZATION = {
    "date_formats": [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
    ],
    "output_date_format": "%Y-%m-%d",
    "boolean_true_values": ["yes", "y", "true", "t", "1", "oui"],
    "boolean_false_values": ["no", "n", "false", "f", "0", "non"],
}

# Paramètres de validation des données
VALIDATION = {
    "required_sections": ["header", "summary", "trial_information", "locations"],
    "required_fields": {
        "header": ["euct_number"],
        "summary.trial_information": ["medical_condition", "trial_phase"],
    },
}

# Paramètres de traitement par lots
BATCH_PROCESSING = {
    "max_workers": os.cpu_count() or 4,
    "chunk_size": 10,
}

# Paramètres de stockage MongoDB
MONGODB_SETTINGS = {
    "connection_string": os.getenv("MONGODB_URI", "mongodb://localhost:27017/"),
    "database_name": os.getenv("MONGODB_DATABASE", "clinical_trials_db"),
    "collection_name": os.getenv("MONGODB_COLLECTION", "trials"),
    "connection_timeout": 5000,  # millisecondes
    "max_pool_size": 50,
    "enable_storage": os.getenv("ENABLE_MONGODB_STORAGE", "false").lower() == "true",
}
