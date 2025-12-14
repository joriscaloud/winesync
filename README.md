# WineSync

Automatically extracts wine orders from Gmail and syncs them to Google Sheets.

## How it works

1. Connects to Gmail via IMAP
2. Filters emails from known wine merchants (configurable in `config.py`)
3. Sends email content to Claude LLM to detect wine orders and extract details
4. Appends extracted wines to a Google Sheet

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Configure `config.py`:
   - `GMAIL_EMAIL` / `GMAIL_PASSWORD` – Gmail credentials (use an App Password)
   - `ANTHROPIC_API_KEY` – Claude API key
   - `GOOGLE_SHEET_ID` – Target spreadsheet ID
   - `GOOGLE_SERVICE_ACCOUNT_FILE` – Path to service account JSON
   - `WINE_MERCHANT_DOMAINS` – List of wine merchant email domains to scan

3. Share your Google Sheet with the service account email (found in the JSON file)

## Run

```
python main.py
```

Wines are appended to your sheet with (very french) columns: Région, AOC, Producteur, Millésime, Cuvée, Format.
