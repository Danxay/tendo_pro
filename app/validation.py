import re
from datetime import datetime
from urllib.parse import urlparse

NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁё\-\s]+$")


def is_valid_name(text: str) -> bool:
    if not text:
        return False
    text = text.strip()
    if len(text) < 2:
        return False
    return bool(NAME_RE.fullmatch(text))


def is_valid_url(text: str) -> bool:
    if not text:
        return False
    parsed = urlparse(text.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def parse_date(text: str):
    if not text:
        return None
    text = text.strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def count_words(text: str) -> int:
    if not text:
        return 0
    return len(re.findall(r"\S+", text))


def normalize_phone(phone: str) -> str:
    if not phone:
        return ""
    digits = re.sub(r"\D+", "", phone)
    if not digits:
        return ""
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    return f"+{digits}"
