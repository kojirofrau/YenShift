from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from models.rates import RateSnapshot
from storage.database import Database


DATABASE_RATE_PRECISION = Decimal("0.0001")


class CacheRepository:
    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database()

    @property
    def database_path(self):
        return self.database.path

    def save_snapshot(self, snapshot: RateSnapshot) -> None:
        rub_usd_rate = _database_rate(snapshot.rub_usd_rate)
        usd_jpy_rate = _database_rate(snapshot.usd_jpy_rate)
        rub_jpy_rate = _database_rate(snapshot.rub_jpy_rate)

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
                    float(rub_usd_rate),
                    float(usd_jpy_rate),
                    float(rub_jpy_rate),
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
            **_snapshot_fields(row),
        )

    def get_latest_snapshot_before_date(self, comparison_date: date) -> RateSnapshot | None:
        with self.database.connect() as conn:
            row = conn.execute(
                """
                SELECT update_time, rub_usd_rate, usd_jpy_rate, rub_jpy_rate,
                       banki_status, tokyo_card_status
                FROM latest_rates
                WHERE date(update_time) < ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (comparison_date.isoformat(),),
            ).fetchone()

        if row is None:
            return None

        return RateSnapshot(**_snapshot_fields(row))

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
                **_snapshot_fields(row),
            )
            for row in rows
        ]

    def clear(self) -> None:
        with self.database.connect() as conn:
            conn.execute("DELETE FROM latest_rates")
            conn.commit()


def _database_rate(value: Decimal) -> Decimal:
    return value.quantize(DATABASE_RATE_PRECISION, rounding=ROUND_HALF_UP)


def _snapshot_fields(row) -> dict:
    return {
        "update_time": datetime.fromisoformat(row["update_time"]),
        "rub_usd_rate": Decimal(str(row["rub_usd_rate"])),
        "usd_jpy_rate": Decimal(str(row["usd_jpy_rate"])),
        "rub_jpy_rate": Decimal(str(row["rub_jpy_rate"])),
        "banki_status": row["banki_status"],
        "tokyo_card_status": row["tokyo_card_status"],
        "used_cache": True,
    }
