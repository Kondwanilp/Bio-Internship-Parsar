"""
Handshake internship scraper.
Handshake does not have a fully public API, so this scraper targets
the public-facing search page. For best results, a Handshake account
session cookie can be added as a GitHub Secret (HANDSHAKE_COOKIE).
"""

import time
import logging
import os
import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

BASE_URL = "https://app.joinhandshake.com/jobs"
API_URL = "https://app.joinhandshake.com/api/v0/jobs"

BIO_EMPLOYER_TYPES = [
    "Biotechnology",
    "Pharmaceuticals",
    "Research",
    "Healthcare",
    "Medical Devices",
    "Clinical Research",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://app.joinhandshake.com/jobs",
}

cookie = os.environ.get("HANDSHAKE_COOKIE", "")
if cookie:
    HEADERS["Cookie"] = cookie


def scrape_handshake(search_terms: list) -> list:
    jobs = []
    terms_to_use = search_terms[:5]

    for term in terms_to_use:
        try:
            params = {
                "query": term,
                "job_type[]": "internship",
                "per_page": 25,
                "page": 1,
                "sort_direction": "desc",
                "sort_column": "created_at",
            }
            resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)

            # If we get JSON back, parse it
            if "application/json" in resp.headers.get("Content-Type", ""):
                data = resp.json()
                results = data.get("results", data.get("jobs", []))
                for item in results:
                    title = item.get("title", item.get("name", "N/A"))
                    company = item.get("employer_name", item.get("company", {}).get("name", "N/A"))
                    location = item.get("city", "") + (", " + item.get("state", "") if item.get("state") else "")
                    date_posted = item.get("created_at", item.get("posted_at", "Unknown"))
                    job_id = item.get("id", "")
                    link = f"https://app.joinhandshake.com/jobs/{job_id}" if job_id else ""

                    if not _is_internship(title):
                        continue

                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location.strip(", "),
                        "source": "Handshake",
                        "date_posted": date_posted,
                        "link": link,
                        "description": item.get("description", "")[:300],
                        "internship_type": "Internship",
                        "deadline": item.get("apply_end_date", "N/A"),
                    })
            else:
                # Fallback: HTML scrape
                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.select("div[class*='job-card'], li[class*='job-tile']")
                for card in cards:
                    try:
                        title = card.select_one("h3, h2, [class*='title']")
                        company = card.select_one("[class*='company'], [class*='employer']")
                        location = card.select_one("[class*='location']")
                        link_el = card.select_one("a")

                        jobs.append({
                            "title": title.get_text(strip=True) if title else "N/A",
                            "company": company.get_text(strip=True) if company else "N/A",
                            "location": location.get_text(strip=True) if location else "N/A",
                            "source": "Handshake",
                            "date_posted": "Unknown",
                            "link": link_el.get("href", "") if link_el else "",
                            "description": "",
                            "internship_type": "Internship",
                            "deadline": "N/A",
                        })
                    except Exception as e:
                        log.debug(f"Handshake HTML card error: {e}")

            time.sleep(2)

        except Exception as e:
            log.error(f"Handshake scrape error for '{term}': {e}")

    return jobs


def _is_internship(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in ["intern", "internship", "co-op", "coop"])
