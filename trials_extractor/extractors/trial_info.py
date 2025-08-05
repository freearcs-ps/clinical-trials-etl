"""
Module pour l'extraction des informations de la section Trial Information de l'essai clinique.
"""

import logging
import re
from bs4 import Tag
from clinical_trials_extractor.extractors.base import BaseExtractor
from clinical_trials_extractor.config.selectors import TRIAL_INFO_SELECTORS
from clinical_trials_extractor.utils.html_utils import extract_text, extract_table

logger = logging.getLogger(__name__)

class TrialInfoExtractor(BaseExtractor):
    """
    Extracteur pour les informations de la section Trial Information de l'essai clinique.
    """
    
    def extract(self):
        """
        Extrait les informations de la section Trial Information.
        
        Returns:
            dict: Dictionnaire contenant les informations de la section Trial Information
        """
        logger.info("Extraction des informations de la section Trial Information")
        
        # Récupération de la section Trial Information
        trial_info_section = self.extract_section("full_trial_info")
        if not trial_info_section:
            logger.error("Section Trial Information non trouvée")
            return {}
        
        # Extraction des différentes sous-sections
        self.data = {
            "trial_details": self.extract_trial_details(trial_info_section),
            "products": self.extract_products(trial_info_section)
        }
        
        logger.debug("Informations de la section Trial Information extraites")
        return self.data
    
    def extract_trial_details(self, trial_info_section):
        """
        Extrait les détails de l'essai.
        
        Args:
            trial_info_section (Tag): Section Trial Information
            
        Returns:
            dict: Détails de l'essai
        """
        logger.debug("Extraction des détails de l'essai")
        
        # Récupération de la sous-section
        selectors = TRIAL_INFO_SELECTORS["trial_details"]
        section = trial_info_section.select_one(selectors["section"])
        if not section:
            logger.warning("Sous-section Trial Details non trouvée")
            return {}
        
        # Extraction des identifiants de l'essai
        trial_identifiers = self.extract_trial_identifiers(section)
        
        # Extraction des informations de l'essai
        trial_information = self.extract_trial_information_details(section)
        
        # Extraction des critères d'inclusion
        inclusion_criteria = self.extract_inclusion_criteria(section)
        
        # Extraction des critères d'exclusion
        exclusion_criteria = self.extract_exclusion_criteria(section)
        
        # Extraction des critères d'évaluation primaires
        primary_endpoints = self.extract_primary_endpoints(section)
        
        # Extraction des critères d'évaluation secondaires
        secondary_endpoints = self.extract_secondary_endpoints(section)
        
        # Combinaison des résultats
        return {
            "trial_identifiers": trial_identifiers,
            "trial_information": trial_information,
            "inclusion_criteria": inclusion_criteria,
            "exclusion_criteria": exclusion_criteria,
            "primary_endpoints": primary_endpoints,
            "secondary_endpoints": secondary_endpoints
        }
    
    def extract_trial_identifiers(self, section):
        """
        Extrait les identifiants de l'essai.
        
        Args:
            section (Tag): Section Trial Details
            
        Returns:
            dict: Identifiants de l'essai
        """
        logger.debug("Extraction des identifiants de l'essai")
        
        # Récupération de la sous-section
        selectors = TRIAL_INFO_SELECTORS["trial_details"]["trial_identifiers"]
        identifiers_section = section.select_one(selectors["section"])
        if not identifiers_section:
            logger.warning("Sous-section Trial Identifiers non trouvée")
            return {}
        
        # Extraction des champs
        identifiers = {
            "eu_trial_number": self.extract_with_selector(section, selectors["eu_trial_number"]),
            "full_title": self.extract_with_selector(section, selectors["full_title"]),
            "public_title": self.extract_with_selector(section, selectors["public_title"]),
            "protocol_code": self.extract_with_selector(section, selectors["protocol_code"])
        }
        
        return identifiers
    
    def extract_trial_information_details(self, section):
        """
        Extrait les informations détaillées de l'essai.
        
        Args:
            section (Tag): Section Trial Details
            
        Returns:
            dict: Informations détaillées de l'essai
        """
        logger.debug("Extraction des informations détaillées de l'essai")
        
        # Récupération de la sous-section
        selectors = TRIAL_INFO_SELECTORS["trial_details"]["trial_information"]
        info_section = section.select_one(selectors["section"])
        if not info_section:
            logger.warning("Sous-section Trial Information Details non trouvée")
            return {}
        
        # Extraction des champs
        info = {
            "trial_phase": self.extract_with_selector(section, selectors["trial_phase"]),
            "medical_condition": self.extract_with_selector(section, selectors["medical_condition"]),
            "therapeutic_area": self.extract_with_selector(section, selectors["therapeutic_area"]),
            "main_objective": self.extract_with_selector(section, selectors["main_objective"])
        }
        
        return info
    
    def extract_inclusion_criteria(self, section):
        """
        Extrait les critères d'inclusion.
        
        Args:
            section (Tag): Section Trial Details
            
        Returns:
            list: Critères d'inclusion
        """
        logger.debug("Extraction des critères d'inclusion")
        
        # Récupération de la sous-section
        selectors = TRIAL_INFO_SELECTORS["trial_details"]["inclusion_criteria"]
        criteria_section = section.select_one(selectors["section"])
        if not criteria_section:
            logger.warning("Sous-section Inclusion Criteria non trouvée")
            return []
        
        # Extraction du tableau
        criteria_table = section.select_one(selectors["table"])
        if not criteria_table:
            logger.warning("Tableau des critères d'inclusion non trouvé")
            return []
        
        # Extraction des critères
        criteria = extract_table(criteria_table)
        
        # Transformation en liste simple
        return [
            {
                "number": item.get("Inclusion criteria number", ""),
                "description": item.get("Principal inclusion criteria (English)", "")
            }
            for item in criteria
        ]
    
    def extract_exclusion_criteria(self, section):
        """
        Extrait les critères d'exclusion.
        
        Args:
            section (Tag): Section Trial Details
            
        Returns:
            list: Critères d'exclusion
        """
        logger.debug("Extraction des critères d'exclusion")
        
        # Récupération de la sous-section
        selectors = TRIAL_INFO_SELECTORS["trial_details"]["exclusion_criteria"]
        criteria_section = section.select_one(selectors["section"])
        if not criteria_section:
            logger.warning("Sous-section Exclusion Criteria non trouvée")
            return []
        
        # Extraction du tableau
        criteria_table = section.select_one(selectors["table"])
        if not criteria_table:
            logger.warning("Tableau des critères d'exclusion non trouvé")
            return []
        
        # Extraction des critères
        criteria = extract_table(criteria_table)
        
        # Transformation en liste simple
        return [
            {
                "number": item.get("Exclusion criteria number", ""),
                "description": item.get("Principal exclusion criteria (English)", "")
            }
            for item in criteria
        ]
    
    def extract_primary_endpoints(self, section):
        """
        Extrait les critères d'évaluation primaires.
        
        Args:
            section (Tag): Section Trial Details
            
        Returns:
            list: Critères d'évaluation primaires
        """
        logger.debug("Extraction des critères d'évaluation primaires")
        
        # Récupération de la sous-section
        selectors = TRIAL_INFO_SELECTORS["trial_details"]["primary_endpoints"]
        endpoints_section = section.select_one(selectors["section"])
        if not endpoints_section:
            logger.warning("Sous-section Primary Endpoints non trouvée")
            return []
        
        # Extraction du tableau
        endpoints_table = section.select_one(selectors["table"])
        if not endpoints_table:
            logger.warning("Tableau des critères d'évaluation primaires non trouvé")
            return []
        
        # Extraction des critères
        endpoints = extract_table(endpoints_table)
        
        # Transformation en liste simple
        return [
            {
                "number": item.get("End point criteria number", ""),
                "description": item.get("Primary end point (English)", "")
            }
            for item in endpoints
        ]
    
    def extract_secondary_endpoints(self, section):
        """
        Extrait les critères d'évaluation secondaires.
        
        Args:
            section (Tag): Section Trial Details
            
        Returns:
            list: Critères d'évaluation secondaires
        """
        logger.debug("Extraction des critères d'évaluation secondaires")
        
        # Récupération de la sous-section
        selectors = TRIAL_INFO_SELECTORS["trial_details"]["secondary_endpoints"]
        endpoints_section = section.select_one(selectors["section"])
        if not endpoints_section:
            logger.warning("Sous-section Secondary Endpoints non trouvée")
            return []
        
        # Extraction du tableau
        endpoints_table = section.select_one(selectors["table"])
        if not endpoints_table:
            logger.warning("Tableau des critères d'évaluation secondaires non trouvé")
            return []
        
        # Extraction des critères
        endpoints = extract_table(endpoints_table)
        
        # Transformation en liste simple
        return [
            {
                "number": item.get("Secondary end point number", ""),
                "description": item.get("Secondary end point (English)", "")
            }
            for item in endpoints
        ]
    
    def extract_products(self, trial_info_section):
        """
        Extrait les informations sur les produits utilisés dans l'essai.
        
        Args:
            trial_info_section (Tag): Section Trial Information
            
        Returns:
            list: Liste des produits
        """
        logger.debug("Extraction des informations sur les produits")
        
        # Récupération de la sous-section
        selectors = TRIAL_INFO_SELECTORS["products"]
        section = trial_info_section.select_one(selectors["section"])
        if not section:
            logger.warning("Sous-section Products non trouvée")
            return []
        
        # Extraction des sections de produits
        product_sections = section.select(selectors["product_sections"])
        products = []
        
        for product_section in product_sections:
            # Extraction du titre du produit
            product_title = extract_text(product_section)
            
            # Récupération des données pour ce produit
            product_content = product_section.find_next("div", class_="content")
            if product_content:
                product = {
                    "title": product_title,
                    "details": self.extract_product_details(product_content, selectors["product_details"]),
                    "characteristics": self.extract_product_characteristics(product_content, selectors["product_characteristics"]),
                    "dosage": self.extract_product_dosage(product_content, selectors["dosage"]),
                    "active_substance": self.extract_active_substance(product_content, selectors["active_substance"])
                }
                products.append(product)
        
        return products
    
    def extract_product_details(self, product_content, selectors):
        """
        Extrait les détails d'un produit.
        
        Args:
            product_content (Tag): Contenu du produit
            selectors (dict): Sélecteurs pour les détails du produit
            
        Returns:
            dict: Détails du produit
        """
        return {
            "name": self.extract_with_selector(product_content, selectors["name"]),
            "id": self.extract_with_selector(product_content, selectors["id"]),
            "form": self.extract_with_selector(product_content, selectors["form"]),
            "role": self.extract_with_selector(product_content, selectors["role"])
        }
    
    def extract_product_characteristics(self, product_content, selectors):
        """
        Extrait les caractéristiques d'un produit.
        
        Args:
            product_content (Tag): Contenu du produit
            selectors (dict): Sélecteurs pour les caractéristiques du produit
            
        Returns:
            dict: Caractéristiques du produit
        """
        return {
            "characteristics": self.extract_with_selector(product_content, selectors["characteristics"])
        }
    
    def extract_product_dosage(self, product_content, selectors):
        """
        Extrait les informations de dosage d'un produit.
        
        Args:
            product_content (Tag): Contenu du produit
            selectors (dict): Sélecteurs pour le dosage du produit
            
        Returns:
            dict: Informations de dosage du produit
        """
        return {
            "route": self.extract_with_selector(product_content, selectors["route"]),
            "duration": self.extract_with_selector(product_content, selectors["duration"]),
            "daily_dose": self.extract_with_selector(product_content, selectors["daily_dose"]),
            "total_dose": self.extract_with_selector(product_content, selectors["total_dose"])
        }
    
    def extract_active_substance(self, product_content, selectors):
        """
        Extrait les informations sur la substance active d'un produit.
        
        Args:
            product_content (Tag): Contenu du produit
            selectors (dict): Sélecteurs pour la substance active
            
        Returns:
            dict: Informations sur la substance active
        """
        return {
            "name": self.extract_with_selector(product_content, selectors["name"]),
            "code": self.extract_with_selector(product_content, selectors["code"])
        }

def extract_trial_info(soup):
    """
    Fonction utilitaire pour extraire les informations de la section Trial Information.
    
    Args:
        soup (BeautifulSoup): Objet BeautifulSoup représentant le document HTML
        
    Returns:
        dict: Dictionnaire contenant les informations de la section Trial Information
    """
    extractor = TrialInfoExtractor(soup)
    return extractor.extract()