#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script principal pour l'extraction automatisée des données d'essais cliniques.
"""

import os
import sys
import click
import logging
from datetime import datetime

from clinical_trials_extractor.utils import html_utils, logging_utils, batch_utils
from clinical_trials_extractor.extractors import (
    header,
    summary,
    trial_info,
    results,
    locations,
)
from clinical_trials_extractor.processors import (
    cleaner,
    normalizer,
    validator,
    storage_manager,
)
from clinical_trials_extractor.exporters import json_exporter, csv_exporter
from clinical_trials_extractor.config.settings import EXPORT_FORMATS, AVAILABLE_SECTIONS


def _configure_mongodb(enable_mongodb, mongodb_uri, mongodb_database):
    """
    Configure les paramètres MongoDB.

    Args:
        enable_mongodb (bool): Activer le stockage MongoDB
        mongodb_uri (str): URI de connexion MongoDB
        mongodb_database (str): Nom de la base de données
    """
    if enable_mongodb:
        import os

        if mongodb_uri:
            os.environ["MONGODB_URI"] = mongodb_uri
        if mongodb_database:
            os.environ["MONGODB_DATABASE"] = mongodb_database
        os.environ["ENABLE_MONGODB_STORAGE"] = "true"
        logging.info("Stockage MongoDB activé")


@click.command()
@click.option("--input", "-i", help="Chemin vers le fichier HTML à traiter")
@click.option(
    "--input-dir",
    "-d",
    help="Chemin vers le répertoire contenant les fichiers HTML à traiter",
)
@click.option(
    "--output", "-o", required=True, help="Chemin vers le répertoire de sortie"
)
@click.option(
    "--format",
    "-f",
    multiple=True,
    default=EXPORT_FORMATS,
    help="Format(s) de sortie (json, csv)",
)
@click.option(
    "--sections",
    "-s",
    multiple=True,
    help="Sections à extraire (header, summary, trial_info, results, locations)",
)
@click.option("--verbose", "-v", is_flag=True, help="Mode verbeux")
@click.option("--enable-mongodb", is_flag=True, help="Activer le stockage MongoDB")
@click.option("--mongodb-uri", help="URI de connexion MongoDB")
@click.option("--mongodb-database", help="Nom de la base de données MongoDB")
def main(
    input,
    input_dir,
    output,
    format,
    sections,
    verbose,
    enable_mongodb,
    mongodb_uri,
    mongodb_database,
):
    """Extracteur automatisé de données d'essais cliniques."""

    # Configuration du logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging_utils.setup_logging(log_level)

    # Configuration MongoDB si activée
    _configure_mongodb(enable_mongodb, mongodb_uri, mongodb_database)

    # Vérification des arguments
    if not input and not input_dir:
        click.echo("Erreur: Vous devez spécifier soit --input, soit --input-dir")
        sys.exit(1)

    # Création du répertoire de sortie
    os.makedirs(output, exist_ok=True)

    # Préparation des options
    options = {
        "formats": format,
        "sections": sections if sections else AVAILABLE_SECTIONS,
        "verbose": verbose,
    }

    # Traitement d'un seul fichier
    if input:
        if not os.path.isfile(input):
            click.echo(f"Erreur: Le fichier {input} n'existe pas")
            sys.exit(1)

        logging.info(f"Traitement du fichier {input}")
        result = process_file(input, output, options)
        if result["success"]:
            click.echo(f"Traitement réussi. Données exportées dans {output}")
        else:
            click.echo(f"Erreur lors du traitement: {result['error']}")

    # Traitement d'un répertoire
    elif input_dir:
        if not os.path.isdir(input_dir):
            click.echo(f"Erreur: Le répertoire {input_dir} n'existe pas")
            sys.exit(1)

        # Récupération des fichiers HTML
        html_files = [
            os.path.join(input_dir, f)
            for f in os.listdir(input_dir)
            if f.endswith(".html") and os.path.isfile(os.path.join(input_dir, f))
        ]

        if not html_files:
            click.echo(f"Aucun fichier HTML trouvé dans {input_dir}")
            sys.exit(0)

        logging.info(f"Traitement de {len(html_files)} fichiers HTML")
        results = batch_utils.process_batch(html_files, process_file, output, options)

        # Rapport de traitement
        success_count = sum(1 for r in results if r.get("success", False))
        click.echo(
            f"Traitement terminé: {success_count}/{len(results)} fichiers traités avec succès"
        )

        if success_count < len(results):
            click.echo("Erreurs rencontrées:")
            for result in results:
                if not result.get("success", False):
                    click.echo(f"  - {result.get('file')}: {result.get('error')}")


def process_file(file_path, output_dir, options):
    """
    Traite un fichier HTML.

    Args:
        file_path (str): Chemin du fichier HTML
        output_dir (str): Répertoire de sortie
        options (dict): Options de traitement

    Returns:
        dict: Résultat du traitement
    """
    try:
        # Création du répertoire de sortie spécifique au fichier
        file_name = os.path.basename(file_path)
        file_base_name = os.path.splitext(file_name)[0]
        file_output_dir = os.path.join(output_dir, file_base_name)
        os.makedirs(file_output_dir, exist_ok=True)

        # Chargement du fichier HTML
        logging.info(f"Chargement du fichier {file_path}")
        soup = html_utils.load_html(file_path)

        # Extraction des données
        logging.info("Extraction des données")
        data = extract_data(soup, options["sections"])

        # Traitement des données
        logging.info("Traitement des données")
        processed_data = process_data(data, file_path)

        # Validation des données
        logging.info("Validation des données")
        valid, issues = validator.validate_and_report(processed_data)

        # Export des données
        logging.info("Export des données")
        export_results = export_data(
            processed_data, file_output_dir, options["formats"]
        )

        return {
            "file": file_path,
            "success": True,
            "output_dir": file_output_dir,
            "valid": valid,
            "issues": issues,
            "export_results": export_results,
        }
    except Exception as e:
        logging.error(f"Erreur lors du traitement du fichier {file_path}: {str(e)}")
        return {"file": file_path, "success": False, "error": str(e)}


def extract_data(soup, sections):
    """
    Extrait les données du document HTML.

    Args:
        soup (BeautifulSoup): Objet BeautifulSoup représentant le document HTML
        sections (list): Liste des sections à extraire

    Returns:
        dict: Données extraites
    """
    data = {}

    # Extraction des sections spécifiées
    if "header" in sections:
        data["header"] = header.extract_header(soup)

    if "summary" in sections:
        data["summary"] = summary.extract_summary(soup)

    if "trial_info" in sections:
        data["trial_information"] = trial_info.extract_trial_info(soup)

    if "results" in sections:
        data["trial_results"] = results.extract_results(soup)

    if "locations" in sections:
        data["locations"] = locations.extract_locations(soup)

    return data


def process_data(data, source_file=None):
    """
    Traite les données extraites et les stocke en base si configuré.

    Args:
        data (dict): Données extraites
        source_file (str): Fichier source des données

    Returns:
        dict: Données traitées avec informations de stockage
    """
    # Nettoyage des données
    cleaned_data = cleaner.clean_and_standardize(data)

    # Normalisation des données
    normalized_data = normalizer.normalize_data(cleaned_data)

    # Stockage des données si activé
    storage_results = {}
    try:
        with storage_manager.DataStorage() as storage:
            storage_results = storage.store_trial_data(normalized_data, source_file)
    except Exception as e:
        logging.error(f"Erreur lors du stockage: {str(e)}")
        storage_results = {
            "mongodb": {"enabled": False, "success": False, "error": str(e)}
        }

    # Ajout des informations de stockage aux données traitées
    normalized_data["_storage_info"] = storage_results

    return normalized_data


def export_data(data, output_dir, formats):
    """
    Exporte les données traitées.

    Args:
        data (dict): Données traitées
        output_dir (str): Répertoire de sortie
        formats (list): Formats d'export

    Returns:
        dict: Résultats de l'export
    """
    results = {}

    # Export au format JSON
    if "json" in formats:
        json_dir = os.path.join(output_dir, "json")
        os.makedirs(json_dir, exist_ok=True)
        json_results = json_exporter.export_sections_to_json(data, json_dir)
        results["json"] = json_results

    # Export au format CSV
    if "csv" in formats:
        csv_dir = os.path.join(output_dir, "csv")
        os.makedirs(csv_dir, exist_ok=True)
        csv_results = csv_exporter.export_to_csv_files(data, csv_dir)
        results["csv"] = csv_results

    return results


if __name__ == "__main__":
    main()
