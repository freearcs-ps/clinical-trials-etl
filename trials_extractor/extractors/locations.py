"""
Module pour l'extraction des informations de la section Locations and Contact de l'essai clinique.
"""

import logging
import re
from bs4 import Tag
from clinical_trials_extractor.extractors.base import BaseExtractor
from clinical_trials_extractor.config.selectors import LOCATIONS_SELECTORS
from clinical_trials_extractor.utils.html_utils import extract_text, extract_table

logger = logging.getLogger(__name__)

class LocationsExtractor(BaseExtractor):
    """
    Extracteur pour les informations de la section Locations and Contact de l'essai clinique.
    """
    
    def extract(self):
        """
        Extrait les informations de la section Locations and Contact.
        
        Returns:
            dict: Dictionnaire contenant les informations de la section Locations and Contact
        """
        logger.info("Extraction des informations de la section Locations and Contact")
        
        # Récupération de la section Locations and Contact
        locations_section = self.extract_section("locations")
        if not locations_section:
            logger.error("Section Locations and Contact non trouvée")
            return {}
        
        # Extraction des différentes sous-sections
        self.data = {
            "countries": self.extract_countries(locations_section),
            "sponsors": self.extract_sponsors(locations_section)
        }
        
        logger.debug("Informations de la section Locations and Contact extraites")
        return self.data
    
    def extract_countries(self, locations_section):
        """
        Extrait les informations sur les pays et les sites.
        
        Args:
            locations_section (Tag): Section Locations and Contact
            
        Returns:
            list: Liste des pays avec leurs sites
        """
        logger.debug("Extraction des informations sur les pays et les sites")
        
        # Récupération des sélecteurs
        selectors = LOCATIONS_SELECTORS
        
        # Extraction des sections de pays
        country_sections = locations_section.select(selectors["countries"])
        countries = []
        
        for country_section in country_sections:
            # Extraction du titre du pays
            country_title = extract_text(country_section)
            
            # Extraction du nom du pays et du statut
            match = re.search(r'(\d+\.\d+\.\d+)\s+(.+?)\s*-\s*(.+)', country_title)
            if match:
                section_number, country_name, status = match.groups()
                
                # Récupération du nombre de sujets prévus
                planned_subjects = self.extract_with_selector(
                    country_section.find_next("p", class_="bolder", string=lambda s: "Planned number of subjects" in s),
                    selectors["planned_subjects"]
                )
                
                # Extraction des sites pour ce pays
                sites = self.extract_sites(country_section, selectors["sites"])
                
                countries.append({
                    "country": country_name.strip(),
                    "status": status.strip(),
                    "planned_subjects": planned_subjects,
                    "sites": sites
                })
        
        return countries
    
    def extract_sites(self, country_section, selectors):
        """
        Extrait les informations sur les sites d'un pays.
        
        Args:
            country_section (Tag): Section d'un pays
            selectors (dict): Sélecteurs pour les sites
            
        Returns:
            list: Liste des sites
        """
        # Recherche des sections de sites
        site_sections = []
        next_element = country_section.find_next("div", class_="content")
        
        if next_element:
            site_sections = next_element.select(selectors["section"])
        
        sites = []
        
        for site_section in site_sections:
            # Extraction du titre du site
            site_title = extract_text(site_section)
            
            # Récupération des données pour ce site
            site = {
                "name": site_title.split(": ")[1] if ": " in site_title else site_title,
                "oms_id": self.extract_with_selector(site_section.parent, selectors["oms_id"]),
                "department": self.extract_with_selector(site_section.parent, selectors["department"]),
                "location": self.extract_with_selector(site_section.parent, selectors["location"]),
                "address": self.extract_with_selector(site_section.parent, selectors["address"]),
                "city": self.extract_with_selector(site_section.parent, selectors["city"]),
                "post_code": self.extract_with_selector(site_section.parent, selectors["post_code"]),
                "country": self.extract_with_selector(site_section.parent, selectors["country"]),
                "contact": {
                    "first_name": self.extract_with_selector(site_section.parent, selectors["contact_first_name"]),
                    "last_name": self.extract_with_selector(site_section.parent, selectors["contact_last_name"]),
                    "title": self.extract_with_selector(site_section.parent, selectors["contact_title"]),
                    "phone": self.extract_with_selector(site_section.parent, selectors["contact_phone"]),
                    "email": self.extract_with_selector(site_section.parent, selectors["contact_email"])
                }
            }
            
            sites.append(site)
        
        return sites
    
    def extract_sponsors(self, locations_section):
        """
        Extrait les informations sur les sponsors.
        
        Args:
            locations_section (Tag): Section Locations and Contact
            
        Returns:
            dict: Informations sur les sponsors
        """
        logger.debug("Extraction des informations sur les sponsors")
        
        # Récupération des sélecteurs
        selectors = LOCATIONS_SELECTORS["sponsors"]
        
        # Récupération de la section sponsors
        sponsors_section = locations_section.select_one(selectors["section"])
        if not sponsors_section:
            logger.warning("Section Sponsors non trouvée")
            return {}
        
        # Extraction des détails du sponsor
        sponsor_details = self.extract_sponsor_details(sponsors_section, selectors["sponsor_details"])
        
        # Extraction du contact scientifique
        scientific_contact = self.extract_scientific_contact(sponsors_section, selectors["scientific_contact"])
        
        # Extraction du contact public
        public_contact = self.extract_public_contact(sponsors_section, selectors["public_contact"])
        
        # Combinaison des résultats
        return {
            "details": sponsor_details,
            "scientific_contact": scientific_contact,
            "public_contact": public_contact
        }
    
    def extract_sponsor_details(self, sponsors_section, selectors):
        """
        Extrait les détails du sponsor.
        
        Args:
            sponsors_section (Tag): Section Sponsors
            selectors (dict): Sélecteurs pour les détails du sponsor
            
        Returns:
            dict: Détails du sponsor
        """
        # Recherche de la section des détails du sponsor
        sponsor_name = sponsors_section.find_next("p")
        if not sponsor_name:
            return {}
        
        # Récupération des données pour le sponsor
        sponsor_content = sponsor_name.find_next("div", class_="content")
        if not sponsor_content:
            return {"name": sponsor_name.text.strip()}
        
        return {
            "name": sponsor_name.text.strip(),
            "id": self.extract_with_selector(sponsor_content, selectors["id"]),
            "address": self.extract_with_selector(sponsor_content, selectors["address"]),
            "city": self.extract_with_selector(sponsor_content, selectors["city"]),
            "post_code": self.extract_with_selector(sponsor_content, selectors["post_code"]),
            "country": self.extract_with_selector(sponsor_content, selectors["country"]),
            "phone": self.extract_with_selector(sponsor_content, selectors["phone"]),
            "email": self.extract_with_selector(sponsor_content, selectors["email"])
        }
    
    def extract_scientific_contact(self, sponsors_section, selectors):
        """
        Extrait les informations sur le contact scientifique.
        
        Args:
            sponsors_section (Tag): Section Sponsors
            selectors (dict): Sélecteurs pour le contact scientifique
            
        Returns:
            dict: Informations sur le contact scientifique
        """
        return {
            "name": self.extract_with_selector(sponsors_section, selectors["name"]),
            "contact_name": self.extract_with_selector(sponsors_section, selectors["contact_name"]),
            "phone": self.extract_with_selector(sponsors_section, selectors["phone"]),
            "email": self.extract_with_selector(sponsors_section, selectors["email"])
        }
    
    def extract_public_contact(self, sponsors_section, selectors):
        """
        Extrait les informations sur le contact public.
        
        Args:
            sponsors_section (Tag): Section Sponsors
            selectors (dict): Sélecteurs pour le contact public
            
        Returns:
            dict: Informations sur le contact public
        """
        return {
            "name": self.extract_with_selector(sponsors_section, selectors["name"]),
            "contact_name": self.extract_with_selector(sponsors_section, selectors["contact_name"]),
            "phone": self.extract_with_selector(sponsors_section, selectors["phone"]),
            "email": self.extract_with_selector(sponsors_section, selectors["email"])
        }

def extract_locations(soup):
    """
    Fonction utilitaire pour extraire les informations de la section Locations and Contact.
    
    Args:
        soup (BeautifulSoup): Objet BeautifulSoup représentant le document HTML
        
    Returns:
        dict: Dictionnaire contenant les informations de la section Locations and Contact
    """
    extractor = LocationsExtractor(soup)
    return extractor.extract()