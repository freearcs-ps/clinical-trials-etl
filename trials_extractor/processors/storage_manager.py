"""
Module pour le stockage des données d'essais cliniques traitées.
"""

import logging
from typing import Dict, Any, Optional

try:
    from clinical_trials_extractor.config.settings import MONGODB_SETTINGS
except ImportError:
    # Configuration par défaut si le module settings n'est pas disponible
    MONGODB_SETTINGS = {
        "connection_string": "mongodb://localhost:27017/",
        "database_name": "clinical_trials_db",
        "collection_name": "trials",
        "enable_storage": False,
    }

from clinical_trials_extractor.storage.mongodb_storage import MongoDBStorage

logger = logging.getLogger(__name__)


class DataStorage:
    """
    Gestionnaire de stockage des données d'essais cliniques.
    """

    def __init__(self):
        """
        Initialise le gestionnaire de stockage.
        """
        self.mongodb_enabled = MONGODB_SETTINGS["enable_storage"]
        self.mongodb_storage = None

        if self.mongodb_enabled:
            self._initialize_mongodb()

    def _initialize_mongodb(self):
        """
        Initialise la connexion MongoDB si activée.
        """
        try:
            self.mongodb_storage = MongoDBStorage(
                connection_string=MONGODB_SETTINGS["connection_string"],
                database_name=MONGODB_SETTINGS["database_name"],
                collection_name=MONGODB_SETTINGS["collection_name"],
            )

            if self.mongodb_storage.connect():
                logger.info("Stockage MongoDB initialisé avec succès")
            else:
                logger.warning("Échec de l'initialisation MongoDB - stockage désactivé")
                self.mongodb_enabled = False
                self.mongodb_storage = None

        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation MongoDB: {str(e)}")
            self.mongodb_enabled = False
            self.mongodb_storage = None

    def store_trial_data(
        self, processed_data: Dict[str, Any], source_file: str = None
    ) -> Dict[str, Any]:
        """
        Stocke les données d'essai clinique traitées.

        Args:
            processed_data (Dict): Données traitées de l'essai
            source_file (str): Fichier source des données

        Returns:
            Dict: Résultat du stockage avec les statuts
        """
        storage_results = {
            "mongodb": {
                "enabled": self.mongodb_enabled,
                "success": False,
                "error": None,
            }
        }

        # Stockage MongoDB
        if self.mongodb_enabled and self.mongodb_storage:
            try:
                success = self.mongodb_storage.save_trial_data(
                    processed_data, source_file
                )
                storage_results["mongodb"]["success"] = success

                if success:
                    logger.info(
                        f"Données stockées avec succès dans MongoDB pour {source_file}"
                    )
                else:
                    logger.warning(f"Échec du stockage MongoDB pour {source_file}")

            except Exception as e:
                error_msg = f"Erreur lors du stockage MongoDB: {str(e)}"
                logger.error(error_msg)
                storage_results["mongodb"]["error"] = error_msg

        return storage_results

    def get_trial_by_euct(self, euct_number: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un essai par son numéro EUCT.

        Args:
            euct_number (str): Numéro EUCT de l'essai

        Returns:
            Dict: Données de l'essai ou None si non trouvé
        """
        if not self.mongodb_enabled or not self.mongodb_storage:
            logger.warning("MongoDB non disponible pour la recherche")
            return None

        try:
            return self.mongodb_storage.find_trial_by_euct(euct_number)
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {str(e)}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtient les statistiques de stockage.

        Returns:
            Dict: Statistiques des différents systèmes de stockage
        """
        stats = {
            "mongodb": {
                "enabled": self.mongodb_enabled,
                "connected": (
                    self.mongodb_storage.is_connected()
                    if self.mongodb_storage
                    else False
                ),
                "statistics": {},
            }
        }

        if self.mongodb_enabled and self.mongodb_storage:
            try:
                stats["mongodb"]["statistics"] = self.mongodb_storage.get_statistics()
            except Exception as e:
                logger.error(
                    f"Erreur lors de la récupération des statistiques: {str(e)}"
                )
                stats["mongodb"]["error"] = str(e)

        return stats

    def close_connections(self):
        """
        Ferme toutes les connexions de stockage.
        """
        if self.mongodb_storage:
            self.mongodb_storage.disconnect()
            logger.info("Connexions de stockage fermées")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_connections()
