"""
Module pour l'extraction des informations de la section Trial Results de l'essai clinique.
"""

import logging
from clinical_trials_extractor.extractors.base import BaseExtractor
from clinical_trials_extractor.config.selectors import TRIAL_RESULTS_SELECTORS

logger = logging.getLogger(__name__)

class ResultsExtractor(BaseExtractor):
    """
    Extracteur pour les informations de la section Trial Results de l'essai clinique.
    """
    
    def extract(self):
        """
        Extrait les informations de la section Trial Results.
        
        Returns:
            dict: Dictionnaire contenant les informations de la section Trial Results
        """
        logger.info("Extraction des informations de la section Trial Results")
        
        # Récupération de la section Trial Results
        results_section = self.extract_section("trial_results")
        if not results_section:
            logger.error("Section Trial Results non trouvée")
            return {}
        
        # Extraction des différentes sous-sections
        self.data = {
            "summaries": self.extract_summaries(results_section),
            "layperson_summaries": self.extract_layperson_summaries(results_section),
            "clinical_study_reports": self.extract_clinical_study_reports(results_section)
        }
        
        logger.debug("Informations de la section Trial Results extraites")
        return self.data
    
    def extract_summaries(self, results_section):
        """
        Extrait les résumés des résultats.
        
        Args:
            results_section (Tag): Section Trial Results
            
        Returns:
            list: Résumés des résultats
        """
        logger.debug("Extraction des résumés des résultats")
        
        # Récupération de la sous-section
        selectors = TRIAL_RESULTS_SELECTORS
        summaries_section = results_section.select_one(selectors["summaries"])
        if not summaries_section:
            logger.warning("Sous-section Summaries of Results non trouvée")
            return []
        
        # Extraction des résumés
        # Note: Dans l'exemple fourni, cette section est vide
        # Nous implémentons une structure de base qui pourra être étendue
        
        # Recherche des éléments après le titre de la section
        summaries = []
        next_element = summaries_section.find_next_sibling()
        
        # Parcours des éléments jusqu'à la prochaine section
        while next_element and not next_element.name == "h2":
            # Si c'est un élément pertinent, l'extraire
            if next_element.name in ["table", "ul", "ol", "p"]:
                if next_element.name == "table":
                    # Extraction d'un tableau
                    summaries.append({
                        "type": "table",
                        "content": self.extract_table_with_selector(results_section, f"#{next_element.get('id')}")
                    })
                elif next_element.name in ["ul", "ol"]:
                    # Extraction d'une liste
                    summaries.append({
                        "type": "list",
                        "content": self.extract_list_with_selector(results_section, f"#{next_element.get('id')}")
                    })
                elif next_element.name == "p" and next_element.text.strip():
                    # Extraction d'un paragraphe
                    summaries.append({
                        "type": "text",
                        "content": next_element.text.strip()
                    })
            
            next_element = next_element.find_next_sibling()
        
        return summaries
    
    def extract_layperson_summaries(self, results_section):
        """
        Extrait les résumés vulgarisés des résultats.
        
        Args:
            results_section (Tag): Section Trial Results
            
        Returns:
            list: Résumés vulgarisés des résultats
        """
        logger.debug("Extraction des résumés vulgarisés des résultats")
        
        # Récupération de la sous-section
        selectors = TRIAL_RESULTS_SELECTORS
        summaries_section = results_section.select_one(selectors["layperson_summaries"])
        if not summaries_section:
            logger.warning("Sous-section Layperson Summaries of Results non trouvée")
            return []
        
        # Extraction des résumés vulgarisés
        # Note: Dans l'exemple fourni, cette section est vide
        # Nous implémentons une structure de base qui pourra être étendue
        
        # Recherche des éléments après le titre de la section
        summaries = []
        next_element = summaries_section.find_next_sibling()
        
        # Parcours des éléments jusqu'à la prochaine section
        while next_element and not next_element.name == "h2":
            # Si c'est un élément pertinent, l'extraire
            if next_element.name in ["table", "ul", "ol", "p"]:
                if next_element.name == "table":
                    # Extraction d'un tableau
                    summaries.append({
                        "type": "table",
                        "content": self.extract_table_with_selector(results_section, f"#{next_element.get('id')}")
                    })
                elif next_element.name in ["ul", "ol"]:
                    # Extraction d'une liste
                    summaries.append({
                        "type": "list",
                        "content": self.extract_list_with_selector(results_section, f"#{next_element.get('id')}")
                    })
                elif next_element.name == "p" and next_element.text.strip():
                    # Extraction d'un paragraphe
                    summaries.append({
                        "type": "text",
                        "content": next_element.text.strip()
                    })
            
            next_element = next_element.find_next_sibling()
        
        return summaries
    
    def extract_clinical_study_reports(self, results_section):
        """
        Extrait les rapports d'étude clinique.
        
        Args:
            results_section (Tag): Section Trial Results
            
        Returns:
            list: Rapports d'étude clinique
        """
        logger.debug("Extraction des rapports d'étude clinique")
        
        # Récupération de la sous-section
        selectors = TRIAL_RESULTS_SELECTORS
        reports_section = results_section.select_one(selectors["clinical_study_reports"])
        if not reports_section:
            logger.warning("Sous-section Clinical Study Reports non trouvée")
            return []
        
        # Extraction des rapports d'étude clinique
        # Note: Dans l'exemple fourni, cette section est vide
        # Nous implémentons une structure de base qui pourra être étendue
        
        # Recherche des éléments après le titre de la section
        reports = []
        next_element = reports_section.find_next_sibling()
        
        # Parcours des éléments jusqu'à la prochaine section
        while next_element and not next_element.name == "h2":
            # Si c'est un élément pertinent, l'extraire
            if next_element.name in ["table", "ul", "ol", "p"]:
                if next_element.name == "table":
                    # Extraction d'un tableau
                    reports.append({
                        "type": "table",
                        "content": self.extract_table_with_selector(results_section, f"#{next_element.get('id')}")
                    })
                elif next_element.name in ["ul", "ol"]:
                    # Extraction d'une liste
                    reports.append({
                        "type": "list",
                        "content": self.extract_list_with_selector(results_section, f"#{next_element.get('id')}")
                    })
                elif next_element.name == "p" and next_element.text.strip():
                    # Extraction d'un paragraphe
                    reports.append({
                        "type": "text",
                        "content": next_element.text.strip()
                    })
            
            next_element = next_element.find_next_sibling()
        
        return reports

def extract_results(soup):
    """
    Fonction utilitaire pour extraire les informations de la section Trial Results.
    
    Args:
        soup (BeautifulSoup): Objet BeautifulSoup représentant le document HTML
        
    Returns:
        dict: Dictionnaire contenant les informations de la section Trial Results
    """
    extractor = ResultsExtractor(soup)
    return extractor.extract()