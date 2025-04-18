import requests
import xml.etree.ElementTree as ET

def fetch_medical_studies(query_text: str, max_results: int = 5):
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


studies = fetch_medical_studies("pulmonary fibrosis CT scan", max_results=3)
for study in studies:
    print(f"Title: {study['title']}")
    print(f"Authors: {', '.join(study['authors'])}")
    print(f"Link: {study['link']}\n")