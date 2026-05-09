from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

import requests
from bs4 import BeautifulSoup

from models.rates import ParserResult


TOKYO_CARD_URL = "https://www.tokyo-card.co.jp/wcs/en/rate.php"
TIMEOUT_SECONDS = 15


def parse_tokyo_card() -> ParserResult:
    try:
        response = requests.get(
            TOKYO_CARD_URL,
            timeout=TIMEOUT_SECONDS,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
            },
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return ParserResult("tokyo-card.co.jp", "error", message=str(exc))

    try:
        soup = BeautifulSoup(response.text, "lxml")
        rate = _extract_usd_buy_rate(soup)
        if rate is None:
            return ParserResult("tokyo-card.co.jp", "error", message="USD buy rate was not found.")
        return ParserResult("tokyo-card.co.jp", "success", rate=rate)
    except Exception as exc:
        return ParserResult("tokyo-card.co.jp", "error", message=str(exc))


def _extract_usd_buy_rate(soup: BeautifulSoup) -> Decimal | None:
    for row in soup.find_all("tr"):
        cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]
        if any("USD" in cell for cell in cells):
            numbers = [_parse_decimal(cell) for cell in cells]
            valid = [value for value in numbers if value is not None and Decimal("50") <= value <= Decimal("300")]
            if len(valid) >= 2:
                return valid[1]

    text = soup.get_text(" ", strip=True)
    match = re.search(r"U\.?S\.?\s*Dollar.*?USD\s+(\d{2,3}\.\d{1,4})\s+(\d{2,3}\.\d{1,4})", text)
    if match:
        return Decimal(match.group(2))

    match = re.search(r"\bUSD\b\s+(\d{2,3}\.\d{1,4})\s+(\d{2,3}\.\d{1,4})", text)
    if match:
        return Decimal(match.group(2))

    return None


def _parse_decimal(value: str) -> Decimal | None:
    cleaned = value.replace("\xa0", " ").replace(",", ".")
    match = re.search(r"(?<!\d)(\d{2,3}(?:\.\d{1,4})?)(?!\d)", cleaned)
    if not match:
        return None
    try:
        return Decimal(match.group(1))
    except InvalidOperation:
        return None
