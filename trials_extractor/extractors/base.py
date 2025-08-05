"""
Module de base pour les extracteurs de données.
Contient la classe de base et les fonctions communes à tous les extracteurs.
"""

import logging
from bs4 import Tag
from clinical_trials_extractor.utils.html_utils import (
    select_element, 
    extract_text, 
    extract_table, 
    extract_list,
    extract_label_value_pairs
)

logger = logging.getLogger(__name__)

class BaseExtractor:
    """
    Classe de base pour tous les extracteurs de données.
    """
    
    def __init__(self, soup):
        """
        Initialise l'extracteur avec un objet BeautifulSoup.
        
        Args:
            soup (BeautifulSoup): Objet BeautifulSoup représentant le document HTML
        """
        self.soup = soup
        self.data = {}
    
    def extract(self):
        """
        Méthode principale d'extraction des données.
        À implémenter dans les classes dérivées.
        
        Returns:
            dict: Données extraites
        """
        raise NotImplementedError("La méthode extract() doit être implémentée dans les classes dérivées")
    
    def extract_simple_field(self, container, label_text, next_tag="p", default=""):
        """
        Extrait un champ simple (paire label-valeur).
        
        Args:
            container (BeautifulSoup|Tag): Conteneur HTML
            label_text (str): Texte du label à rechercher
            next_tag (str): Tag HTML contenant la valeur (par défaut "p")
            default (str): Valeur par défaut si non trouvée
            
        Returns:
            str: Valeur extraite, ou default si non trouvée
        """
        if not container:
            return default
            
        # Recherche du label
        label = container.find("p", class_="bolder", string=lambda s: label_text in s)
        if not label:
            logger.debug(f"Label '{label_text}' non trouvé")
            return default
            
        # Recherche de la valeur
        value_tag = label.find_next(next_tag)
        if not value_tag:
            logger.debug(f"Aucun tag {next_tag} après le label '{label_text}'")
            return default
            
        return value_tag.text.strip()
    
    def extract_section(self, section_id):
        """
        Extrait une section spécifique du document.
        
        Args:
            section_id (str): ID de la section à extraire
            
        Returns:
            Tag: Élément HTML correspondant à la section, ou None si non trouvé
        """
        section = self.soup.find(id=section_id)
        if not section:
            logger.warning(f"Section avec l'id '{section_id}' non trouvée")
        return section
    
    def extract_with_selector(self, container, selector, default=""):
        """
        Extrait le texte d'un élément à l'aide d'un sélecteur CSS.
        
        Args:
            container (BeautifulSoup|Tag): Conteneur HTML
            selector (str): Sélecteur CSS
            default (str): Valeur par défaut si non trouvée
            
        Returns:
            str: Texte extrait, ou default si non trouvé
        """
        element = select_element(container, selector)
        return extract_text(element, default)
    
    def extract_table_with_selector(self, container, selector):
        """
        Extrait un tableau à l'aide d'un sélecteur CSS.
        
        Args:
            container (BeautifulSoup|Tag): Conteneur HTML
            selector (str): Sélecteur CSS
            
        Returns:
            list: Liste de dictionnaires représentant les lignes du tableau
        """
        table = select_element(container, selector)
        return extract_table(table)
    
    def extract_list_with_selector(self, container, selector):
        """
        Extrait une liste à l'aide d'un sélecteur CSS.
        
        Args:
            container (BeautifulSoup|Tag): Conteneur HTML
            selector (str): Sélecteur CSS
            
        Returns:
            list: Liste des éléments extraits
        """
        list_element = select_element(container, selector)
        return extract_list(list_element)
    
    def extract_label_value_pairs_with_selector(self, container, selector):
        """
        Extrait des paires label-valeur à l'aide d'un sélecteur CSS.
        
        Args:
            container (BeautifulSoup|Tag): Conteneur HTML
            selector (str): Sélecteur CSS
            
        Returns:
            dict: Dictionnaire des paires label-valeur extraites
        """
        section = select_element(container, selector)
        return extract_label_value_pairs(section)
    
    def extract_subsections(self, container, subsection_selector, process_func):
        """
        Extrait et traite des sous-sections.
        
        Args:
            container (BeautifulSoup|Tag): Conteneur HTML
            subsection_selector (str): Sélecteur CSS pour les sous-sections
            process_func (callable): Fonction de traitement pour chaque sous-section
            
        Returns:
            list: Liste des résultats du traitement des sous-sections
        """
        if not container:
            return []
            
        subsections = container.select(subsection_selector)
        results = []
        
        for subsection in subsections:
            result = process_func(subsection)
            if result:
                results.append(result)
                
        return results
    
    def extract_countries_data(self, container, country_selector, process_func):
        """
        Extrait et traite des données par pays.
        
        Args:
            container (BeautifulSoup|Tag): Conteneur HTML
            country_selector (str): Sélecteur CSS pour les pays
            process_func (callable): Fonction de traitement pour chaque pays
            
        Returns:
            dict: Dictionnaire des données par pays
        """
        if not container:
            return {}
            
        countries = container.select(country_selector)
        results = {}
        
        for country in countries:
            country_name = extract_text(country).split(' - ')[0]
            if country_name:
                country_data = process_func(country)
                if country_data:
                    results[country_name] = country_data
                    
        return results