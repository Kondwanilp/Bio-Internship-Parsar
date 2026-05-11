"""
Google Sheets updater.
Appends new internship listings without overwriting existing ones.
Preserves timestamps of when each job was first discovered.
"""

import os
import json
import logging
from datetime import datetime

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

log = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

SPREADSHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")

HEADERS = [
    "Job Title",
    "Company",
    "Location",
    "Source",
    "Date Posted",
    "Date Scraped",
    "Application Link",
    "Description Snippet",
    "Internship Type",
    "Deadline",
]


def get_service():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
    if not creds_json:
        raise EnvironmentError(
            "GOOGLE_CREDENTIALS_JSON environment variable not set. "
            "Add your service account JSON as a GitHub Secret."
        )
    creds_data = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def ensure_header(service, sheet_name="Internships"):
    """Make sure the header row exists. If sheet is empty, write it."""
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A1:Z1")
        .execute()
    )
    existing = result.get("values", [])
    if not existing or existing[0] != HEADERS:
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A1",
            valueInputOption="RAW",
            body={"values": [HEADERS]},
        ).execute()
        log.info("Header row written.")


def get_existing_links(service, sheet_name="Internships"):
    """Fetch all existing application links to avoid duplicates."""
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!G:G")
        .execute()
    )
    rows = result.get("values", [])
    return {row[0].strip() for row in rows if row}


def update_sheet(jobs: list, sheet_name: str = "Internships"):
    service = get_service()
    ensure_header(service, sheet_name)

    existing_links = get_existing_links(service, sheet_name)
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    new_rows = []
    for job in jobs:
        link = job.get("link", "").strip()
        if link and link in existing_links:
            continue  # already recorded

        row = [
            job.get("title", "N/A"),
            job.get("company", "N/A"),
            job.get("location", "N/A"),
            job.get("source", "N/A"),
            job.get("date_posted", "Unknown"),
            now_str,
            link or "N/A",
            job.get("description", "")[:300],  # cap snippet at 300 chars
            job.get("internship_type", "Internship"),
            job.get("deadline", "N/A"),
        ]
        new_rows.append(row)
        if link:
            existing_links.add(link)  # prevent intra-run dupes

    if new_rows:
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": new_rows},
        ).execute()
        log.info(f"Appended {len(new_rows)} new job(s) to Google Sheets.")
    else:
        log.info("No new jobs to append (all already recorded).")
