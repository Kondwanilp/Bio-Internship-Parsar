"""
Glassdoor internship scraper.
Targets the public job listings search endpoint.
"""

import time
import logging
import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.glassdoor.com/",
}

BASE_URL = "https://www.glassdoor.com/Job/jobs.htm"


def scrape_glassdoor(search_terms: list) -> list:
    jobs = []
    terms_to_use = search_terms[:4]

    for term in terms_to_use:
        try:
            params = {
                "sc.keyword": term,
                "jobType": "internship",
                "fromAge": 1,
                "sort.sortType": "date",
                "sort.descending": "true",
            }
            resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            cards = soup.select("li.react-job-listing")
            for card in cards:
                try:
                    title_el = card.select_one("a.jobLink span")
                    company_el = card.select_one("div.jobHeader a.jobLink")
                    location_el = card.select_one("span.loc")
                    date_el = card.select_one("div.listing-age")
                    link_el = card.select_one("a.jobLink")

                    title = title_el.get_text(strip=True) if title_el else "N/A"
                    company = company_el.get_text(strip=True) if company_el else "N/A"
                    location = location_el.get_text(strip=True) if location_el else "N/A"
                    date_posted = date_el.get_text(strip=True) if date_el else "Unknown"
                    href = link_el.get("href", "") if link_el else ""
                    link = f"https://www.glassdoor.com{href}" if href.startswith("/") else href

                    if not _is_internship(title):
                        continue

                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "source": "Glassdoor",
                        "date_posted": date_posted,
                        "link": link,
                        "description": "",
                        "internship_type": "Internship",
                        "deadline": "N/A",
                    })
                except Exception as e:
                    log.debug(f"Glassdoor card parse error: {e}")

            time.sleep(2)

        except Exception as e:
            log.error(f"Glassdoor scrape error for '{term}': {e}")

    return jobs


def _is_internship(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in ["intern", "internship", "co-op", "coop"])
