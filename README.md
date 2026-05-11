# Bio/Pharma Internship Parser

Automatically scrapes internship listings from LinkedIn, Indeed, Glassdoor, Handshake, and 10+ company career pages every hour, then writes new listings to a Google Sheet with timestamps.

**Fields logged per listing:**
| Job Title | Company | Location | Source | Date Posted | Date Scraped | Application Link | Description Snippet | Internship Type | Deadline |

---

## Setup (one-time, ~15 minutes)

### Step 1: Fork or clone this repo

Push it to your own GitHub account. The Actions workflow will run from there.

### Step 2: Create a Google Sheet

1. Go to [Google Sheets](https://sheets.google.com) and create a new blank sheet.
2. Name the first tab `Internships` (exact spelling).
3. Copy the Sheet ID from the URL, it looks like this:
   ```
   https://docs.google.com/spreadsheets/d/THIS_PART_HERE/edit
   ```

### Step 3: Set up Google Sheets API access

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (or use an existing one).
3. Enable the **Google Sheets API** (search "Sheets API" in the library).
4. Go to **IAM & Admin > Service Accounts** and create a new service account.
5. Give it any name (e.g., `internship-parser`). No special roles needed.
6. Click on the service account, go to **Keys**, click **Add Key > Create new key > JSON**.
7. Download the JSON file. Keep it safe, it is your credential.
8. Open your Google Sheet and share it with the service account email (looks like `something@project.iam.gserviceaccount.com`) as **Editor**.

### Step 4: Add GitHub Secrets

In your GitHub repo, go to **Settings > Secrets and variables > Actions > New repository secret** and add:

| Secret Name | Value |
|---|---|
| `GOOGLE_CREDENTIALS_JSON` | The entire contents of the JSON file from Step 3 (paste the raw JSON) |
| `GOOGLE_SHEET_ID` | The Sheet ID from Step 2 |
| `HANDSHAKE_COOKIE` | *(Optional)* Your Handshake session cookie for better results (see below) |

### Step 5: Enable GitHub Actions

Go to the **Actions** tab in your repo and enable workflows if prompted. The parser will now run automatically every hour.

To run it immediately: go to **Actions > Internship Parser (Hourly) > Run workflow**.

---

## Optional: Handshake Cookie (Better Results)

Handshake shows more results when logged in. To get your session cookie:

1. Log in to [Handshake](https://app.joinhandshake.com).
2. Open DevTools (F12) > Application > Cookies > `app.joinhandshake.com`.
3. Copy the value of the `_hjsess` or `remember_user_token` cookie.
4. Add it as the `HANDSHAKE_COOKIE` secret.

---

## Customizing Search Terms

Edit the `SEARCH_TERMS` list in `scraper.py` to add or remove keywords. Currently targets:

- biotechnology internship
- pharmaceutical internship
- biomedical research internship
- molecular biology internship
- biochemistry internship
- clinical research internship
- drug discovery internship
- bioinformatics internship
- genomics internship
- cell biology internship
- toxicology internship
- bioanalytical internship
- ADME internship
- wet lab internship
- research scientist internship

## Adding More Companies

To add a company, open `scrapers/company_pages.py` and add a new function following the pattern of existing ones. Then add it to the `COMPANY_SCRAPERS` list at the bottom.

---

## Notes

- The scraper only **appends** new listings. It never deletes or overwrites existing rows.
- Deduplication is handled by application link. Same listing from two sources appears once.
- LinkedIn, Indeed, and Glassdoor are scraped without authentication. Rate limiting is handled with polite delays between requests.
- GitHub Actions free tier gives 2,000 minutes/month. Running hourly uses roughly 750 minutes/month (well within free limits).
- All times are in UTC.
