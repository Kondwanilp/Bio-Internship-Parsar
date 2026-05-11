"""
Indeed internship scraper.
Uses public search results page with internship job type filter.
"""

import time
import logging
import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

BASE_URL = "https://www.indeed.com/jobs"


def scrape_indeed(search_terms: list) -> list:
    jobs = []
    terms_to_use = search_terms[:5]

    for term in terms_to_use:
        try:
            params = {
                "q": term,
                "jt": "internship",
                "fromage": "1",   # Posted in last 1 day
                "sort": "date",
            }
            resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            cards = soup.select("div.job_seen_beacon")
            for card in cards:
                try:
                    title_el = card.select_one("h2.jobTitle span[title]")
                    company_el = card.select_one("span.companyName")
                    location_el = card.select_one("div.companyLocation")
                    date_el = card.select_one("span.date")
                    link_el = card.select_one("a[data-jk]")

                    title = title_el.get("title", "N/A") if title_el else "N/A"
                    company = company_el.get_text(strip=True) if company_el else "N/A"
                    location = location_el.get_text(strip=True) if location_el else "N/A"
                    date_posted = date_el.get_text(strip=True) if date_el else "Unknown"
                    jk = link_el.get("data-jk", "") if link_el else ""
                    link = f"https://www.indeed.com/viewjob?jk={jk}" if jk else ""

                    if not _is_internship(title):
                        continue

                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "source": "Indeed",
                        "date_posted": date_posted,
                        "link": link,
                        "description": "",
                        "internship_type": "Internship",
                        "deadline": "N/A",
                    })
                except Exception as e:
                    log.debug(f"Indeed card parse error: {e}")

            time.sleep(2)

        except Exception as e:
            log.error(f"Indeed scrape error for '{term}': {e}")

    return jobs


def _is_internship(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in ["intern", "internship", "co-op", "coop"])
