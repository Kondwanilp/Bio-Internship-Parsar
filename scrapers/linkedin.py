"""
LinkedIn internship scraper using the public jobs search endpoint.
No login required for basic scraping.
"""

import time
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

BASE_URL = "https://www.linkedin.com/jobs/search/"


def scrape_linkedin(search_terms: list) -> list:
    jobs = []
    # Use a focused subset to avoid rate limiting
    terms_to_use = search_terms[:6]

    for term in terms_to_use:
        try:
            params = {
                "keywords": term,
                "f_JT": "I",          # I = Internship job type filter
                "f_TPR": "r86400",    # Posted in last 24 hours
                "sortBy": "DD",       # Most recent first
                "start": 0,
            }
            resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            cards = soup.select("div.base-card")
            for card in cards:
                try:
                    title_el = card.select_one("h3.base-search-card__title")
                    company_el = card.select_one("h4.base-search-card__subtitle a")
                    location_el = card.select_one("span.job-search-card__location")
                    date_el = card.select_one("time")
                    link_el = card.select_one("a.base-card__full-link")

                    title = title_el.get_text(strip=True) if title_el else "N/A"
                    company = company_el.get_text(strip=True) if company_el else "N/A"
                    location = location_el.get_text(strip=True) if location_el else "N/A"
                    date_posted = date_el.get("datetime", "Unknown") if date_el else "Unknown"
                    link = link_el.get("href", "").split("?")[0] if link_el else ""

                    # Filter: must contain internship signals in title
                    if not _is_internship(title):
                        continue

                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "source": "LinkedIn",
                        "date_posted": date_posted,
                        "link": link,
                        "description": "",
                        "internship_type": "Internship",
                        "deadline": "N/A",
                    })
                except Exception as e:
                    log.debug(f"LinkedIn card parse error: {e}")

            time.sleep(2)

        except Exception as e:
            log.error(f"LinkedIn scrape error for '{term}': {e}")

    return jobs


def _is_internship(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in ["intern", "internship", "co-op", "coop"])
