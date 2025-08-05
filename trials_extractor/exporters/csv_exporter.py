"""
Module pour l'exportation des données au format CSV.
"""

import csv
import logging
import os
import pandas as pd
from clinical_trials_extractor.config.settings import CSV_SETTINGS

logger = logging.getLogger(__name__)

def export_to_csv(data, output_path, delimiter=None):
    """
    Exporte les données au format CSV.
    
    Args:
        data (list): Liste de dictionnaires à exporter
        output_path (str): Chemin du fichier de sortie
        delimiter (str): Délimiteur à utiliser (None pour utiliser la valeur par défaut)
        
    Returns:
        bool: True si l'export a réussi, False sinon
    """
    try:
        # Création du répertoire parent si nécessaire
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Configuration du délimiteur
        delimiter_value = delimiter if delimiter is not None else CSV_SETTINGS["delimiter"]
        
        # Utilisation de pandas pour l'export
        df = pd.DataFrame(data)
        df.to_csv(
            output_path,
            sep=delimiter_value,
            quotechar=CSV_SETTINGS["quotechar"],
            quoting=CSV_SETTINGS["quoting"],
            index=False,
            encoding=CSV_SETTINGS["encoding"]
        )
        
        logger.info(f"Données exportées au format CSV: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'export au format CSV: {str(e)}")
        return False

def flatten_data(data):
    """
    Transforme les données hiérarchiques en format tabulaire.
    
    Args:
        data (dict): Données hiérarchiques
        
    Returns:
        dict: Dictionnaire contenant les données aplaties par entité
    """
    flat_data = {
        "trials": [],
        "trial_status": [],
        "trial_notifications": [],
        "recruitment": [],
        "applications": [],
        "products": [],
        "locations": [],
        "sponsors": []
    }
    
    # Extraction des données de base de l'essai
    if "header" in data:
        trial = {
            "euct_number": data["header"].get("euct_number"),
            "title": data["header"].get("title"),
            "protocol_code": data["header"].get("protocol_code")
        }
        
        # Ajout des informations du résumé
        if "summary" in data and "trial_information" in data["summary"]:
            trial_info = data["summary"]["trial_information"]
            for key, value in trial_info.items():
                if not isinstance(value, (dict, list)):
                    trial[key] = value
                elif isinstance(value, list) and key == "locations":
                    trial[key] = ", ".join(value)
        
        flat_data["trials"].append(trial)
        
        # Extraction des statuts par pays
        if "summary" in data and "overall_trial_status" in data["summary"]:
            status_info = data["summary"]["overall_trial_status"]
            if "application_trial_status" in status_info:
                for status in status_info["application_trial_status"]:
                    status_entry = {
                        "euct_number": trial["euct_number"],
                        "member_state": status.get("Member State"),
                        "status": status.get("Application Trial Status"),
                        "decision_date": status.get("Decision Date")
                    }
                    flat_data["trial_status"].append(status_entry)
        
        # Extraction des notifications par pays
        if "summary" in data and "trial_notifications" in data["summary"] and "countries" in data["summary"]["trial_notifications"]:
            countries_data = data["summary"]["trial_notifications"]["countries"]
            for country, country_data in countries_data.items():
                notification_entry = {
                    "euct_number": trial["euct_number"],
                    "country": country,
                    "start_trial": country_data.get("start_trial"),
                    "restart_trial": country_data.get("restart_trial"),
                    "end_trial": country_data.get("end_trial"),
                    "early_termination": country_data.get("early_termination"),
                    "termination_reason": country_data.get("termination_reason")
                }
                flat_data["trial_notifications"].append(notification_entry)
        
        # Extraction des informations de recrutement par pays
        if "summary" in data and "recruitment_notifications" in data["summary"] and "countries" in data["summary"]["recruitment_notifications"]:
            countries_data = data["summary"]["recruitment_notifications"]["countries"]
            for country, country_data in countries_data.items():
                recruitment_entry = {
                    "euct_number": trial["euct_number"],
                    "country": country,
                    "start_recruitment": country_data.get("start_recruitment"),
                    "restart_recruitment": country_data.get("restart_recruitment"),
                    "end_recruitment": country_data.get("end_recruitment")
                }
                flat_data["recruitment"].append(recruitment_entry)
        
        # Extraction des demandes et décisions
        if "summary" in data and "applications" in data["summary"]:
            for app in data["summary"]["applications"]:
                app_entry = {
                    "euct_number": trial["euct_number"],
                    "title": app.get("title"),
                    "type": app.get("type"),
                    "submission_date": app.get("submission_date")
                }
                
                # Ajout des informations d'évaluation Part I
                if "assessment_part1" in app:
                    app_entry["reference_member_state"] = app["assessment_part1"].get("reference_member_state")
                    app_entry["part1_conclusion"] = app["assessment_part1"].get("conclusion")
                    app_entry["part1_reporting_date"] = app["assessment_part1"].get("reporting_date")
                
                flat_data["applications"].append(app_entry)
                
                # Extraction des décisions
                if "decisions" in app:
                    for decision in app["decisions"]:
                        decision_entry = {
                            "euct_number": trial["euct_number"],
                            "application_title": app.get("title"),
                            "member_state": decision.get("Member state"),
                            "decision": decision.get("Decision"),
                            "decision_date": decision.get("Decision date"),
                            "decision_type": decision.get("Decision type")
                        }
                        flat_data["applications"].append(decision_entry)
        
        # Extraction des produits
        if "trial_information" in data and "products" in data["trial_information"]:
            for product in data["trial_information"]["products"]:
                product_entry = {
                    "euct_number": trial["euct_number"],
                    "title": product.get("title")
                }
                
                # Ajout des détails du produit
                if "details" in product:
                    for key, value in product["details"].items():
                        product_entry[f"details_{key}"] = value
                
                # Ajout des caractéristiques du produit
                if "characteristics" in product:
                    for key, value in product["characteristics"].items():
                        product_entry[f"characteristics_{key}"] = value
                
                # Ajout des informations de dosage
                if "dosage" in product:
                    for key, value in product["dosage"].items():
                        product_entry[f"dosage_{key}"] = value
                
                # Ajout des informations sur la substance active
                if "active_substance" in product:
                    for key, value in product["active_substance"].items():
                        product_entry[f"active_substance_{key}"] = value
                
                flat_data["products"].append(product_entry)
        
        # Extraction des sites par pays
        if "locations" in data and "countries" in data["locations"]:
            for country in data["locations"]["countries"]:
                country_name = country.get("country")
                country_status = country.get("status")
                planned_subjects = country.get("planned_subjects")
                
                if "sites" in country:
                    for site in country["sites"]:
                        site_entry = {
                            "euct_number": trial["euct_number"],
                            "country": country_name,
                            "country_status": country_status,
                            "planned_subjects": planned_subjects,
                            "site_name": site.get("name"),
                            "site_oms_id": site.get("oms_id"),
                            "site_department": site.get("department"),
                            "site_location": site.get("location"),
                            "site_address": site.get("address"),
                            "site_city": site.get("city"),
                            "site_post_code": site.get("post_code")
                        }
                        
                        # Ajout des informations de contact
                        if "contact" in site:
                            contact = site["contact"]
                            site_entry["contact_first_name"] = contact.get("first_name")
                            site_entry["contact_last_name"] = contact.get("last_name")
                            site_entry["contact_title"] = contact.get("title")
                            site_entry["contact_phone"] = contact.get("phone")
                            site_entry["contact_email"] = contact.get("email")
                        
                        flat_data["locations"].append(site_entry)
        
        # Extraction des sponsors
        if "locations" in data and "sponsors" in data["locations"]:
            sponsors_data = data["locations"]["sponsors"]
            
            sponsor_entry = {
                "euct_number": trial["euct_number"]
            }
            
            # Ajout des détails du sponsor
            if "details" in sponsors_data:
                for key, value in sponsors_data["details"].items():
                    sponsor_entry[f"details_{key}"] = value
            
            # Ajout des informations de contact scientifique
            if "scientific_contact" in sponsors_data:
                for key, value in sponsors_data["scientific_contact"].items():
                    sponsor_entry[f"scientific_contact_{key}"] = value
            
            # Ajout des informations de contact public
            if "public_contact" in sponsors_data:
                for key, value in sponsors_data["public_contact"].items():
                    sponsor_entry[f"public_contact_{key}"] = value
            
            flat_data["sponsors"].append(sponsor_entry)
    
    return flat_data

def export_entity(entity_data, output_path):
    """
    Exporte une entité spécifique en CSV.
    
    Args:
        entity_data (list): Liste de dictionnaires représentant l'entité
        output_path (str): Chemin du fichier de sortie
        
    Returns:
        bool: True si l'export a réussi, False sinon
    """
    if not entity_data:
        logger.warning(f"Aucune donnée à exporter vers {output_path}")
        return False
    
    return export_to_csv(entity_data, output_path)

def export_to_csv_files(data, output_dir, delimiter=None):
    """
    Exporte les données en plusieurs fichiers CSV.
    
    Args:
        data (dict): Données à exporter
        output_dir (str): Répertoire de sortie
        delimiter (str): Délimiteur à utiliser (None pour utiliser la valeur par défaut)
        
    Returns:
        dict: Dictionnaire des résultats d'export par entité
    """
    try:
        # Création du répertoire de sortie
        os.makedirs(output_dir, exist_ok=True)
        
        # Aplatissement des données
        flat_data = flatten_data(data)
        
        # Export de chaque entité
        results = {}
        for entity, entity_data in flat_data.items():
            if entity_data:
                output_path = os.path.join(output_dir, f"{entity}.csv")
                success = export_entity(entity_data, output_path)
                results[entity] = {
                    "success": success,
                    "path": output_path,
                    "count": len(entity_data)
                }
        
        logger.info(f"Données exportées au format CSV: {output_dir}")
        return results
    except Exception as e:
        logger.error(f"Erreur lors de l'export au format CSV: {str(e)}")
        return {"error": str(e)}