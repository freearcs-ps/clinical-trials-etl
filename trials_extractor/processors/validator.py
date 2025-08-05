"""
Module pour la validation des données extraites.
"""

import logging
import json
import os
from datetime import datetime
from clinical_trials_extractor.config.settings import VALIDATION
from clinical_trials_extractor.utils.date_utils import is_date_valid

logger = logging.getLogger(__name__)

def load_schema(schema_name):
    """
    Charge un schéma JSON de validation.
    
    Args:
        schema_name (str): Nom du schéma à charger
        
    Returns:
        dict: Schéma JSON, ou None si le chargement échoue
    """
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'schemas', f"{schema_name}.json")
    try:
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning(f"Schéma {schema_name} non trouvé à {schema_path}")
            return None
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Erreur lors du chargement du schéma {schema_name}: {str(e)}")
        return None

def validate_required_sections(data):
    """
    Vérifie la présence des sections requises.
    
    Args:
        data (dict): Données à valider
        
    Returns:
        list: Liste des problèmes détectés
    """
    issues = []
    
    # Vérification des sections principales
    for section in VALIDATION["required_sections"]:
        if section not in data:
            issues.append(f"Section requise manquante: {section}")
    
    # Vérification des champs requis dans chaque section
    for field_path, required_fields in VALIDATION.get("required_fields", {}).items():
        # Séparation du chemin en parties
        path_parts = field_path.split('.')
        
        # Navigation dans la structure de données
        current_data = data
        valid_path = True
        
        for part in path_parts:
            if part in current_data:
                current_data = current_data[part]
            else:
                valid_path = False
                issues.append(f"Chemin invalide pour les champs requis: {field_path}")
                break
        
        # Vérification des champs requis
        if valid_path:
            for field in required_fields:
                if field not in current_data:
                    issues.append(f"Champ requis manquant: {field_path}.{field}")
    
    return issues

def validate_dates(data):
    """
    Vérifie la cohérence des dates.
    
    Args:
        data (dict): Données à valider
        
    Returns:
        list: Liste des problèmes détectés
    """
    issues = []
    
    # Vérification des dates de l'essai
    if "summary" in data and "trial_duration" in data["summary"]:
        trial_duration = data["summary"]["trial_duration"]
        
        # Vérification de la cohérence des dates de début et de fin
        start_date = trial_duration.get("estimated_recruitment_start")
        end_date = trial_duration.get("estimated_end_date")
        
        if start_date and end_date and is_date_valid(start_date) and is_date_valid(end_date):
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            if start_dt > end_dt:
                issues.append(f"Dates incohérentes: la date de début de recrutement ({start_date}) est postérieure à la date de fin ({end_date})")
    
    return issues

def validate_consistency(data):
    """
    Vérifie la cohérence globale des données.
    
    Args:
        data (dict): Données à valider
        
    Returns:
        list: Liste des problèmes détectés
    """
    issues = []
    
    # Vérification de la cohérence entre l'en-tête et les détails de l'essai
    if "header" in data and "trial_information" in data:
        header = data["header"]
        trial_info = data["trial_information"]
        
        # Vérification du numéro EUCT
        if "trial_details" in trial_info and "trial_identifiers" in trial_info["trial_details"]:
            identifiers = trial_info["trial_details"]["trial_identifiers"]
            
            if "euct_number" in header and "eu_trial_number" in identifiers:
                if header["euct_number"] != identifiers["eu_trial_number"]:
                    issues.append(f"Incohérence: numéro EUCT différent entre l'en-tête ({header['euct_number']}) et les détails ({identifiers['eu_trial_number']})")
            
            # Vérification du code de protocole
            if "protocol_code" in header and "protocol_code" in identifiers:
                if header["protocol_code"] != identifiers["protocol_code"]:
                    issues.append(f"Incohérence: code de protocole différent entre l'en-tête ({header['protocol_code']}) et les détails ({identifiers['protocol_code']})")
    
    # Vérification de la cohérence entre les pays listés et les sections détaillées
    if "summary" in data and "trial_information" in data["summary"] and "locations" in data["summary"]["trial_information"]:
        summary_locations = data["summary"]["trial_information"]["locations"]
        
        if "locations" in data and "countries" in data["locations"]:
            location_countries = [country["country"] for country in data["locations"]["countries"]]
            
            # Vérification que tous les pays listés dans le résumé sont présents dans les détails
            for country in summary_locations:
                if country not in location_countries:
                    issues.append(f"Incohérence: pays {country} mentionné dans le résumé mais absent des détails de localisation")
    
    return issues

def validate_data(data, schema_name="clinical_trial"):
    """
    Valide les données par rapport à un schéma et des règles de cohérence.
    
    Args:
        data (dict): Données à valider
        schema_name (str): Nom du schéma à utiliser
        
    Returns:
        dict: Résultat de la validation avec les clés 'valid' et 'issues'
    """
    issues = []
    valid = True
    
    # Validation par rapport au schéma JSON
    schema = load_schema(schema_name)
    if schema:
        try:
            # Ici, on pourrait utiliser jsonschema pour valider les données
            # jsonschema.validate(data, schema)
            # Mais pour simplifier, nous utilisons nos propres validations
            pass
        except Exception as e:
            valid = False
            issues.append(f"Erreur de validation par rapport au schéma: {str(e)}")
    
    # Validation des sections requises
    section_issues = validate_required_sections(data)
    if section_issues:
        valid = False
        issues.extend(section_issues)
    
    # Validation des dates
    date_issues = validate_dates(data)
    if date_issues:
        valid = False
        issues.extend(date_issues)
    
    # Validation de la cohérence
    consistency_issues = validate_consistency(data)
    if consistency_issues:
        valid = False
        issues.extend(consistency_issues)
    
    return {"valid": valid, "issues": issues}

def validate_and_report(data):
    """
    Valide les données et génère un rapport de validation.
    
    Args:
        data (dict): Données à valider
        
    Returns:
        tuple: (bool, list) - Validité des données et liste des problèmes
    """
    validation_result = validate_data(data)
    
    if validation_result["valid"]:
        logger.info("Validation réussie: les données sont valides")
    else:
        logger.warning(f"Validation échouée: {len(validation_result['issues'])} problèmes détectés")
        for issue in validation_result["issues"]:
            logger.warning(f"  - {issue}")
    
    return validation_result["valid"], validation_result["issues"]