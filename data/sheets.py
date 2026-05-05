import gspread
from google.oauth2.service_account import Credentials

from config import config

SHEET_NAME = "Properties"

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

_INT_FIELDS = ("price", "size_sqm", "floor")
_BOOL_FIELDS = ("pet_friendly", "parking")
_TRUTHY = {"TRUE", "True", "true", True, 1, "1"}


def _to_int(value) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    return int(str(value).strip())


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return value in _TRUTHY


def _is_available(row: dict) -> bool:
    return _to_bool(row.get("available"))


def _normalize(row: dict) -> dict:
    cleaned: dict = {}
    for key, value in row.items():
        if key == "available":
            continue
        if key in _INT_FIELDS:
            cleaned[key] = _to_int(value)
        elif key in _BOOL_FIELDS:
            cleaned[key] = _to_bool(value)
        else:
            cleaned[key] = "" if value is None else str(value)
    return cleaned


def get_listings() -> list[dict]:
    creds = Credentials.from_service_account_file(
        config.SERVICE_ACCOUNT_PATH, scopes=_SCOPES
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(config.GOOGLE_SHEET_ID)
    worksheet = spreadsheet.worksheet(SHEET_NAME)
    rows = worksheet.get_all_records()
    return [_normalize(row) for row in rows if _is_available(row)]