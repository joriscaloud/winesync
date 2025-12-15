from typing import List, Dict
from datetime import datetime
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

from utils.logger import logger
import config

LAST_SYNC_FILE = Path(__file__).parent.parent / ".last_sync"


def _normalize_format(format_value: str) -> str:
    """Convert format strings to numeric centimeters (75/150/300)."""
    if not format_value:
        return ""
    fmt = format_value.lower()
    if "jeroboam" in fmt or "300" in fmt:
        return "300"
    if "magnum" in fmt or "150" in fmt or "1.5" in fmt:
        return "150"
    if "75" in fmt:
        return "75"
    return ""


def get_last_sync_date() -> datetime | None:
    """Get the last sync date from file."""
    if not LAST_SYNC_FILE.exists():
        return None
    try:
        return datetime.fromisoformat(LAST_SYNC_FILE.read_text().strip())
    except Exception:
        return None


def save_last_sync_date(date: datetime) -> None:
    """Save the last sync date to file."""
    LAST_SYNC_FILE.write_text(date.isoformat())


def append_wines_to_sheet(wine_orders: List[Dict]) -> None:
    """Append wine rows to the configured Google Sheet."""
    if not wine_orders:
        logger.info("No wine orders to export.")
        return

    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(
            config.GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=scopes,
        )
        client = gspread.authorize(creds)
        worksheet = client.open_by_key(config.GOOGLE_SHEET_ID).worksheet(
            config.GOOGLE_SHEET_WORKSHEET
        )
    except Exception as exc:
        logger.error(f"Failed to initialize Google Sheets: {exc}")
        return

    rows: List[List[str]] = []
    latest_date: datetime | None = None
    
    for order in wine_orders:
        for wine in order.get("wines", []):
            rows.append([
                wine.get("région", ""),
                wine.get("aoc", ""),
                wine.get("producteur", ""),
                wine.get("millésime", ""),
                wine.get("cuvée", ""),
                _normalize_format(wine.get("format", "")),
            ])
        
        order_date = order.get("date")
        if order_date and (not latest_date or order_date > latest_date):
            latest_date = order_date

    if not rows:
        logger.info("No wines to append.")
        return

    try:
        worksheet.append_rows(rows, value_input_option="USER_ENTERED")
        logger.info(f"Appended {len(rows)} rows to Google Sheet.")
        
        if latest_date:
            save_last_sync_date(latest_date)
            logger.info(f"Updated last sync date: {latest_date}")
    except Exception as exc:
        logger.error(f"Failed to append rows: {exc}")
