import json
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return value


def _parse_allowed_ids(raw: str) -> set[int]:
    ids: set[int] = set()
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            ids.add(int(chunk))
        except ValueError as exc:
            raise EnvironmentError(
                f"ALLOWED_TELEGRAM_IDS contains a non-integer value: {chunk!r}"
            ) from exc
    if not ids:
        raise EnvironmentError(
            "ALLOWED_TELEGRAM_IDS must contain at least one Telegram user ID"
        )
    return ids


def _parse_service_account(raw: str) -> tuple[str, dict | None]:
    """Returns (path, info). Exactly one is populated.

    If the value looks like inline JSON (starts with `{`), parse and return as info.
    Otherwise treat as a filesystem path.
    """
    if raw.lstrip().startswith("{"):
        try:
            return ("", json.loads(raw))
        except json.JSONDecodeError as exc:
            raise EnvironmentError(
                "GOOGLE_SERVICE_ACCOUNT_JSON looks like inline JSON but failed to parse"
            ) from exc
    return (raw, None)


@dataclass(frozen=True)
class Config:
    TELEGRAM_BOT_TOKEN: str
    OPENAI_API_KEY: str
    GOOGLE_SHEET_ID: str
    SERVICE_ACCOUNT_PATH: str
    SERVICE_ACCOUNT_INFO: dict | None
    ALLOWED_IDS: set[int]


_path, _info = _parse_service_account(_require("GOOGLE_SERVICE_ACCOUNT_JSON"))

config = Config(
    TELEGRAM_BOT_TOKEN=_require("TELEGRAM_BOT_TOKEN"),
    OPENAI_API_KEY=_require("OPENAI_API_KEY"),
    GOOGLE_SHEET_ID=_require("GOOGLE_SHEET_ID"),
    SERVICE_ACCOUNT_PATH=_path,
    SERVICE_ACCOUNT_INFO=_info,
    ALLOWED_IDS=_parse_allowed_ids(_require("ALLOWED_TELEGRAM_IDS")),
)
