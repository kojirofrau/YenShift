from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from models.rates import RateSnapshot
from storage.database import Database


class CacheRepository:
    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database()

    @property
    def database_path(self):
        return self.database.path

    def save_snapshot(self, snapshot: RateSnapshot) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO latest_rates (
                    update_time,
                    rub_usd_rate,
                    usd_jpy_rate,
                    rub_jpy_rate,
                    banki_status,
                    tokyo_card_status
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.update_time.isoformat(timespec="seconds"),
                    float(snapshot.rub_usd_rate),
                    float(snapshot.usd_jpy_rate),
                    float(snapshot.rub_jpy_rate),
                    snapshot.banki_status,
                    snapshot.tokyo_card_status,
                ),
            )
            conn.commit()

    def get_latest_snapshot(self) -> RateSnapshot | None:
        with self.database.connect() as conn:
            row = conn.execute(
                """
                SELECT update_time, rub_usd_rate, usd_jpy_rate, rub_jpy_rate,
                       banki_status, tokyo_card_status
                FROM latest_rates
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()

        if row is None:
            return None

        return RateSnapshot(
            update_time=datetime.fromisoformat(row["update_time"]),
            rub_usd_rate=Decimal(str(row["rub_usd_rate"])),
            usd_jpy_rate=Decimal(str(row["usd_jpy_rate"])),
            rub_jpy_rate=Decimal(str(row["rub_jpy_rate"])),
            banki_status=row["banki_status"],
            tokyo_card_status=row["tokyo_card_status"],
            used_cache=True,
        )

    def list_snapshots(self) -> list[RateSnapshot]:
        with self.database.connect() as conn:
            rows = conn.execute(
                """
                SELECT update_time, rub_usd_rate, usd_jpy_rate, rub_jpy_rate,
                       banki_status, tokyo_card_status
                FROM latest_rates
                ORDER BY id DESC
                """
            ).fetchall()

        return [
            RateSnapshot(
                update_time=datetime.fromisoformat(row["update_time"]),
                rub_usd_rate=Decimal(str(row["rub_usd_rate"])),
                usd_jpy_rate=Decimal(str(row["usd_jpy_rate"])),
                rub_jpy_rate=Decimal(str(row["rub_jpy_rate"])),
                banki_status=row["banki_status"],
                tokyo_card_status=row["tokyo_card_status"],
                used_cache=True,
            )
            for row in rows
        ]

    def clear(self) -> None:
        with self.database.connect() as conn:
            conn.execute("DELETE FROM latest_rates")
            conn.commit()
