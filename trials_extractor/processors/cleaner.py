"""
Module pour le nettoyage des données extraites.
"""

import logging
import re

logger = logging.getLogger(__name__)

def clean_text(text):
    """
    Nettoie un texte (espaces, caractères spéciaux).
    
    Args:
        text (str): Texte à nettoyer
        
    Returns:
        str: Texte nettoyé
    """
    if not text:
        return text
        
    # Suppression des espaces multiples
    cleaned = re.sub(r'\s+', ' ', text)
    # Suppression des espaces en début et fin
    cleaned = cleaned.strip()
    # Remplacement des caractères spéciaux problématiques
    cleaned = cleaned.replace('\u00A0', ' ')  # Espace insécable
    cleaned = cleaned.replace('\u2019', "'")  # Apostrophe typographique
    cleaned = cleaned.replace('\u2013', '-')  # Tiret demi-cadratin
    cleaned = cleaned.replace('\u2014', '-')  # Tiret cadratin
    cleaned = cleaned.replace('\u201C', '"')  # Guillemet ouvrant
    cleaned = cleaned.replace('\u201D', '"')  # Guillemet fermant
    
    return cleaned

def handle_missing_values(data, default_value=None):
    """
    Gère les valeurs manquantes dans un dictionnaire.
    
    Args:
        data (dict): Dictionnaire à traiter
        default_value: Valeur par défaut pour les champs manquants
        
    Returns:
        dict: Dictionnaire avec les valeurs manquantes traitées
    """
    if not isinstance(data, dict):
        return data
        
    result = {}
    for key, value in data.items():
        if value is None:
            result[key] = default_value
        elif isinstance(value, dict):
            result[key] = handle_missing_values(value, default_value)
        elif isinstance(value, list):
            result[key] = [handle_missing_values(item, default_value) if isinstance(item, dict) else item for item in value]
        else:
            result[key] = value
            
    return result

def clean_data(data):
    """
    Nettoie l'ensemble des données extraites.
    
    Args:
        data (dict): Données à nettoyer
        
    Returns:
        dict: Données nettoyées
    """
    if not isinstance(data, dict):
        return data
        
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = clean_text(value)
        elif isinstance(value, dict):
            result[key] = clean_data(value)
        elif isinstance(value, list):
            result[key] = [clean_data(item) if isinstance(item, dict) else 
                          clean_text(item) if isinstance(item, str) else item 
                          for item in value]
        else:
            result[key] = value
            
    return result

def remove_empty_values(data, remove_empty_lists=True, remove_empty_dicts=True):
    """
    Supprime les valeurs vides d'un dictionnaire.
    
    Args:
        data (dict): Dictionnaire à traiter
        remove_empty_lists (bool): Supprimer les listes vides
        remove_empty_dicts (bool): Supprimer les dictionnaires vides
        
    Returns:
        dict: Dictionnaire sans les valeurs vides
    """
    if not isinstance(data, dict):
        return data
        
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            cleaned_dict = remove_empty_values(value, remove_empty_lists, remove_empty_dicts)
            if cleaned_dict or not remove_empty_dicts:
                result[key] = cleaned_dict
        elif isinstance(value, list):
            cleaned_list = [
                remove_empty_values(item, remove_empty_lists, remove_empty_dicts) 
                if isinstance(item, dict) else item 
                for item in value 
                if item or not isinstance(item, (str, dict, list))
            ]
            if cleaned_list or not remove_empty_lists:
                result[key] = cleaned_list
        elif value or not isinstance(value, str):
            result[key] = value
            
    return result

def standardize_keys(data):
    """
    Standardise les clés d'un dictionnaire (minuscules, underscores).
    
    Args:
        data (dict): Dictionnaire à traiter
        
    Returns:
        dict: Dictionnaire avec des clés standardisées
    """
    if not isinstance(data, dict):
        return data
        
    result = {}
    for key, value in data.items():
        # Conversion de la clé en minuscules et remplacement des espaces par des underscores
        new_key = key.lower().replace(' ', '_').replace('-', '_')
        
        # Traitement récursif des valeurs
        if isinstance(value, dict):
            result[new_key] = standardize_keys(value)
        elif isinstance(value, list):
            result[new_key] = [standardize_keys(item) if isinstance(item, dict) else item for item in value]
        else:
            result[new_key] = value
            
    return result

def clean_and_standardize(data):
    """
    Nettoie et standardise les données extraites.
    
    Args:
        data (dict): Données à traiter
        
    Returns:
        dict: Données nettoyées et standardisées
    """
    # Nettoyage des textes
    cleaned_data = clean_data(data)
    
    # Gestion des valeurs manquantes
    cleaned_data = handle_missing_values(cleaned_data, default_value="")
    
    # Suppression des valeurs vides
    cleaned_data = remove_empty_values(cleaned_data)
    
    # Standardisation des clés
    standardized_data = standardize_keys(cleaned_data)
    
    return standardized_data