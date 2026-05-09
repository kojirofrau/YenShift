from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import requests
from bs4 import BeautifulSoup

from models.rates import ParserResult


BANKI_URL = "https://www.banki.ru/products/currency/usd/?regionUrl=nizhniy_novgorod"
TIMEOUT_SECONDS = 15


def parse_banki_ru() -> ParserResult:
    try:
        response = requests.get(
            BANKI_URL,
            timeout=TIMEOUT_SECONDS,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                ),
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            },
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return ParserResult("banki.ru", "error", message=str(exc))

    try:
        soup = BeautifulSoup(response.text, "lxml")
        rates = _extract_sell_rates_from_tables(soup)
        if not rates:
            rates = _extract_sell_rates_from_text(soup.get_text(" ", strip=True))

        unique_rates = list(dict.fromkeys(rate for rate in rates if rate > 0))
        if not unique_rates:
            return ParserResult("banki.ru", "error", message="No valid USD sell rates found.")

        average = sum(unique_rates) / Decimal(len(unique_rates))
        average = average.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        return ParserResult("banki.ru", "success", rate=average)
    except Exception as exc:
        return ParserResult("banki.ru", "error", message=str(exc))


def _extract_sell_rates_from_tables(soup: BeautifulSoup) -> list[Decimal]:
    rates: list[Decimal] = []
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]
            row_text = " ".join(cells)
            if not re.search(r"\d{2}\.\d{2}\.\d{4}", row_text):
                continue
            numeric_cells = [_parse_decimal(cell) for cell in cells]
            valid = [value for value in numeric_cells if value is not None and Decimal("20") <= value <= Decimal("200")]
            if len(valid) >= 2:
                rates.append(valid[1])
    return rates


def _extract_sell_rates_from_text(text: str) -> list[Decimal]:
    rates: list[Decimal] = []
    block = _extract_best_rate_block(text)

    row_pattern = re.compile(
        r"([А-Яа-яЁёA-Za-z0-9 .«»\"'()\-]+?)\s+"
        r"(\d{2,3}(?:[,.]\d{1,4})?)\s+"
        r"(\d{2,3}(?:[,.]\d{1,4})?)\s+"
        r"\d{2}\.\d{2}\.\d{4}",
        flags=re.DOTALL,
    )
    for match in row_pattern.finditer(block):
        value = _parse_decimal(match.group(3))
        if value is not None and Decimal("20") <= value <= Decimal("200"):
            rates.append(value)

    if rates:
        return rates

    for match in re.finditer(r"(?<!\d)(\d{2,3}(?:[,.]\d{1,4})?)(?!\d)", block):
        value = _parse_decimal(match.group(1))
        if value is not None and Decimal("20") <= value <= Decimal("200"):
            rates.append(value)

    if len(rates) >= 2:
        return rates[1::2]
    return rates


def _extract_best_rate_block(text: str) -> str:
    start = _find_first_marker(text, ["Лучший курс", "Р›СѓС‡С€РёР№ РєСѓСЂСЃ"])
    if start == -1:
        start = _find_first_marker(text, ["Все курсы банков", "Р’СЃРµ РєСѓСЂСЃС‹ Р±Р°РЅРєРѕРІ"])
    if start == -1:
        return text

    end_markers = [
        "Новости",
        "Где выгоднее",
        "Информация о долларе",
        "РќРѕРІРѕСЃС‚Рё",
        "Р“РґРµ РІС‹РіРѕРґРЅРµРµ",
        "РРЅС„РѕСЂРјР°С†РёСЏ Рѕ РґРѕР»Р»Р°СЂРµ",
    ]
    end_candidates = [
        index for marker in end_markers
        if (index := text.find(marker, start + 1)) != -1
    ]
    end = min(end_candidates) if end_candidates else len(text)
    return text[start:end]


def _find_first_marker(text: str, markers: list[str]) -> int:
    positions = [index for marker in markers if (index := text.find(marker)) != -1]
    return min(positions) if positions else -1


def _parse_decimal(value: str) -> Decimal | None:
    cleaned = value.replace("\xa0", " ").replace("₽", "").replace("в‚Ѕ", "").replace(",", ".")
    match = re.search(r"(?<!\d)(\d{2,3}(?:\.\d{1,4})?)(?!\d)", cleaned)
    if not match:
        return None
    try:
        return Decimal(match.group(1))
    except InvalidOperation:
        return None
