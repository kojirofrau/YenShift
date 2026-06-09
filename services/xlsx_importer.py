from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile

from models.rates import RateSnapshot
from services.xlsx_exporter import HEADERS


WORKSHEET_PATH = "xl/worksheets/sheet1.xml"
SPREADSHEET_NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


class XlsxImportError(ValueError):
    pass


def import_snapshots_from_xlsx(path: Path, import_date: date | None = None) -> list[RateSnapshot]:
    import_dates = _allowed_import_dates(import_date or date.today())

    try:
        with ZipFile(path) as workbook:
            if WORKSHEET_PATH not in workbook.namelist():
                raise XlsxImportError("The workbook does not match the YenShift export format.")
            worksheet_xml = workbook.read(WORKSHEET_PATH)
    except (BadZipFile, OSError) as exc:
        raise XlsxImportError("Unable to open the selected XLSX file.") from exc

    try:
        root = ET.fromstring(worksheet_xml)
    except ET.ParseError as exc:
        raise XlsxImportError("The workbook contains an invalid worksheet.") from exc

    rows = root.findall(".//s:sheetData/s:row", SPREADSHEET_NS)
    if not rows:
        raise XlsxImportError("The workbook does not contain exported rate data.")

    parsed_rows = [_row_values(row) for row in rows]
    if parsed_rows[0] != HEADERS:
        raise XlsxImportError("The workbook headers do not match the YenShift export format.")

    snapshots: list[RateSnapshot] = []
    for row_index, values in enumerate(parsed_rows[1:], start=2):
        if _is_empty_row(values):
            continue
        snapshot = _snapshot_from_values(values, row_index)
        if snapshot.update_time.date() in import_dates:
            snapshots.append(snapshot)

    return snapshots


def _allowed_import_dates(today: date) -> set[date]:
    return {today, today - timedelta(days=1)}


def _row_values(row: ET.Element) -> list[str]:
    values = [""] * len(HEADERS)
    seen_columns: set[int] = set()

    for cell in row.findall("s:c", SPREADSHEET_NS):
        reference = cell.attrib.get("r", "")
        column_index = _column_index(reference)
        if column_index is None or column_index < 0 or column_index >= len(HEADERS):
            raise XlsxImportError("The workbook columns do not match the YenShift export format.")
        if column_index in seen_columns:
            raise XlsxImportError("The workbook contains duplicate cells.")
        seen_columns.add(column_index)
        values[column_index] = _cell_value(cell)

    return values


def _cell_value(cell: ET.Element) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        text_node = cell.find("s:is/s:t", SPREADSHEET_NS)
        return "" if text_node is None or text_node.text is None else text_node.text
    if cell_type in (None, "n"):
        value_node = cell.find("s:v", SPREADSHEET_NS)
        return "" if value_node is None or value_node.text is None else value_node.text
    raise XlsxImportError("The workbook cell types do not match the YenShift export format.")


def _column_index(reference: str) -> int | None:
    match = re.fullmatch(r"([A-Z]+)\d+", reference)
    if match is None:
        return None

    index = 0
    for letter in match.group(1):
        index = index * 26 + ord(letter) - ord("A") + 1
    return index - 1


def _snapshot_from_values(values: list[str], row_index: int) -> RateSnapshot:
    if len(values) != len(HEADERS):
        raise XlsxImportError(f"Row {row_index} does not match the YenShift export format.")

    try:
        update_time = datetime.strptime(values[0], "%Y-%m-%d %H:%M:%S")
        rub_usd_rate = Decimal(values[1])
        usd_jpy_rate = Decimal(values[2])
        rub_jpy_rate = Decimal(values[3])
    except (ValueError, InvalidOperation) as exc:
        raise XlsxImportError(f"Row {row_index} contains invalid rate data.") from exc

    if rub_usd_rate <= 0 or usd_jpy_rate <= 0 or rub_jpy_rate <= 0:
        raise XlsxImportError(f"Row {row_index} contains invalid rate data.")
    if not values[4] or not values[5]:
        raise XlsxImportError(f"Row {row_index} contains invalid source status data.")

    return RateSnapshot(
        update_time=update_time,
        rub_usd_rate=rub_usd_rate,
        usd_jpy_rate=usd_jpy_rate,
        rub_jpy_rate=rub_jpy_rate,
        banki_status=values[4],
        tokyo_card_status=values[5],
        used_cache=True,
    )


def _is_empty_row(values: list[str]) -> bool:
    return all(not value for value in values)
