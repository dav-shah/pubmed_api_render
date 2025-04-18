import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=".env")

API_KEY = os.getenv("ELSEVIER_API_KEY")
BASE_URL = "https://api.elsevier.com/content/search/scopus"

def search_scopus(query: str, count: int = 10, start: int = 0):
    headers = {
        "X-ELS-APIKey": API_KEY,
        "Accept": "application/json"
    }
    params = {
        "query": query,
        "count": count,
        "start": start
    }
    response = requests.get(BASE_URL, headers=headers, params=params)
    response.raise_for_status()
    return parse_scopus_results(response.json())

def parse_scopus_results(data):
    entries = data.get("search-results", {}).get("entry", [])
    parsed = []

    for entry in entries:
        parsed.append({
            "source": "scopus",
            "title": entry.get("dc:title"),
            "doi": entry.get("prism:doi"),
            "authors": entry.get("dc:creator"),  # optional: split into list if comma-separated
            "journal": entry.get("prism:publicationName"),
            "publication_date": entry.get("prism:coverDate"),
            "url": entry.get("prism:url"),  # Scopus API link
            "eid": entry.get("eid"),
            "openaccess": entry.get("openaccessFlag"),
            "link_to_scopus": next((link["@href"] for link in entry.get("link", []) if link.get("@ref") == "scopus"), None),
            "link_to_citedby": next((link["@href"] for link in entry.get("link", []) if link.get("@ref") == "scopus-citedby"), None),
            "link_to_fulltext": next((link["@href"] for link in entry.get("link", []) if link.get("@ref") == "full-text"), None),
        })

    return parsed

def fetch_full_text_by_doi(doi: str, para_start: int = 1, para_end: int = None):
    headers = {
        "X-ELS-APIKey": API_KEY,
        "Accept": "application/json"
    }
    url = f"https://api.elsevier.com/content/article/doi/{doi}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        original_text = data.get("full-text-retrieval-response", {}).get("originalText", "")
        if not original_text:
            return {"error": "Full text not available. This may be due to access restrictions."}

        # Split into chunks by paragraph (or double line break)
        paragraphs = [p.strip() for p in original_text.split("\n\n") if p.strip()]
        total_paragraphs = len(paragraphs)

        start = max(para_start - 1, 0)
        end = min(para_end, total_paragraphs) if para_end else total_paragraphs
        selected = paragraphs[start:end]

        return {
            "doi": doi,
            "total_paragraphs": total_paragraphs,
            "range": [start + 1, end],
            "paragraphs": selected
        }

    except Exception as e:
        # Handle large response error or other issues
        fallback_response = {
            "doi": doi,
            "warning": "Full text may be too large to retrieve in one request.",
            "suggestion": "Try using smaller ranges with para_start and para_end (e.g., 1–5).",
            "error_detail": str(e)
        }

        # Attempt to return just the first paragraph if possible
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            original_text = data.get("full-text-retrieval-response", {}).get("originalText", "")
            paragraphs = [p.strip() for p in original_text.split("\n\n") if p.strip()]
            if paragraphs:
                fallback_response["first_paragraph"] = paragraphs[0]
        except:
            fallback_response["first_paragraph"] = None

        return fallback_response
        
def search_sciencedirect(query: str, count: int = 10, start: int = 0):
    headers = {
        "X-ELS-APIKey": API_KEY,
        "Accept": "application/json"
    }
    url = "https://api.elsevier.com/content/search/sciencedirect"
    params = {
        "query": query,
        "count": count,
        "start": start
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return parse_sciencedirect_results(response.json())

def parse_sciencedirect_results(data):
    entries = data.get("search-results", {}).get("entry", [])
    parsed = []

    for entry in entries:
        parsed.append({
            "source": "sciencedirect",
            "title": entry.get("dc:title"),
            "doi": entry.get("prism:doi"),
            "authors": entry.get("dc:creator"),
            "journal": entry.get("prism:publicationName"),
            "publication_date": entry.get("prism:coverDate"),
            "url": entry.get("prism:url"),
            "eid": entry.get("eid"),
            "openaccess": entry.get("openaccessFlag"),
            "link_to_fulltext": next((link["@href"] for link in entry.get("link", []) if link.get("@ref") == "full-text"), None)
        })

    return parsed