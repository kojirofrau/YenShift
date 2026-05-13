from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.rates import RateSnapshot


INDICATOR_COLORS = {
    "better": "#a8f0b0",
    "worse": "#d01818",
    "same": "#ffffff",
    "missing": "#111111",
}


class MainTab(QWidget):
    refresh_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.snapshot: RateSnapshot | None = None

        self.date_value = QLabel(date.today().isoformat())
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("100000")
        self.rub_usd_value = QLabel("-")
        self.rub_usd_indicator = RateIndicator()
        self.usd_amount_value = QLabel("-")
        self.usd_jpy_value = QLabel("-")
        self.usd_jpy_indicator = RateIndicator()
        self.jpy_amount_value = QLabel("-")
        self.rub_jpy_value = QLabel("-")
        self.rub_jpy_indicator = RateIndicator()
        self.source_status_value = QLabel("No rates loaded")
        self.source_status_value.setWordWrap(True)
        self.last_update_value = QLabel("-")

        self.refresh_button = QPushButton("Refresh current rates")
        self.amount_input.returnPressed.connect(self.calculate)
        self.refresh_button.clicked.connect(self.refresh_requested.emit)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setVerticalSpacing(12)
        form.addRow("Current date", self.date_value)
        form.addRow("Amount in RUB", self.amount_input)
        form.addRow("RUB -> USD rate", _rate_row(self.rub_usd_value, self.rub_usd_indicator))
        form.addRow("Calculated USD", self.usd_amount_value)
        form.addRow("USD -> JPY rate", _rate_row(self.usd_jpy_value, self.usd_jpy_indicator))
        form.addRow("Calculated JPY", self.jpy_amount_value)
        form.addRow("RUB -> JPY coefficient", _rate_row(self.rub_jpy_value, self.rub_jpy_indicator))
        form.addRow("Source status", self.source_status_value)
        form.addRow("Last successful update", self.last_update_value)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)
        layout.addLayout(form)
        layout.addStretch(1)
        layout.addWidget(self.refresh_button)

    def set_loading(self, is_loading: bool) -> None:
        self.refresh_button.setEnabled(not is_loading)
        if is_loading:
            self.source_status_value.setText("Refreshing current rates...")

    def set_snapshot(self, snapshot: RateSnapshot, comparison_snapshot: RateSnapshot | None = None) -> None:
        self.snapshot = snapshot
        self.date_value.setText(date.today().isoformat())
        self.rub_usd_value.setText(f"{snapshot.rub_usd_rate:.4f}")
        self.usd_jpy_value.setText(f"{snapshot.usd_jpy_rate:.4f}")
        self.rub_jpy_value.setText(f"{snapshot.rub_jpy_rate:.6f}")
        self.set_rate_indicators(snapshot, comparison_snapshot)
        self.last_update_value.setText(snapshot.update_time.strftime("%Y-%m-%d %H:%M:%S"))

        source_status = f"banki.ru: {snapshot.banki_status}; tokyo-card.co.jp: {snapshot.tokyo_card_status}"
        if snapshot.used_cache:
            source_status += "; cached values used"
        if snapshot.warning:
            source_status += f"\n{snapshot.warning}"
        self.source_status_value.setText(source_status)
        if self.amount_input.text().strip():
            self.calculate(show_errors=False)

    def clear_snapshot(self) -> None:
        self.snapshot = None
        self.rub_usd_value.setText("-")
        self.rub_usd_indicator.set_state("missing")
        self.usd_amount_value.setText("-")
        self.usd_jpy_value.setText("-")
        self.usd_jpy_indicator.set_state("missing")
        self.jpy_amount_value.setText("-")
        self.rub_jpy_value.setText("-")
        self.rub_jpy_indicator.set_state("missing")
        self.source_status_value.setText("No rates loaded")
        self.last_update_value.setText("-")

    def set_rate_indicators(self, snapshot: RateSnapshot, comparison_snapshot: RateSnapshot | None) -> None:
        if comparison_snapshot is None:
            self.rub_usd_indicator.set_state("missing")
            self.usd_jpy_indicator.set_state("missing")
            self.rub_jpy_indicator.set_state("missing")
            return

        self.rub_usd_indicator.set_state(_comparison_state(snapshot.rub_usd_rate, comparison_snapshot.rub_usd_rate, lower_is_better=True))
        self.usd_jpy_indicator.set_state(_comparison_state(snapshot.usd_jpy_rate, comparison_snapshot.usd_jpy_rate))
        self.rub_jpy_indicator.set_state(_comparison_state(snapshot.rub_jpy_rate, comparison_snapshot.rub_jpy_rate))

    def calculate(self, show_errors: bool = True) -> None:
        if self.snapshot is None:
            if show_errors:
                QMessageBox.warning(self, "Rates unavailable", "Refresh current rates or load cached data first.")
            return

        try:
            amount = Decimal(self.amount_input.text().strip().replace(",", "."))
        except InvalidOperation:
            if show_errors:
                QMessageBox.warning(self, "Invalid amount", "Enter a valid RUB amount.")
            return

        if amount <= 0:
            if show_errors:
                QMessageBox.warning(self, "Invalid amount", "RUB amount must be greater than zero.")
            return

        usd = (amount / self.snapshot.rub_usd_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        jpy = (usd * self.snapshot.usd_jpy_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        coefficient = (jpy / amount).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

        self.usd_amount_value.setText(f"{usd:,.2f}")
        self.jpy_amount_value.setText(f"{jpy:,.0f}")
        self.rub_jpy_value.setText(f"{coefficient:.6f}")


class RateIndicator(QLabel):
    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(14, 14)
        self.set_state("missing")

    def set_state(self, state: str) -> None:
        color = INDICATOR_COLORS[state]
        self.setToolTip(_indicator_tooltip(state))
        self.setStyleSheet(
            f"background: {color}; border: 1px solid #111111; border-radius: 7px;"
        )


def _rate_row(value_label: QLabel, indicator: RateIndicator) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    layout.addWidget(value_label)
    layout.addWidget(indicator)
    layout.addStretch(1)
    return row


def _comparison_state(current: Decimal, previous: Decimal, lower_is_better: bool = False) -> str:
    if current == previous:
        return "same"
    if lower_is_better:
        return "better" if current < previous else "worse"
    return "better" if current > previous else "worse"


def _indicator_tooltip(state: str) -> str:
    return {
        "better": "Better than the latest saved rate before today",
        "worse": "Worse than the latest saved rate before today",
        "same": "Same as the latest saved rate before today",
        "missing": "No saved rate before today to compare",
    }[state]
