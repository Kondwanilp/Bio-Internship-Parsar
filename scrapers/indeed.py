"""
Adzuna API scraper - replaces direct Indeed scraping.
Adzuna aggregates from Indeed, Glassdoor, and 100+ job boards.
Free tier: 250 calls/month. Sign up at https://developer.adzuna.com/
 
Requires two GitHub Secrets:
  ADZUNA_APP_ID   - your app ID from the Adzuna developer dashboard
  ADZUNA_API_KEY  - your API key from the Adzuna developer dashboard
"""
 
import os
import time
import logging
import requests
from datetime import datetime
 
log = logging.getLogger(__name__)
 
APP_ID  = os.environ.get("ADZUNA_APP_ID", "")
API_KEY = os.environ.get("ADZUNA_API_KEY", "")
 
BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search/1"
 
BIO_KEYWORDS = [
    "biotechnology intern",
    "pharmaceutical intern",
    "molecular biology intern",
    "biochemistry intern",
    "clinical research intern",
    "bioinformatics intern",
    "cell biology intern",
    "toxicology intern",
    "ADME intern",
    "wet lab intern",
]
 
 
def scrape_indeed(search_terms: list) -> list:
    """
    Parameter name kept as scrape_indeed so scraper.py needs no changes.
    Actually queries Adzuna, which includes Indeed + Glassdoor + more.
    """
    if not APP_ID or not API_KEY:
        log.warning(
            "ADZUNA_APP_ID or ADZUNA_API_KEY not set. "
            "Skipping Adzuna. See scrapers/indeed.py for setup instructions."
        )
        return []
 
    jobs = []
    terms_to_use = BIO_KEYWORDS[:8]  # Stay well within free tier
 
    for term in terms_to_use:
        try:
            params = {
                "app_id": APP_ID,
                "app_key": API_KEY,
                "what": term,
                "what_and": "intern",
                "category": "science-quality-jobs",
                "results_per_page": 20,
                "sort_by": "date",
                "max_days_old": 7,
                "content-type": "application/json",
            }
 
            resp = requests.get(BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
 
            for item in data.get("results", []):
                title = item.get("title", "N/A")
                if not _is_internship(title):
                    continue
 
                company     = item.get("company", {}).get("display_name", "N/A")
                location    = item.get("location", {}).get("display_name", "N/A")
                link        = item.get("redirect_url", "")
                created     = item.get("created", "")
                description = item.get("description", "")[:300]
 
                date_posted = "Unknown"
                if created:
                    try:
                        date_posted = datetime.fromisoformat(
                            created.replace("Z", "+00:00")
                        ).strftime("%Y-%m-%d")
                    except Exception:
                        date_posted = created[:10]
 
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "source": "Adzuna (Indeed/Glassdoor/+)",
                    "date_posted": date_posted,
                    "link": link,
                    "description": description,
                    "internship_type": "Internship",
                    "deadline": "N/A",
                })
 
            log.info(f"  Adzuna '{term}': {len(data.get('results', []))} results")
            time.sleep(1.5)
 
        except Exception as e:
            log.error(f"Adzuna scrape error for '{term}': {e}")
 
    return jobs
 
 
def _is_internship(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in ["intern", "internship", "co-op", "coop"])
