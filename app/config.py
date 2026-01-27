from dataclasses import dataclass
import os

from .validation import normalize_phone


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_code: str
    admin_phones: list[str]
    db_path: str


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN env var is required")
    admin_code = os.getenv("ADMIN_CODE", "0000")
    phones_raw = os.getenv("ADMIN_PHONES", "")
    admin_phones = [normalize_phone(p) for p in phones_raw.split(",") if normalize_phone(p)]
    db_path = os.getenv("DB_PATH", os.path.join("data", "bot.db"))
    return Config(
        bot_token=token,
        admin_code=admin_code,
        admin_phones=admin_phones,
        db_path=db_path,
    )
