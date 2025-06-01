import os
import re
import requests
import numpy as np
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional


def get_summary_params(text: str) -> Dict[str, int]:
    """Adaptive parameters based on input length"""

    text_word_count = len(text.split())
    if text_word_count <= 10:  # Very short texts
        return {"min_length": 3, "max_length": 8}
    elif text_word_count <= 50:  # Short-medium texts
        return {"min_length": 8, "max_length": 25}
    elif text_word_count <= 100:  # Medium-long texts
        return {"min_length": 15, "max_length": 40}
    else:  # Very long texts
        return {"min_length": 20, "max_length": 60}

def replace_indication_placeholder(text: str, substitute:str) -> str:
  """
  Replaces 'XXXX' in the indication string with a custom string.

  Args:
      text (str): The original text string which might contain 'XXXX'.
      substitute (str): The string to replace 'XXXX' with.

  Returns:
      str: The updated indication string with 'XXXX' replaced.
  """
  return re.sub(r'XXXX', substitute, str(text), flags=re.IGNORECASE)

def aggregate_chexpert_predictions(chex_preds_list: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Aggregates a list of CheXpert prediction dictionaries by averaging the scores for each pathology.

    Args:
        chex_preds_list (list): A list of dictionaries, where each dictionary
                                 contains pathology names as keys and prediction scores as values.

    Returns:
        dict: A dictionary with aggregated (averaged) scores for each pathology.
              Returns an empty dictionary if the input list is empty or None.
    """
    if not chex_preds_list:
        return {}

    # Initialize a dictionary to store the sum of scores for each pathology
    sum_of_scores = {}
    # Initialize a dictionary to store the count of valid scores for each pathology
    count_of_scores = {}

    for predictions in chex_preds_list:
        for pathology, score in predictions.items():
            if pathology not in sum_of_scores:
                sum_of_scores[pathology] = 0.0
                count_of_scores[pathology] = 0

            # Only add if the score is a valid number (not None, NaN, etc.)
            if isinstance(score, (int, float)) and not np.isnan(score):
                 sum_of_scores[pathology] += score
                 count_of_scores[pathology] += 1

    # Calculate the average score for each pathology
    aggregated_predictions = {}
    for pathology, total_score in sum_of_scores.items():
        if count_of_scores[pathology] > 0:
            aggregated_predictions[pathology] = total_score / count_of_scores[pathology]
        else:
            # If no valid scores for a pathology, you might want to assign a default (e.g., 0 or NaN)
            aggregated_predictions[pathology] = 0.0 # or np.nan

    return aggregated_predictions

def chexpert_preds_to_text(predictions: Dict[str, float], threshold :int = 0.8) -> str:
    """Converts CheXpert probability predictions to text findings based on a threshold."""
    findings = []
    for pathology, score in predictions.items():
        if score >= threshold:
            # Basic text conversion - could be more sophisticated
            findings.append(f"{pathology.replace('_', ' ').lower()}")
    if not findings:
        return ""
    return ", ".join(findings[:-1]) + "and" + findings[-1]

def get_largest_image(image_paths: List[str]) -> Optional[str]:
    """Finds the image with the largest file size among the given paths."""
    largest_path = None
    largest_size = -1
    for path in image_paths:
        if os.path.exists(path):
            size = os.path.getsize(path)
            if size > largest_size:
                largest_size = size
                largest_path = path
    return largest_path

def get_medical_studies(query_text: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Fetches medical studies from PubMed based on a search query.
    Args:
        query_text (str): The search term to query PubMed.
        max_results (int): Maximum number of results to return. Defaults to 5.
    Returns:
        List[Dict[str, str]]: A list of dictionaries containing study details like title, authors, abstract, and link.
    """

    # Step 1: Search PubMed for relevant article IDs
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": query_text,
        "retmode": "xml",
        "retmax": max_results
    }

    search_resp = requests.get(search_url, params=search_params)
    search_tree = ET.fromstring(search_resp.text)
    ids = [id_elem.text for id_elem in search_tree.findall(".//Id")]

    if not ids:
        return []

    # Step 2: Fetch article details
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    fetch_params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "xml"
    }

    fetch_resp = requests.get(fetch_url, params=fetch_params)
    fetch_tree = ET.fromstring(fetch_resp.text)

    results = []
    for article in fetch_tree.findall(".//PubmedArticle"):
        title_elem = article.find(".//ArticleTitle")
        abstract_elem = article.find(".//AbstractText")
        authors = article.findall(".//Author")
        author_names = []
        for author in authors:
            last = author.find("LastName")
            fore = author.find("ForeName")
            if last is not None and fore is not None:
                author_names.append(f"{fore.text} {last.text}")
        title = title_elem.text if title_elem is not None else "No title"
        abstract = abstract_elem.text if abstract_elem is not None else "No abstract available"
        pubmed_id = article.find(".//PMID").text
        results.append({
            "title": title,
            "authors": author_names[:3],  # just top 3 authors
            "abstract": abstract,
            "link": f"https://pubmed.ncbi.nlm.nih.gov/{pubmed_id}/"
        })

    return results