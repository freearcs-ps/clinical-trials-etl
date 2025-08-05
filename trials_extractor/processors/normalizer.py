"""
Module pour la normalisation des données extraites.
"""

import logging
import re
from datetime import datetime
import dateutil.parser
from clinical_trials_extractor.config.settings import NORMALIZATION
from clinical_trials_extractor.utils.date_utils import normalize_date, normalize_boolean

logger = logging.getLogger(__name__)

def normalize_string(value):
    """
    Normalise une chaîne de caractères.
    
    Args:
        value (str): Chaîne à normaliser
        
    Returns:
        str: Chaîne normalisée
    """
    if not value or not isinstance(value, str):
        return value
    
    # Suppression des espaces multiples
    normalized = re.sub(r'\s+', ' ', value)
    # Suppression des espaces en début et fin
    normalized = normalized.strip()
    
    return normalized

def normalize_number(value):
    """
    Normalise une valeur numérique.
    
    Args:
        value (str): Valeur à normaliser
        
    Returns:
        int|float|str: Valeur numérique normalisée, ou la chaîne originale si la conversion échoue
    """
    if not value or not isinstance(value, str):
        return value
    
    value = value.strip()
    
    # Tentative de conversion en entier
    try:
        return int(value)
    except ValueError:
        pass
    
    # Tentative de conversion en nombre à virgule flottante
    try:
        # Remplacement de la virgule par un point si nécessaire
        value = value.replace(',', '.')
        return float(value)
    except ValueError:
        pass
    
    # Si la conversion échoue, retourner la chaîne originale
    return value

def normalize_list(value, separator=','):
    """
    Normalise une liste (chaîne séparée par des virgules).
    
    Args:
        value (str): Chaîne à normaliser
        separator (str): Séparateur utilisé dans la chaîne
        
    Returns:
        list: Liste normalisée
    """
    if not value or not isinstance(value, str):
        return []
    
    # Séparation des éléments
    items = [item.strip() for item in value.split(separator)]
    # Suppression des éléments vides
    items = [item for item in items if item]
    
    return items

def normalize_age_range(value):
    """
    Normalise une plage d'âge.
    
    Args:
        value (str): Plage d'âge à normaliser
        
    Returns:
        dict: Plage d'âge normalisée
    """
    if not value or not isinstance(value, str):
        return {"min": None, "max": None}
    
    # Recherche des valeurs numériques
    numbers = re.findall(r'\d+', value)
    
    # Détermination des âges minimum et maximum
    min_age = None
    max_age = None
    
    if "+" in value and numbers:
        # Format "65+ years"
        min_age = int(numbers[0])
    elif "-" in value and len(numbers) >= 2:
        # Format "18-64 years"
        min_age = int(numbers[0])
        max_age = int(numbers[1])
    
    return {"min": min_age, "max": max_age}

def normalize_country(value):
    """
    Normalise un nom de pays.
    
    Args:
        value (str): Nom de pays à normaliser
        
    Returns:
        str: Nom de pays normalisé
    """
    if not value or not isinstance(value, str):
        return value
    
    # Suppression des espaces en début et fin
    value = value.strip()
    
    # Normalisation des noms de pays courants
    country_mapping = {
        "united states": "United States",
        "usa": "United States",
        "united states of america": "United States",
        "uk": "United Kingdom",
        "great britain": "United Kingdom",
        "england": "United Kingdom",
        "united kingdom": "United Kingdom",
        "france": "France",
        "germany": "Germany",
        "spain": "Spain",
        "italy": "Italy",
        "belgium": "Belgium",
        "netherlands": "Netherlands",
        "the netherlands": "Netherlands",
        "switzerland": "Switzerland",
        "sweden": "Sweden",
        "denmark": "Denmark",
        "norway": "Norway",
        "finland": "Finland",
        "austria": "Austria",
        "portugal": "Portugal",
        "greece": "Greece",
        "ireland": "Ireland",
        "poland": "Poland",
        "czech republic": "Czech Republic",
        "hungary": "Hungary",
        "romania": "Romania",
        "bulgaria": "Bulgaria",
        "croatia": "Croatia",
        "slovenia": "Slovenia",
        "slovakia": "Slovakia",
        "estonia": "Estonia",
        "latvia": "Latvia",
        "lithuania": "Lithuania",
        "cyprus": "Cyprus",
        "malta": "Malta",
        "luxembourg": "Luxembourg",
        "iceland": "Iceland",
        "liechtenstein": "Liechtenstein"
    }
    
    return country_mapping.get(value.lower(), value)

def normalize_trial_phase(value):
    """
    Normalise une phase d'essai clinique.
    
    Args:
        value (str): Phase d'essai à normaliser
        
    Returns:
        str: Phase d'essai normalisée
    """
    if not value or not isinstance(value, str):
        return value
    
    # Suppression des espaces en début et fin
    value = value.strip()
    
    # Extraction de la phase
    phase_match = re.search(r'Phase\s+([IViv]+)', value, re.IGNORECASE)
    if phase_match:
        phase = phase_match.group(1).upper()
        return f"Phase {phase}"
    
    # Normalisation des phases courantes
    phase_mapping = {
        "therapeutic exploratory": "Phase II",
        "therapeutic confirmatory": "Phase III",
        "first in human": "Phase I",
        "human pharmacology": "Phase I",
        "bioequivalence study": "Phase I"
    }
    
    for key, normalized_phase in phase_mapping.items():
        if key.lower() in value.lower():
            return normalized_phase
    
    return value

def normalize_data(data):
    """
    Normalise l'ensemble des données extraites.
    
    Args:
        data (dict): Données à normaliser
        
    Returns:
        dict: Données normalisées
    """
    if not isinstance(data, dict):
        return data
        
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = normalize_data(value)
        elif isinstance(value, list):
            result[key] = [normalize_data(item) if isinstance(item, dict) else item for item in value]
        elif isinstance(value, str):
            # Normalisation selon le type de champ
            if 'date' in key.lower():
                result[key] = normalize_date(value)
            elif key.lower() in ['transition_trial', 'early_termination']:
                result[key] = normalize_boolean(value)
            elif 'age_range' in key.lower():
                result[key] = normalize_age_range(value)
            elif 'country' in key.lower() and not isinstance(value, dict):
                result[key] = normalize_country(value)
            elif 'trial_phase' in key.lower():
                result[key] = normalize_trial_phase(value)
            elif 'number' in key.lower():
                result[key] = normalize_number(value)
            elif 'locations' in key.lower() and ',' in value:
                result[key] = normalize_list(value)
            else:
                result[key] = normalize_string(value)
        else:
            result[key] = value
            
    return result