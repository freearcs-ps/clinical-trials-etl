"""
Module pour l'extraction des informations d'en-tête de l'essai clinique.
"""

import logging
from clinical_trials_extractor.extractors.base import BaseExtractor
from clinical_trials_extractor.config.selectors import HEADER_SELECTORS

logger = logging.getLogger(__name__)

class HeaderExtractor(BaseExtractor):
    """
    Extracteur pour les informations d'en-tête de l'essai clinique.
    """
    
    def extract(self):
        """
        Extrait les informations d'en-tête de l'essai clinique.
        
        Returns:
            dict: Dictionnaire contenant les informations d'en-tête
        """
        logger.info("Extraction des informations d'en-tête")
        
        if not self.soup:
            logger.error("Aucun contenu HTML fourni")
            return {}
        
        # Essayer d'extraire les informations d'en-tête
        title = self.extract_with_selector(self.soup, HEADER_SELECTORS["title"])
        euct_number = self.extract_with_selector(self.soup, HEADER_SELECTORS["euct_number"])
        protocol_code = self.extract_with_selector(self.soup, HEADER_SELECTORS["protocol_code"])
        
        # Si le numéro EUCT n'est pas trouvé, essayer de l'extraire depuis la section des détails de l'essai
        if not euct_number:
            try:
                # Essayer d'extraire depuis la section des identifiants de l'essai
                trial_id_section = self.soup.select_one("h3:contains('Trial identifiers')")
                if trial_id_section:
                    eu_trial_number_label = trial_id_section.find_next("p", class_="bolder", string=lambda s: "EU trial number" in s if s else False)
                    if eu_trial_number_label:
                        euct_number = eu_trial_number_label.find_next("p").get_text(strip=True)
            except Exception as e:
                logger.debug(f"Erreur lors de l'extraction alternative du numéro EUCT: {str(e)}")
        
        # Si le titre n'est pas trouvé, essayer de l'extraire depuis la section des détails de l'essai
        if not title:
            try:
                # Essayer d'extraire depuis la section des identifiants de l'essai
                trial_id_section = self.soup.select_one("h3:contains('Trial identifiers')")
                if trial_id_section:
                    full_title_label = trial_id_section.find_next("p", class_="bolder", string=lambda s: "Full title" in s if s else False)
                    if full_title_label:
                        title = full_title_label.find_next("p").get_text(strip=True)
            except Exception as e:
                logger.debug(f"Erreur lors de l'extraction alternative du titre: {str(e)}")
        
        # Créer l'en-tête avec les informations extraites
        header = {
            "title": title or "Non spécifié",
            "euct_number": euct_number or "Non spécifié",
            "protocol_code": protocol_code or "Non spécifié"
        }
        
        # Vérification des champs obligatoires
        if header["euct_number"] == "Non spécifié":
            logger.warning("Numéro EUCT non trouvé dans l'en-tête")
        
        logger.debug(f"Informations d'en-tête extraites: {header}")
        return header

def extract_header(soup):
    """
    Fonction utilitaire pour extraire les informations d'en-tête.
    
    Args:
        soup (BeautifulSoup): Objet BeautifulSoup représentant le document HTML
        
    Returns:
        dict: Dictionnaire contenant les informations d'en-tête
    """
    extractor = HeaderExtractor(soup)
    return extractor.extract()