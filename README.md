# WineSync

Automatically extracts wine orders from Gmail and syncs them to Google Sheets.

## How it works

1. Connects to Gmail via IMAP
2. Filters emails from known wine merchants (configurable in `config.py`)
3. Sends email content to Claude LLM to detect real wine orders and extract details
4. Appends extracted wines to a Google Sheet

## Project structure

```
winesync/
├── main.py                 # Entry point
├── config.py               # All configuration (credentials, merchant list)
├── services/
│   ├── gmail_client.py     # IMAP connection and email fetching
│   ├── wine_detector.py    # Pre-filtering + LLM orchestration
│   ├── llm_extractor.py    # Claude API calls for wine extraction
│   ├── pdf_parser.py       # PDF attachment parsing
│   └── sheets_client.py    # Google Sheets export
└── utils/
    └── logger.py           # Logging setup
```

## Setup

### 1. Install dependencies

```
pip install -r requirements.txt
```

### 2. Gmail App Password

Go to [Google Account Security](https://myaccount.google.com/security) → 2-Step Verification → App passwords → Generate one for "Mail".

### 3. Anthropic API Key

Get one at [console.anthropic.com](https://console.anthropic.com/)

### 4. Google Sheets API

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Google Sheets API
3. Create a Service Account and download the JSON key
4. Share your target spreadsheet with the service account email (found in the JSON)

### 5. Configure `config.py`

```python
GMAIL_EMAIL = "your.email@gmail.com"
GMAIL_PASSWORD = "your_app_password"
ANTHROPIC_API_KEY = "sk-ant-..."
GOOGLE_SHEET_ID = "your_sheet_id"  # From the spreadsheet URL
GOOGLE_SHEET_WORKSHEET = "Sheet1"
GOOGLE_SERVICE_ACCOUNT_FILE = "path/to/service_account.json"
WINE_MERCHANT_DOMAINS = ["vinatis.com", "millesima.com", ...]
```

## Run

```
python main.py
```

Wines are appended to your sheet with (very French) columns: Région, AOC, Producteur, Millésime, Cuvée, Format.

## Notes

- The LLM (Claude) decides whether an email is a real wine order (vs newsletters/promos)
- PDF attachments are parsed if they look like wine invoices
- Only emails from domains in `WINE_MERCHANT_DOMAINS` are processed
