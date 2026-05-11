"""
Direct career page scraper for major biotech/pharma/research companies.
Targets internship listings on company-hosted career portals.
Each company function handles its own HTML structure.
"""

import time
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

TODAY = datetime.utcnow().strftime("%Y-%m-%d")

# ── Company scrapers ──────────────────────────────────────────────────────────

def _genentech(session):
    """Genentech / Roche careers (via Roche workday)"""
    jobs = []
    try:
        url = "https://www.roche.com/careers/jobs.htm#category=Internship&country=US"
        resp = session.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select("div.job-card, article.job-listing"):
            title = card.select_one("h3, h2, .job-title")
            location = card.select_one(".location, .job-location")
            link = card.select_one("a")
            if title:
                jobs.append(_build(
                    title.get_text(strip=True),
                    "Genentech / Roche",
                    location.get_text(strip=True) if location else "N/A",
                    link.get("href", "") if link else "",
                    "Genentech Careers",
                ))
    except Exception as e:
        log.debug(f"Genentech scrape error: {e}")
    return jobs


def _pfizer(session):
    """Pfizer careers JSON endpoint"""
    jobs = []
    try:
        url = "https://www.pfizer.com/api/careers/search?keywords=intern&country=US&category=internship"
        resp = session.get(url, timeout=15)
        if resp.ok:
            data = resp.json()
            for item in data.get("jobs", data.get("results", [])):
                title = item.get("title", item.get("jobTitle", "N/A"))
                if not _is_internship(title):
                    continue
                jobs.append(_build(
                    title,
                    "Pfizer",
                    item.get("location", item.get("city", "N/A")),
                    item.get("applyUrl", item.get("url", "")),
                    "Pfizer Careers",
                    date_posted=item.get("postedDate", TODAY),
                ))
        else:
            # HTML fallback
            url2 = "https://www.pfizer.com/careers/search-jobs?keywords=internship"
            resp2 = session.get(url2, timeout=15)
            soup = BeautifulSoup(resp2.text, "html.parser")
            for card in soup.select(".job-result, .search-result"):
                title = card.select_one("h2, h3, .job-title")
                location = card.select_one(".location")
                link = card.select_one("a")
                if title and _is_internship(title.get_text()):
                    jobs.append(_build(
                        title.get_text(strip=True), "Pfizer",
                        location.get_text(strip=True) if location else "N/A",
                        link.get("href", "") if link else "",
                        "Pfizer Careers",
                    ))
    except Exception as e:
        log.debug(f"Pfizer scrape error: {e}")
    return jobs


def _abbvie(session):
    jobs = []
    try:
        url = "https://careers.abbvie.com/jobs?keywords=intern&location=United+States&country=US&jobtype=Intern"
        resp = session.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select("div.search-result-item, li.job-tile"):
            title = card.select_one("h2, h3, .job-title, a")
            location = card.select_one(".location, .job-location")
            link = card.select_one("a")
            if title and _is_internship(title.get_text()):
                href = link.get("href", "") if link else ""
                if href.startswith("/"):
                    href = "https://careers.abbvie.com" + href
                jobs.append(_build(
                    title.get_text(strip=True), "AbbVie",
                    location.get_text(strip=True) if location else "N/A",
                    href, "AbbVie Careers",
                ))
    except Exception as e:
        log.debug(f"AbbVie scrape error: {e}")
    return jobs


def _biogen(session):
    jobs = []
    try:
        url = "https://www.biogen.com/en_us/careers/find-a-job.html#q=intern&t=Jobs"
        resp = session.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select(".coveo-result-frame, .CoveoResult"):
            title = card.select_one("h3, h2, .coveo-title, a")
            location = card.select_one(".location, .coveo-field-worklocation")
            link = card.select_one("a")
            if title and _is_internship(title.get_text()):
                jobs.append(_build(
                    title.get_text(strip=True), "Biogen",
                    location.get_text(strip=True) if location else "N/A",
                    link.get("href", "") if link else "",
                    "Biogen Careers",
                ))
    except Exception as e:
        log.debug(f"Biogen scrape error: {e}")
    return jobs


def _amgen(session):
    jobs = []
    try:
        url = "https://careers.amgen.com/en/search#q=intern&t=Jobs"
        resp = session.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select(".CoveoResult, article.job"):
            title = card.select_one("h3, h2, .coveo-title")
            location = card.select_one(".location, [class*='location']")
            link = card.select_one("a")
            if title and _is_internship(title.get_text()):
                href = link.get("href", "") if link else ""
                if href.startswith("/"):
                    href = "https://careers.amgen.com" + href
                jobs.append(_build(
                    title.get_text(strip=True), "Amgen",
                    location.get_text(strip=True) if location else "N/A",
                    href, "Amgen Careers",
                ))
    except Exception as e:
        log.debug(f"Amgen scrape error: {e}")
    return jobs


def _merck(session):
    jobs = []
    try:
        # Merck uses Workday
        url = "https://jobs.merck.com/us/en/search-results?keywords=intern"
        resp = session.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select("li.job-tile, div.job-card"):
            title = card.select_one("h3, h2, a[data-ph-at-job-title-text]")
            location = card.select_one("span[data-ph-at-job-location-text], .location")
            link = card.select_one("a")
            if title and _is_internship(title.get_text()):
                href = link.get("href", "") if link else ""
                if href.startswith("/"):
                    href = "https://jobs.merck.com" + href
                jobs.append(_build(
                    title.get_text(strip=True), "Merck",
                    location.get_text(strip=True) if location else "N/A",
                    href, "Merck Careers",
                ))
    except Exception as e:
        log.debug(f"Merck scrape error: {e}")
    return jobs


def _novartis(session):
    jobs = []
    try:
        url = "https://www.novartis.com/careers/career-search?search=intern&country=United+States"
        resp = session.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select(".job-item, .career-listing-item"):
            title = card.select_one("h3, h2, .job-title")
            location = card.select_one(".location, .job-location")
            link = card.select_one("a")
            if title and _is_internship(title.get_text()):
                href = link.get("href", "") if link else ""
                if href.startswith("/"):
                    href = "https://www.novartis.com" + href
                jobs.append(_build(
                    title.get_text(strip=True), "Novartis",
                    location.get_text(strip=True) if location else "N/A",
                    href, "Novartis Careers",
                ))
    except Exception as e:
        log.debug(f"Novartis scrape error: {e}")
    return jobs


def _biorad(session):
    jobs = []
    try:
        url = "https://www.bio-rad.com/en-us/careers/search-jobs?keywords=intern"
        resp = session.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select(".job-result, .search-result-item, li.job"):
            title = card.select_one("h2, h3, a")
            location = card.select_one(".location")
            link = card.select_one("a")
            if title and _is_internship(title.get_text()):
                href = link.get("href", "") if link else ""
                if href.startswith("/"):
                    href = "https://www.bio-rad.com" + href
                jobs.append(_build(
                    title.get_text(strip=True), "Bio-Rad",
                    location.get_text(strip=True) if location else "N/A",
                    href, "Bio-Rad Careers",
                ))
    except Exception as e:
        log.debug(f"Bio-Rad scrape error: {e}")
    return jobs


def _charles_river(session):
    jobs = []
    try:
        url = "https://www.criver.com/careers/search-jobs?keywords=intern"
        resp = session.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select(".job-result, .job-item, li.job"):
            title = card.select_one("h2, h3, a")
            location = card.select_one(".location")
            link = card.select_one("a")
            if title and _is_internship(title.get_text()):
                href = link.get("href", "") if link else ""
                if href.startswith("/"):
                    href = "https://www.criver.com" + href
                jobs.append(_build(
                    title.get_text(strip=True), "Charles River Laboratories",
                    location.get_text(strip=True) if location else "N/A",
                    href, "Charles River Careers",
                ))
    except Exception as e:
        log.debug(f"Charles River scrape error: {e}")
    return jobs


def _iqvia(session):
    jobs = []
    try:
        url = "https://jobs.iqvia.com/search-jobs?keyword=intern&country=United+States"
        resp = session.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select("li.job-tile, div.job-tile"):
            title = card.select_one("h2, h3, a[data-ph-at-job-title-text]")
            location = card.select_one("span.job-location, .location")
            link = card.select_one("a")
            if title and _is_internship(title.get_text()):
                href = link.get("href", "") if link else ""
                if href.startswith("/"):
                    href = "https://jobs.iqvia.com" + href
                jobs.append(_build(
                    title.get_text(strip=True), "IQVIA",
                    location.get_text(strip=True) if location else "N/A",
                    href, "IQVIA Careers",
                ))
    except Exception as e:
        log.debug(f"IQVIA scrape error: {e}")
    return jobs


def _labcorp(session):
    jobs = []
    try:
        url = "https://careers.labcorp.com/global/en/search-results?keywords=intern"
        resp = session.get(url, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for card in soup.select("li.job-tile, .job-result"):
            title = card.select_one("h3, h2, a")
            location = card.select_one(".location, [data-ph-at-job-location-text]")
            link = card.select_one("a")
            if title and _is_internship(title.get_text()):
                href = link.get("href", "") if link else ""
                if href.startswith("/"):
                    href = "https://careers.labcorp.com" + href
                jobs.append(_build(
                    title.get_text(strip=True), "Labcorp",
                    location.get_text(strip=True) if location else "N/A",
                    href, "Labcorp Careers",
                ))
    except Exception as e:
        log.debug(f"Labcorp scrape error: {e}")
    return jobs


# ── Orchestrator ──────────────────────────────────────────────────────────────

COMPANY_SCRAPERS = [
    _genentech,
    _pfizer,
    _abbvie,
    _biogen,
    _amgen,
    _merck,
    _novartis,
    _biorad,
    _charles_river,
    _iqvia,
    _labcorp,
]


def scrape_company_pages(search_terms: list) -> list:
    """search_terms unused here; each company function targets its own URL."""
    jobs = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for fn in COMPANY_SCRAPERS:
        try:
            result = fn(session)
            log.info(f"  {fn.__name__}: {len(result)} listings")
            jobs.extend(result)
        except Exception as e:
            log.error(f"  {fn.__name__} failed: {e}")
        time.sleep(1.5)

    return jobs


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build(title, company, location, link, source, date_posted=None, deadline="N/A"):
    return {
        "title": title,
        "company": company,
        "location": location,
        "source": source,
        "date_posted": date_posted or TODAY,
        "link": link,
        "description": "",
        "internship_type": "Internship",
        "deadline": deadline,
    }


def _is_internship(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in ["intern", "internship", "co-op", "coop"])
