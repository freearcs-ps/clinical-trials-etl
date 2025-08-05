"""
Utilitaires pour la configuration et l'utilisation de la journalisation.
"""

import logging
import logging.config
import os
import sys
from clinical_trials_extractor.config.settings import LOGGING

def setup_logging(level=logging.INFO):
    """
    Configure le système de journalisation.
    
    Args:
        level (int): Niveau de journalisation (par défaut: logging.INFO)
    """
    # Création du répertoire pour les fichiers de log si nécessaire
    log_file = LOGGING['handlers']['file']['filename']
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configuration du niveau de journalisation
    LOGGING['root']['level'] = level
    LOGGING['handlers']['console']['level'] = level
    
    # Application de la configuration
    logging.config.dictConfig(LOGGING)
    
    # Message de démarrage
    logger = logging.getLogger(__name__)
    logger.info("Système de journalisation initialisé")

def get_logger(name):
    """
    Obtient un logger configuré pour un module spécifique.
    
    Args:
        name (str): Nom du module
        
    Returns:
        Logger: Logger configuré
    """
    return logging.getLogger(name)

class ProgressLogger:
    """
    Classe pour journaliser la progression d'un traitement par lots.
    """
    
    def __init__(self, total, name="Traitement", log_interval=5):
        """
        Initialise le logger de progression.
        
        Args:
            total (int): Nombre total d'éléments à traiter
            name (str): Nom du traitement
            log_interval (int): Intervalle de journalisation en pourcentage
        """
        self.logger = logging.getLogger(__name__)
        self.total = total
        self.current = 0
        self.name = name
        self.log_interval = log_interval
        self.last_logged_percent = 0
        
        self.logger.info(f"{self.name} démarré - {self.total} éléments à traiter")
    
    def update(self, increment=1):
        """
        Met à jour la progression.
        
        Args:
            increment (int): Nombre d'éléments traités
        """
        self.current += increment
        percent = int((self.current / self.total) * 100)
        
        # Journalisation à intervalles réguliers
        if percent >= self.last_logged_percent + self.log_interval or self.current == self.total:
            self.logger.info(f"{self.name} - {self.current}/{self.total} éléments traités ({percent}%)")
            self.last_logged_percent = percent
    
    def complete(self, success_count=None):
        """
        Marque le traitement comme terminé.
        
        Args:
            success_count (int): Nombre d'éléments traités avec succès
        """
        if success_count is not None:
            self.logger.info(f"{self.name} terminé - {success_count}/{self.total} éléments traités avec succès")
        else:
            self.logger.info(f"{self.name} terminé - {self.current}/{self.total} éléments traités")

def log_exception(e, message="Une erreur est survenue"):
    """
    Journalise une exception avec des détails.
    
    Args:
        e (Exception): Exception à journaliser
        message (str): Message descriptif
    """
    logger = logging.getLogger(__name__)
    logger.error(f"{message}: {str(e)}")
    logger.debug(f"Détails de l'exception:", exc_info=True)