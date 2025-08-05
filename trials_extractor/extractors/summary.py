"""
Module pour l'extraction des informations de la section Summary de l'essai clinique.
"""

import logging
import re
from bs4 import Tag
from clinical_trials_extractor.extractors.base import BaseExtractor
from clinical_trials_extractor.config.selectors import SUMMARY_SELECTORS
from clinical_trials_extractor.utils.html_utils import extract_text, extract_table

logger = logging.getLogger(__name__)

class SummaryExtractor(BaseExtractor):
    """
    Extracteur pour les informations de la section Summary de l'essai clinique.
    """
    
    def extract(self):
        """
        Extrait les informations de la section Summary.
        
        Returns:
            dict: Dictionnaire contenant les informations de la section Summary
        """
        logger.info("Extraction des informations de la section Summary")
        
        # Récupération de la section Summary
        summary_section = self.extract_section("summary")
        if not summary_section:
            logger.error("Section Summary non trouvée")
            return {}
        
        # Extraction des différentes sous-sections
        trial_info = self.extract_trial_information(summary_section)
        
        self.data = {
            "trial_information": trial_info,  # Cela correspond à summary.trial_information dans le validateur
            "overall_trial_status": self.extract_overall_trial_status(summary_section),
            "trial_notifications": self.extract_trial_notifications(summary_section),
            "recruitment_notifications": self.extract_recruitment_notifications(summary_section),
            "trial_duration": self.extract_trial_duration(summary_section),
            "applications": self.extract_applications(summary_section)
        }
        
        logger.debug("Informations de la section Summary extraites")
        return self.data
    
    def extract_trial_information(self, summary_section):
        """
        Extrait les informations générales de l'essai.
        
        Args:
            summary_section (Tag): Section Summary
            
        Returns:
            dict: Informations générales de l'essai
        """
        logger.debug("Extraction des informations générales de l'essai")
        
        # Récupération de la sous-section
        selectors = SUMMARY_SELECTORS["trial_information"]
        section = summary_section.select_one(selectors["section"])
        if not section:
            logger.warning("Sous-section Trial Information non trouvée")
            return {}
        
        # Extraction des champs
        trial_info = {
            "medical_condition": self.extract_with_selector(section, selectors["medical_condition"]),
            "trial_phase": self.extract_with_selector(section, selectors["trial_phase"]),
            "transition_trial": self.extract_with_selector(section, selectors["transition_trial"]),
            "sponsor": self.extract_with_selector(section, selectors["sponsor"]),
            "participants_type": self.extract_with_selector(section, selectors["participants_type"]),
            "age_range": self.extract_with_selector(section, selectors["age_range"]),
            "main_objective": self.extract_with_selector(section, selectors["main_objective"])
        }
        
        # Traitement spécial pour les locations (liste séparée par des virgules)
        locations_text = self.extract_with_selector(section, selectors["locations"])
        if locations_text:
            trial_info["locations"] = [loc.strip() for loc in locations_text.split(",")]
        else:
            trial_info["locations"] = []
        
        return trial_info
    
    def extract_overall_trial_status(self, summary_section):
        """
        Extrait les informations sur le statut global de l'essai.
        
        Args:
            summary_section (Tag): Section Summary
            
        Returns:
            dict: Informations sur le statut global de l'essai
        """
        logger.debug("Extraction des informations sur le statut global de l'essai")
        
        # Récupération de la sous-section
        selectors = SUMMARY_SELECTORS["overall_trial_status"]
        section = summary_section.select_one(selectors["section"])
        if not section:
            logger.warning("Sous-section Overall Trial Status non trouvée")
            return {}
        
        # Extraction des champs simples
        status_info = {
            "status": self.extract_with_selector(section, selectors["status"]),
            "start_date": self.extract_with_selector(section, selectors["start_date"]),
            "end_date": self.extract_with_selector(section, selectors["end_date"]),
            "global_end_date": self.extract_with_selector(section, selectors["global_end_date"])
        }
        
        # Extraction du tableau de statut par pays
        status_table = section.select_one(selectors["application_trial_status"])
        if status_table:
            status_info["application_trial_status"] = extract_table(status_table)
        else:
            status_info["application_trial_status"] = []
        
        return status_info
    
    def extract_trial_notifications(self, summary_section):
        """
        Extrait les notifications d'essai par pays.
        
        Args:
            summary_section (Tag): Section Summary
            
        Returns:
            dict: Notifications d'essai par pays
        """
        logger.debug("Extraction des notifications d'essai par pays")
        
        # Récupération de la sous-section
        selectors = SUMMARY_SELECTORS["trial_notifications"]
        section = summary_section.select_one(selectors["section"])
        if not section:
            logger.warning("Sous-section Trial Notifications non trouvée")
            return {}
        
        # Extraction des données par pays
        countries_data = {}
        countries = section.select(selectors["countries"])
        
        for country in countries:
            # Extraction du nom du pays à partir du titre de la sous-section
            country_title = extract_text(country)
            match = re.search(r'\d+\.\d+\.\d+\s+(.+)', country_title)
            if match:
                country_name = match.group(1).strip()
                
                # Récupération des données pour ce pays
                country_section = country.find_next("div", class_="content")
                if country_section:
                    countries_data[country_name] = {
                        "start_trial": self.extract_with_selector(country_section, selectors["start_trial"]),
                        "restart_trial": self.extract_with_selector(country_section, selectors["restart_trial"]),
                        "end_trial": self.extract_with_selector(country_section, selectors["end_trial"]),
                        "early_termination": self.extract_with_selector(country_section, selectors["early_termination"]),
                        "termination_reason": self.extract_with_selector(country_section, selectors["termination_reason"])
                    }
        
        return {"countries": countries_data}
    
    def extract_recruitment_notifications(self, summary_section):
        """
        Extrait les notifications de recrutement par pays.
        
        Args:
            summary_section (Tag): Section Summary
            
        Returns:
            dict: Notifications de recrutement par pays
        """
        logger.debug("Extraction des notifications de recrutement par pays")
        
        # Récupération de la sous-section
        selectors = SUMMARY_SELECTORS["recruitment_notifications"]
        section = summary_section.select_one(selectors["section"])
        if not section:
            logger.warning("Sous-section Recruitment Notifications non trouvée")
            return {}
        
        # Extraction des données par pays
        countries_data = {}
        countries = section.select(selectors["countries"])
        
        for country in countries:
            # Extraction du nom du pays à partir du titre de la sous-section
            country_title = extract_text(country)
            match = re.search(r'\d+\.\d+\.\d+\s+(.+)', country_title)
            if match:
                country_name = match.group(1).strip()
                
                # Récupération des données pour ce pays
                country_section = country.find_next("div", class_="content")
                if country_section:
                    countries_data[country_name] = {
                        "start_recruitment": self.extract_with_selector(country_section, selectors["start_recruitment"]),
                        "restart_recruitment": self.extract_with_selector(country_section, selectors["restart_recruitment"]),
                        "end_recruitment": self.extract_with_selector(country_section, selectors["end_recruitment"])
                    }
        
        return {"countries": countries_data}
    
    def extract_trial_duration(self, summary_section):
        """
        Extrait les informations sur la durée de l'essai.
        
        Args:
            summary_section (Tag): Section Summary
            
        Returns:
            dict: Informations sur la durée de l'essai
        """
        logger.debug("Extraction des informations sur la durée de l'essai")
        
        # Récupération de la sous-section
        selectors = SUMMARY_SELECTORS["trial_duration"]
        section = summary_section.select_one(selectors["section"])
        if not section:
            logger.warning("Sous-section Trial Duration non trouvée")
            return {}
        
        # Extraction des champs
        duration_info = {
            "estimated_recruitment_start": self.extract_with_selector(section, selectors["estimated_recruitment_start"]),
            "estimated_end_date": self.extract_with_selector(section, selectors["estimated_end_date"]),
            "estimated_global_end_date": self.extract_with_selector(section, selectors["estimated_global_end_date"])
        }
        
        return duration_info
    
    def extract_applications(self, summary_section):
        """
        Extrait les informations sur les demandes et décisions.
        
        Args:
            summary_section (Tag): Section Summary
            
        Returns:
            list: Liste des demandes et décisions
        """
        logger.debug("Extraction des informations sur les demandes et décisions")
        
        # Récupération de la sous-section
        selectors = SUMMARY_SELECTORS["applications"]
        section = summary_section.select_one(selectors["section"])
        if not section:
            logger.warning("Sous-section Applications non trouvée")
            return []
        
        # Extraction des applications
        applications = []
        app_sections = section.select(selectors["applications"])
        
        for app_section in app_sections:
            # Extraction du titre de l'application
            app_title = extract_text(app_section)
            
            # Récupération des données pour cette application
            app_content = app_section.find_next("div", class_="content")
            if app_content:
                application = {
                    "title": app_title,
                    "type": self.extract_with_selector(app_content, selectors["application_type"]),
                    "submission_date": self.extract_with_selector(app_content, selectors["submission_date"])
                }
                
                # Extraction de l'évaluation Part I
                part1_section = app_content.select_one(selectors["assessment_part1"]["section"])
                if part1_section:
                    application["assessment_part1"] = {
                        "reference_member_state": self.extract_with_selector(app_content, selectors["assessment_part1"]["reference_member_state"]),
                        "conclusion": self.extract_with_selector(app_content, selectors["assessment_part1"]["conclusion"]),
                        "reporting_date": self.extract_with_selector(app_content, selectors["assessment_part1"]["reporting_date"])
                    }
                
                # Extraction de l'évaluation Part II
                part2_table = app_content.select_one(selectors["assessment_part2"]["table"])
                if part2_table:
                    application["assessment_part2"] = extract_table(part2_table)
                
                # Extraction des décisions
                decision_table = app_content.select_one(selectors["decision"]["table"])
                if decision_table:
                    application["decisions"] = extract_table(decision_table)
                
                applications.append(application)
        
        return applications

def extract_summary(soup):
    """
    Fonction utilitaire pour extraire les informations de la section Summary.
    
    Args:
        soup (BeautifulSoup): Objet BeautifulSoup représentant le document HTML
        
    Returns:
        dict: Dictionnaire contenant les informations de la section Summary
    """
    extractor = SummaryExtractor(soup)
    return extractor.extract()