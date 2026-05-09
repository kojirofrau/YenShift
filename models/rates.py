from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class RateSnapshot:
    update_time: datetime
    rub_usd_rate: Decimal
    usd_jpy_rate: Decimal
    rub_jpy_rate: Decimal
    banki_status: str
    tokyo_card_status: str
    used_cache: bool = False
    warning: str = ""


@dataclass(frozen=True)
class ParserResult:
    source_name: str
    status: str
    rate: Decimal | None = None
    message: str = ""
