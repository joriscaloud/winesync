from typing import List, Dict

import gspread
from google.oauth2.service_account import Credentials

from utils.logger import logger
import config


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


def append_wines_to_sheet(wine_orders: List[Dict]) -> None:
    """Append wine rows to the configured Google Sheet."""
    if not wine_orders:
        logger.info("No wine orders to export to Google Sheets.")
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
        logger.error(f"Failed to initialize Google Sheets client: {type(exc).__name__}: {exc}")
        return

    rows: List[List[str]] = []
    for order in wine_orders:
        for wine in order.get("wines", []):
            rows.append(
                [
                    wine.get("région", ""),
                    wine.get("aoc", ""),
                    wine.get("producteur", ""),
                    wine.get("millésime", ""),
                    wine.get("cuvée", ""),
                    _normalize_format(wine.get("format", "")),
                ]
            )

    if not rows:
        logger.info("No wine rows to append.")
        return

    try:
        worksheet.append_rows(rows, value_input_option="USER_ENTERED")
        logger.info(f"Appended {len(rows)} rows to Google Sheet.")
    except Exception as exc:
        logger.error(f"Failed to append rows to Google Sheet: {exc}")
