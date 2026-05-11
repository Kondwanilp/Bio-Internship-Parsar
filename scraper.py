"""
Bio/Pharma/Research Internship Parser
Runs hourly via GitHub Actions. Scrapes LinkedIn, Indeed, Glassdoor,
Handshake, and company career pages. Writes to Google Sheets.
"""

import os
import time
import logging
from datetime import datetime

from scrapers.linkedin import scrape_linkedin
from scrapers.indeed import scrape_indeed
from scrapers.glassdoor import scrape_glassdoor
from scrapers.handshake import scrape_handshake
from scrapers.company_pages import scrape_company_pages
from sheets import update_sheet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

SEARCH_TERMS = [
    "biotechnology internship",
    "pharmaceutical internship",
    "biomedical research internship",
    "molecular biology internship",
    "biochemistry internship",
    "clinical research internship",
    "drug discovery internship",
    "bioinformatics internship",
    "genomics internship",
    "cell biology internship",
    "toxicology internship",
    "bioanalytical internship",
    "ADME internship",
    "wet lab internship",
    "research scientist internship",
]


def run():
    log.info("=== Internship Parser Started ===")
    all_jobs = []

    scrapers = [
        ("LinkedIn",        scrape_linkedin),
        ("Indeed",          scrape_indeed),
        ("Glassdoor",       scrape_glassdoor),
        ("Handshake",       scrape_handshake),
        ("Company Pages",   scrape_company_pages),
    ]

    for name, fn in scrapers:
        log.info(f"Scraping {name}...")
        try:
            jobs = fn(SEARCH_TERMS)
            log.info(f"  -> {len(jobs)} jobs found on {name}")
            all_jobs.extend(jobs)
        except Exception as e:
            log.error(f"  -> {name} failed: {e}")
        time.sleep(3)  # polite delay between sources

    # Deduplicate by (title + company + source)
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = (
            job.get("title", "").lower().strip(),
            job.get("company", "").lower().strip(),
            job.get("source", "").lower().strip(),
        )
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    log.info(f"Total unique internships found: {len(unique_jobs)}")

    if unique_jobs:
        update_sheet(unique_jobs)
        log.info("Google Sheets updated successfully.")
    else:
        log.warning("No jobs found this run.")

    log.info("=== Parser Complete ===")


if __name__ == "__main__":
    run()
