"""
Utilitaires pour le traitement et la normalisation des dates.
"""

import logging
import re
from datetime import datetime
import dateutil.parser
from clinical_trials_extractor.config.settings import NORMALIZATION

logger = logging.getLogger(__name__)

def normalize_date(date_str):
    """
    Normalise une date au format ISO 8601 (YYYY-MM-DD).
    
    Args:
        date_str (str): Chaîne représentant une date
        
    Returns:
        str: Date normalisée au format ISO 8601, ou None si la conversion échoue
    """
    if not date_str or not isinstance(date_str, str):
        return None
        
    date_str = date_str.strip()
    if not date_str:
        return None
    
    # Suppression des caractères non numériques sauf les séparateurs
    date_str = re.sub(r'[^\d/\-\.]', ' ', date_str)
    date_str = re.sub(r'\s+', ' ', date_str).strip()
    
    try:
        # Essai de parsing avec dateutil
        dt = dateutil.parser.parse(date_str, dayfirst=True)
        return dt.strftime(NORMALIZATION['output_date_format'])
    except (ValueError, TypeError):
        # Tentative avec des formats courants
        for fmt in NORMALIZATION['date_formats']:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime(NORMALIZATION['output_date_format'])
            except ValueError:
                continue
                
        logger.warning(f"Impossible de normaliser la date: {date_str}")
        return date_str

def normalize_boolean(value):
    """
    Normalise une valeur booléenne (Yes/No → true/false).
    
    Args:
        value (str): Valeur à normaliser
        
    Returns:
        bool: Valeur booléenne normalisée, ou None si la conversion échoue
    """
    if not value or not isinstance(value, str):
        return None
        
    value = value.strip().lower()
    
    if value in NORMALIZATION['boolean_true_values']:
        return True
    elif value in NORMALIZATION['boolean_false_values']:
        return False
    else:
        logger.warning(f"Impossible de normaliser la valeur booléenne: {value}")
        return None

def extract_year(date_str):
    """
    Extrait l'année d'une date.
    
    Args:
        date_str (str): Chaîne représentant une date
        
    Returns:
        int: Année extraite, ou None si l'extraction échoue
    """
    normalized_date = normalize_date(date_str)
    if not normalized_date or normalized_date == date_str:
        # Tentative d'extraction directe avec regex
        year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if year_match:
            return int(year_match.group(0))
        return None
    
    try:
        return int(normalized_date.split('-')[0])
    except (IndexError, ValueError):
        return None

def calculate_duration(start_date, end_date):
    """
    Calcule la durée entre deux dates en jours.
    
    Args:
        start_date (str): Date de début
        end_date (str): Date de fin
        
    Returns:
        int: Durée en jours, ou None si le calcul échoue
    """
    start = normalize_date(start_date)
    end = normalize_date(end_date)
    
    if not start or not end:
        return None
    
    try:
        start_dt = datetime.strptime(start, NORMALIZATION['output_date_format'])
        end_dt = datetime.strptime(end, NORMALIZATION['output_date_format'])
        delta = end_dt - start_dt
        return delta.days
    except ValueError:
        logger.warning(f"Impossible de calculer la durée entre {start} et {end}")
        return None

def is_date_valid(date_str):
    """
    Vérifie si une chaîne représente une date valide.
    
    Args:
        date_str (str): Chaîne à vérifier
        
    Returns:
        bool: True si la chaîne est une date valide, False sinon
    """
    normalized = normalize_date(date_str)
    return normalized is not None and normalized != date_str