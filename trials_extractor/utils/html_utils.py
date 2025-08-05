"""
Utilitaires pour le traitement des fichiers HTML.
Ce module contient des fonctions pour charger, analyser et extraire des données
des documents HTML d'essais cliniques.
"""

import logging
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

def load_html(file_path):
    """
    Charge un fichier HTML et retourne un objet BeautifulSoup.
    
    Args:
        file_path (str): Chemin vers le fichier HTML
        
    Returns:
        BeautifulSoup: Objet BeautifulSoup représentant le document HTML
        
    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        Exception: Pour les autres erreurs de lecture
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return BeautifulSoup(html_content, 'lxml')
    except FileNotFoundError:
        logger.error(f"Fichier non trouvé: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Erreur lors du chargement du fichier HTML {file_path}: {str(e)}")
        raise

def load_html_from_string(html_content):
    """
    Crée un objet BeautifulSoup à partir d'une chaîne HTML.
    
    Args:
        html_content (str): Contenu HTML
        
    Returns:
        BeautifulSoup: Objet BeautifulSoup représentant le document HTML
    """
    return BeautifulSoup(html_content, 'lxml')

def get_section(soup, section_id):
    """
    Extrait une section spécifique du document.
    
    Args:
        soup (BeautifulSoup): Objet BeautifulSoup représentant le document HTML
        section_id (str): ID de la section à extraire
        
    Returns:
        Tag: Élément HTML correspondant à la section, ou None si non trouvé
    """
    section = soup.find(id=section_id)
    if not section:
        logger.warning(f"Section avec l'id '{section_id}' non trouvée")
    return section

def select_element(soup, selector, default=None):
    """
    Sélectionne un élément à l'aide d'un sélecteur CSS.
    
    Args:
        soup (BeautifulSoup): Objet BeautifulSoup ou Tag
        selector (str): Sélecteur CSS
        default: Valeur par défaut si l'élément n'est pas trouvé
        
    Returns:
        Tag: Élément HTML correspondant au sélecteur, ou default si non trouvé
    """
    if not soup:
        return default
    
    try:
        # Gestion des sélecteurs avec :contains()
        if ":contains(" in selector:
            # Extraction du texte à rechercher
            pattern = r":contains\(['\"](.+?)['\"]\)"
            match = re.search(pattern, selector)
            if match:
                text_to_find = match.group(1)
                # Création d'un nouveau sélecteur sans la partie :contains()
                base_selector = re.sub(pattern, "", selector)
                
                # Sélection des éléments correspondant au sélecteur de base
                elements = soup.select(base_selector)
                
                # Filtrage des éléments contenant le texte recherché
                for element in elements:
                    if text_to_find in element.text:
                        return element
                
                return default
        
        # Sélecteur CSS standard
        element = soup.select_one(selector)
        return element if element else default
    except Exception as e:
        logger.warning(f"Erreur lors de la sélection avec le sélecteur '{selector}': {str(e)}")
        return default

def extract_text(element, default=""):
    """
    Extrait le texte d'un élément HTML.
    
    Args:
        element (Tag): Élément HTML
        default (str): Valeur par défaut si l'élément est None
        
    Returns:
        str: Texte extrait, ou default si l'élément est None
    """
    if element is None:
        return default
    return element.text.strip()

def extract_table(table_element):
    """
    Extrait les données d'un tableau HTML.
    
    Args:
        table_element (Tag): Élément table HTML
        
    Returns:
        list: Liste de dictionnaires représentant les lignes du tableau
    """
    if not table_element:
        return []
    
    # Extraction des en-têtes
    headers = []
    thead = table_element.find("thead")
    if thead:
        headers = [th.text.strip() for th in thead.find_all("th")]
    
    # Si pas d'en-têtes dans thead, chercher dans la première ligne
    if not headers:
        first_row = table_element.find("tr")
        if first_row:
            headers = [th.text.strip() for th in first_row.find_all("th")]
    
    if not headers:
        logger.warning("Aucun en-tête trouvé dans le tableau")
        return []
    
    # Extraction des lignes
    rows = []
    tbody = table_element.find("tbody")
    if tbody:
        for tr in tbody.find_all("tr"):
            cells = [td.text.strip() for td in tr.find_all("td")]
            if len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))
            else:
                logger.warning(f"Différence entre le nombre d'en-têtes ({len(headers)}) et de cellules ({len(cells)})")
    
    return rows

def extract_list(list_element):
    """
    Extrait les éléments d'une liste HTML.
    
    Args:
        list_element (Tag): Élément ul ou ol HTML
        
    Returns:
        list: Liste des éléments extraits
    """
    if not list_element:
        return []
    
    return [li.text.strip() for li in list_element.find_all("li")]

def extract_label_value_pairs(container, label_selector="p.bolder", value_selector="p", label_suffix=":"):
    """
    Extrait des paires label-valeur d'un conteneur HTML.
    
    Args:
        container (Tag): Élément HTML contenant les paires label-valeur
        label_selector (str): Sélecteur CSS pour les labels
        value_selector (str): Sélecteur CSS pour les valeurs
        label_suffix (str): Suffixe à supprimer des labels
        
    Returns:
        dict: Dictionnaire des paires label-valeur extraites
    """
    if not container:
        return {}
    
    result = {}
    labels = container.select(label_selector)
    
    for label in labels:
        key = label.text.strip()
        if key.endswith(label_suffix):
            key = key[:-len(label_suffix)]
        
        value_element = label.find_next(value_selector.split('.')[0])
        if value_element:
            value = value_element.text.strip()
            result[key] = value
    
    return result

def get_next_sibling_text(element, tag="p", default=""):
    """
    Obtient le texte du prochain élément frère d'un type spécifié.
    
    Args:
        element (Tag): Élément HTML
        tag (str): Type d'élément à rechercher
        default (str): Valeur par défaut si aucun élément frère n'est trouvé
        
    Returns:
        str: Texte de l'élément frère, ou default si non trouvé
    """
    if not element:
        return default
    
    sibling = element.find_next_sibling(tag)
    if not sibling:
        return default
    
    return sibling.text.strip()