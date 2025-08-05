"""
Module pour l'exportation des données au format JSON.
"""

import json
import logging
import os
from clinical_trials_extractor.config.settings import JSON_SETTINGS

logger = logging.getLogger(__name__)

def export_to_json(data, output_path, indent=None):
    """
    Exporte les données au format JSON.
    
    Args:
        data (dict): Données à exporter
        output_path (str): Chemin du fichier de sortie
        indent (int): Nombre d'espaces pour l'indentation (None pour utiliser la valeur par défaut)
        
    Returns:
        bool: True si l'export a réussi, False sinon
    """
    try:
        # Création du répertoire parent si nécessaire
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Configuration de l'indentation
        indent_value = indent if indent is not None else JSON_SETTINGS["indent"]
        
        # Export des données
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=JSON_SETTINGS["ensure_ascii"], indent=indent_value)
            
        logger.info(f"Données exportées au format JSON: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'export au format JSON: {str(e)}")
        return False

def format_json(data, indent=None):
    """
    Formate les données pour l'export JSON.
    
    Args:
        data (dict): Données à formater
        indent (int): Nombre d'espaces pour l'indentation (None pour utiliser la valeur par défaut)
        
    Returns:
        str: Chaîne JSON formatée
    """
    try:
        # Configuration de l'indentation
        indent_value = indent if indent is not None else JSON_SETTINGS["indent"]
        
        # Formatage des données
        return json.dumps(data, ensure_ascii=JSON_SETTINGS["ensure_ascii"], indent=indent_value)
    except Exception as e:
        logger.error(f"Erreur lors du formatage JSON: {str(e)}")
        return "{}"

def export_sections_to_json(data, output_dir, sections=None):
    """
    Exporte les sections spécifiées au format JSON.
    
    Args:
        data (dict): Données à exporter
        output_dir (str): Répertoire de sortie
        sections (list): Liste des sections à exporter (None pour toutes les sections)
        
    Returns:
        dict: Dictionnaire des résultats d'export par section
    """
    # Création du répertoire de sortie
    os.makedirs(output_dir, exist_ok=True)
    
    # Détermination des sections à exporter
    if sections is None:
        sections = data.keys()
    else:
        sections = [section for section in sections if section in data]
    
    # Export de chaque section
    results = {}
    for section in sections:
        section_data = data.get(section, {})
        output_path = os.path.join(output_dir, f"{section}.json")
        success = export_to_json(section_data, output_path)
        results[section] = {
            "success": success,
            "path": output_path
        }
    
    # Export du fichier complet
    output_path = os.path.join(output_dir, "clinical_trial.json")
    success = export_to_json(data, output_path)
    results["complete"] = {
        "success": success,
        "path": output_path
    }
    
    return results

def export_to_jsonl(data_list, output_path):
    """
    Exporte une liste de données au format JSONL (JSON Lines).
    
    Args:
        data_list (list): Liste de dictionnaires à exporter
        output_path (str): Chemin du fichier de sortie
        
    Returns:
        bool: True si l'export a réussi, False sinon
    """
    try:
        # Création du répertoire parent si nécessaire
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Export des données
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in data_list:
                f.write(json.dumps(item, ensure_ascii=JSON_SETTINGS["ensure_ascii"]) + '\n')
            
        logger.info(f"Données exportées au format JSONL: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'export au format JSONL: {str(e)}")
        return False