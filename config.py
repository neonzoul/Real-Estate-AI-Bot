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


@dataclass(frozen=True)
class Config:
    TELEGRAM_BOT_TOKEN: str
    OPENAI_API_KEY: str
    GOOGLE_SHEET_ID: str
    SERVICE_ACCOUNT_PATH: str
    ALLOWED_IDS: set[int]


config = Config(
    TELEGRAM_BOT_TOKEN=_require("TELEGRAM_BOT_TOKEN"),
    OPENAI_API_KEY=_require("OPENAI_API_KEY"),
    GOOGLE_SHEET_ID=_require("GOOGLE_SHEET_ID"),
    SERVICE_ACCOUNT_PATH=_require("GOOGLE_SERVICE_ACCOUNT_JSON"),
    ALLOWED_IDS=_parse_allowed_ids(_require("ALLOWED_TELEGRAM_IDS")),
)
