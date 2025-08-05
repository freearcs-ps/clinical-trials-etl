"""
Module pour le stockage des données d'essais cliniques dans MongoDB.
# mongosh
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError, PyMongoError

logger = logging.getLogger(__name__)


class MongoDBStorage:
    """
    Gestionnaire de stockage MongoDB pour les données d'essais cliniques.
    """

    def __init__(
        self,
        connection_string: str = "mongodb://localhost:27017/",
        database_name: str = "clinical_trials_db",
        collection_name: str = "trials",
    ):
        """
        Initialise la connexion MongoDB.

        Args:
            connection_string (str): Chaîne de connexion MongoDB
            database_name (str): Nom de la base de données
            collection_name (str): Nom de la collection principale
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        self._connected = False

    def connect(self) -> bool:
        """
        Établit la connexion à MongoDB.

        Returns:
            bool: True si la connexion est établie, False sinon
        """
        try:
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,  # 5 secondes timeout
                connectTimeoutMS=5000,
                maxPoolSize=50,
            )

            # Test de la connexion
            self.client.admin.command("ping")

            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]

            # Création des index
            self._create_indexes()

            self._connected = True
            logger.info(
                f"Connexion établie à MongoDB: {self.database_name}.{self.collection_name}"
            )
            return True

        except ConnectionFailure as e:
            logger.error(f"Erreur de connexion à MongoDB: {str(e)}")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la connexion à MongoDB: {str(e)}")
            self._connected = False
            return False

    def _create_indexes(self):
        """
        Crée les index nécessaires pour optimiser les requêtes.
        """
        try:
            # Index unique sur le numéro EUCT
            self.collection.create_index(
                [("header.euct_number", pymongo.ASCENDING)],
                unique=True,
                background=True,
            )

            # Index sur les pays des sites d'essais
            self.collection.create_index(
                [("locations.countries.country", pymongo.ASCENDING)], background=True
            )

            # Index sur la phase de l'essai
            self.collection.create_index(
                [("summary.trial_information.trial_phase", pymongo.ASCENDING)],
                background=True,
            )

            # Index sur la condition médicale
            self.collection.create_index(
                [("summary.trial_information.medical_condition", pymongo.ASCENDING)],
                background=True,
            )

            # Index sur la date de création/modification
            self.collection.create_index(
                [("metadata.created_at", pymongo.DESCENDING)], background=True
            )

            # Index composé pour recherche par statut et pays
            self.collection.create_index(
                [
                    (
                        "summary.overall_trial_status.application_trial_status.member_state",
                        pymongo.ASCENDING,
                    ),
                    (
                        "summary.overall_trial_status.application_trial_status.application_trial_status",
                        pymongo.ASCENDING,
                    ),
                ],
                background=True,
            )

            logger.info("Index MongoDB créés avec succès")

        except Exception as e:
            logger.warning(f"Erreur lors de la création des index: {str(e)}")

    def disconnect(self):
        """
        Ferme la connexion à MongoDB.
        """
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("Connexion MongoDB fermée")

    def is_connected(self) -> bool:
        """
        Vérifie si la connexion à MongoDB est active.

        Returns:
            bool: True si connecté, False sinon
        """
        return self._connected and self.client is not None

    def save_trial_data(
        self, trial_data: Dict[str, Any], source_file: str = None
    ) -> bool:
        """
        Sauvegarde les données d'un essai clinique.

        Args:
            trial_data (Dict): Données de l'essai clinique
            source_file (str): Fichier source des données

        Returns:
            bool: True si la sauvegarde a réussi, False sinon
        """
        if not self.is_connected():
            logger.error("Aucune connexion MongoDB active")
            return False

        try:
            # Ajout des métadonnées
            document = trial_data.copy()
            document["metadata"] = {
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "source_file": source_file,
                "version": "1.0",
            }

            # Tentative d'insertion
            result = self.collection.insert_one(document)

            if result.inserted_id:
                logger.info(
                    f"Essai clinique sauvegardé avec l'ID: {result.inserted_id}"
                )
                return True
            else:
                logger.error("Échec de la sauvegarde des données")
                return False

        except DuplicateKeyError:
            # Essai de mise à jour si l'essai existe déjà
            return self._update_trial_data(trial_data, source_file)

        except PyMongoError as e:
            logger.error(f"Erreur MongoDB lors de la sauvegarde: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la sauvegarde: {str(e)}")
            return False

    def _update_trial_data(
        self, trial_data: Dict[str, Any], source_file: str = None
    ) -> bool:
        """
        Met à jour les données d'un essai existant.

        Args:
            trial_data (Dict): Données de l'essai clinique
            source_file (str): Fichier source des données

        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        try:
            euct_number = trial_data.get("header", {}).get("euct_number")

            if not euct_number:
                logger.error("Numéro EUCT manquant pour la mise à jour")
                return False

            # Mise à jour des métadonnées
            trial_data["metadata.updated_at"] = datetime.utcnow()
            if source_file:
                trial_data["metadata.source_file"] = source_file

            result = self.collection.update_one(
                {"header.euct_number": euct_number}, {"$set": trial_data}, upsert=True
            )

            if result.modified_count > 0 or result.upserted_id:
                logger.info(f"Essai clinique mis à jour: {euct_number}")
                return True
            else:
                logger.warning(f"Aucune modification effectuée pour: {euct_number}")
                return True  # Pas d'erreur, mais pas de modification

        except PyMongoError as e:
            logger.error(f"Erreur MongoDB lors de la mise à jour: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la mise à jour: {str(e)}")
            return False

    def find_trial_by_euct(self, euct_number: str) -> Optional[Dict[str, Any]]:
        """
        Recherche un essai par son numéro EUCT.

        Args:
            euct_number (str): Numéro EUCT de l'essai

        Returns:
            Dict: Données de l'essai ou None si non trouvé
        """
        if not self.is_connected():
            logger.error("Aucune connexion MongoDB active")
            return None

        try:
            return self.collection.find_one({"header.euct_number": euct_number})
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {str(e)}")
            return None

    def find_trials_by_country(
        self, country: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Recherche les essais par pays.

        Args:
            country (str): Nom du pays
            limit (int): Nombre maximum de résultats

        Returns:
            List: Liste des essais trouvés
        """
        if not self.is_connected():
            logger.error("Aucune connexion MongoDB active")
            return []

        try:
            cursor = self.collection.find(
                {"locations.countries.country": country}
            ).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par pays: {str(e)}")
            return []

    def find_trials_by_condition(
        self, condition: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Recherche les essais par condition médicale.

        Args:
            condition (str): Condition médicale (recherche textuelle)
            limit (int): Nombre maximum de résultats

        Returns:
            List: Liste des essais trouvés
        """
        if not self.is_connected():
            logger.error("Aucune connexion MongoDB active")
            return []

        try:
            cursor = self.collection.find(
                {
                    "summary.trial_information.medical_condition": {
                        "$regex": condition,
                        "$options": "i",
                    }
                }
            ).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par condition: {str(e)}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtient des statistiques sur la base de données.

        Returns:
            Dict: Statistiques de la base de données
        """
        if not self.is_connected():
            logger.error("Aucune connexion MongoDB active")
            return {}

        try:
            stats = {
                "total_trials": self.collection.count_documents({}),
                "database_size": self.db.command("dbStats")["dataSize"],
                "collection_size": self.db.command("collStats", self.collection_name)[
                    "size"
                ],
                "average_document_size": self.db.command(
                    "collStats", self.collection_name
                ).get("avgObjSize", 0),
            }

            # Statistiques par phase
            pipeline = [
                {
                    "$group": {
                        "_id": "$summary.trial_information.trial_phase",
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"count": -1}},
            ]
            phase_stats = list(self.collection.aggregate(pipeline))
            stats["trials_by_phase"] = phase_stats

            # Statistiques par pays
            pipeline = [
                {"$unwind": "$locations.countries"},
                {
                    "$group": {
                        "_id": "$locations.countries.country",
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": 10},
            ]
            country_stats = list(self.collection.aggregate(pipeline))
            stats["top_countries"] = country_stats

            return stats

        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            return {}

    def bulk_insert_trials(
        self, trials_data: List[Dict[str, Any]], source_files: List[str] = None
    ) -> Dict[str, int]:
        """
        Insertion en lot de plusieurs essais.

        Args:
            trials_data (List): Liste des données d'essais
            source_files (List): Liste des fichiers sources

        Returns:
            Dict: Statistiques d'insertion (succès, échecs, doublons)
        """
        if not self.is_connected():
            logger.error("Aucune connexion MongoDB active")
            return {"success": 0, "failed": 0, "duplicates": 0}

        if not trials_data:
            return {"success": 0, "failed": 0, "duplicates": 0}

        results = {"success": 0, "failed": 0, "duplicates": 0}

        # Préparation des documents avec métadonnées
        documents = []
        for i, trial_data in enumerate(trials_data):
            document = trial_data.copy()
            document["metadata"] = {
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "source_file": (
                    source_files[i] if source_files and i < len(source_files) else None
                ),
                "version": "1.0",
            }
            documents.append(document)

        try:
            # Insertion en lot avec gestion des doublons
            result = self.collection.insert_many(documents, ordered=False)
            results["success"] = len(result.inserted_ids)

        except pymongo.errors.BulkWriteError as e:
            # Gestion des erreurs d'insertion en lot
            results["success"] = e.details.get("nInserted", 0)

            for error in e.details.get("writeErrors", []):
                if error.get("code") == 11000:  # Code pour duplicate key
                    results["duplicates"] += 1
                else:
                    results["failed"] += 1

        except Exception as e:
            logger.error(f"Erreur lors de l'insertion en lot: {str(e)}")
            results["failed"] = len(documents)

        logger.info(
            f"Insertion en lot terminée: {results['success']} succès, "
            f"{results['duplicates']} doublons, {results['failed']} échecs"
        )

        return results

    def export_to_json_file(
        self, output_file: str, query: Dict = None, limit: int = None
    ) -> bool:
        """
        Exporte les données vers un fichier JSON.

        Args:
            output_file (str): Chemin du fichier de sortie
            query (Dict): Filtre de requête MongoDB
            limit (int): Nombre maximum de documents à exporter

        Returns:
            bool: True si l'export a réussi, False sinon
        """
        if not self.is_connected():
            logger.error("Aucune connexion MongoDB active")
            return False

        try:
            import json
            from bson import ObjectId

            # Fonction pour sérialiser les ObjectId
            def json_serializer(obj):
                if isinstance(obj, ObjectId):
                    return str(obj)
                elif isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

            query = query or {}
            cursor = self.collection.find(query)

            if limit:
                cursor = cursor.limit(limit)

            documents = list(cursor)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(
                    documents, f, indent=2, ensure_ascii=False, default=json_serializer
                )

            logger.info(
                f"Export terminé: {len(documents)} documents exportés vers {output_file}"
            )
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'export: {str(e)}")
            return False

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
