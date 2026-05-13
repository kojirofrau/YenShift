from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path


APP_NAME = "YenShift"


def get_database_path() -> Path:
    candidates = [
        Path(base) / APP_NAME
        for base in (os.environ.get("APPDATA"), os.environ.get("LOCALAPPDATA"))
        if base
    ]
    candidates.extend(
        [
            Path.home() / f".{APP_NAME.lower()}",
            Path(tempfile.gettempdir()) / APP_NAME,
        ]
    )

    for data_dir in candidates:
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            return data_dir / "yenshift.sqlite"
        except OSError:
            continue

    raise RuntimeError("Unable to create a writable YenShift data directory.")


class Database:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or get_database_path()
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS latest_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    update_time TEXT,
                    rub_usd_rate REAL,
                    usd_jpy_rate REAL,
                    rub_jpy_rate REAL,
                    banki_status TEXT,
                    tokyo_card_status TEXT
                )
                """
            )
            conn.execute(
                """
                UPDATE latest_rates
                SET rub_usd_rate = ROUND(rub_usd_rate, 4),
                    usd_jpy_rate = ROUND(usd_jpy_rate, 4),
                    rub_jpy_rate = ROUND(rub_jpy_rate, 4)
                """
            )
            conn.commit()
