from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from models.rates import RateSnapshot
from services.parsers.banki_ru_parser import parse_banki_ru
from services.parsers.tokyo_card_parser import parse_tokyo_card
from storage.cache_repository import CacheRepository


class DataSourceManager:
    def __init__(self, cache: CacheRepository | None = None) -> None:
        self.cache = cache or CacheRepository()

    def refresh_current_rates(self) -> RateSnapshot:
        banki = parse_banki_ru()
        tokyo = parse_tokyo_card()

        cached = self.cache.get_latest_snapshot()
        warnings: list[str] = []

        rub_usd_rate = banki.rate
        usd_jpy_rate = tokyo.rate
        used_cache = False

        if rub_usd_rate is None:
            if cached is not None:
                rub_usd_rate = cached.rub_usd_rate
                used_cache = True
                warnings.append("Unable to update RUB -> USD rate from banki.ru. Using last saved value.")
            else:
                warnings.append("Unable to update RUB -> USD rate from banki.ru.")

        if usd_jpy_rate is None:
            if cached is not None:
                usd_jpy_rate = cached.usd_jpy_rate
                used_cache = True
                warnings.append("Unable to update USD -> JPY rate from tokyo-card.co.jp. Using last saved value.")
            else:
                warnings.append("Unable to update USD -> JPY rate from tokyo-card.co.jp.")

        if rub_usd_rate is None or usd_jpy_rate is None:
            raise RuntimeError("No valid exchange rates are available. Please connect to the internet and refresh.")

        rub_jpy_rate = (usd_jpy_rate / rub_usd_rate).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        snapshot = RateSnapshot(
            update_time=datetime.now(),
            rub_usd_rate=rub_usd_rate,
            usd_jpy_rate=usd_jpy_rate,
            rub_jpy_rate=rub_jpy_rate,
            banki_status=banki.status,
            tokyo_card_status=tokyo.status,
            used_cache=used_cache,
            warning="\n".join(warnings),
        )
        self.cache.save_snapshot(snapshot)
        return snapshot

    def latest_or_none(self) -> RateSnapshot | None:
        return self.cache.get_latest_snapshot()
