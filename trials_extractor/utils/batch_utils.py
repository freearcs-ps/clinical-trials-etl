"""
Utilitaires pour le traitement par lots des fichiers HTML.
"""

import logging
import os
import concurrent.futures
from functools import partial
from clinical_trials_extractor.config.settings import BATCH_PROCESSING
from clinical_trials_extractor.utils.logging_utils import ProgressLogger

logger = logging.getLogger(__name__)

def process_batch(files, process_function, output_dir, options=None):
    """
    Traite un lot de fichiers HTML en parallèle.
    
    Args:
        files (list): Liste des chemins de fichiers à traiter
        process_function (callable): Fonction de traitement à appliquer à chaque fichier
        output_dir (str): Répertoire de sortie
        options (dict): Options de traitement
        
    Returns:
        list: Liste des résultats pour chaque fichier
    """
    if not files:
        logger.warning("Aucun fichier à traiter")
        return []
    
    if options is None:
        options = {}
    
    # Création du répertoire de sortie
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialisation du logger de progression
    progress = ProgressLogger(len(files), "Traitement par lots")
    
    # Fonction partielle avec les arguments communs
    process_func = partial(process_file_wrapper, process_function, output_dir, options, progress)
    
    # Traitement parallèle
    results = []
    max_workers = min(BATCH_PROCESSING['max_workers'], len(files))
    
    logger.info(f"Démarrage du traitement par lots avec {max_workers} workers")
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Soumission des tâches
        future_to_file = {executor.submit(process_func, file): file for file in files}
        
        # Récupération des résultats
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Erreur lors du traitement du fichier {file}: {str(e)}")
                results.append({
                    "file": file,
                    "success": False,
                    "error": str(e)
                })
    
    # Calcul des statistiques
    success_count = sum(1 for r in results if r.get("success", False))
    progress.complete(success_count)
    
    return results

def process_file_wrapper(process_function, output_dir, options, progress, file):
    """
    Wrapper pour le traitement d'un fichier individuel.
    
    Args:
        process_function (callable): Fonction de traitement
        output_dir (str): Répertoire de sortie
        options (dict): Options de traitement
        progress (ProgressLogger): Logger de progression
        file (str): Chemin du fichier à traiter
        
    Returns:
        dict: Résultat du traitement
    """
    try:
        # Création d'un sous-répertoire pour chaque fichier
        file_name = os.path.basename(file)
        file_base_name = os.path.splitext(file_name)[0]
        file_output_dir = os.path.join(output_dir, file_base_name)
        
        # Traitement du fichier
        result = process_function(file, file_output_dir, options)
        
        # Mise à jour de la progression
        progress.update()
        
        return {
            "file": file,
            "success": True,
            "output_dir": file_output_dir,
            **result
        }
    except Exception as e:
        logger.error(f"Erreur lors du traitement du fichier {file}: {str(e)}")
        progress.update()
        return {
            "file": file,
            "success": False,
            "error": str(e)
        }

def chunk_list(lst, chunk_size):
    """
    Divise une liste en chunks de taille spécifiée.
    
    Args:
        lst (list): Liste à diviser
        chunk_size (int): Taille des chunks
        
    Returns:
        list: Liste de chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def find_html_files(directory):
    """
    Trouve tous les fichiers HTML dans un répertoire.
    
    Args:
        directory (str): Répertoire à explorer
        
    Returns:
        list: Liste des chemins de fichiers HTML
    """
    html_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.html'):
                html_files.append(os.path.join(root, file))
    
    return html_files