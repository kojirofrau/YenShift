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


class MainTab(QWidget):
    refresh_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.snapshot: RateSnapshot | None = None

        self.date_value = QLabel(date.today().isoformat())
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("100000")
        self.rub_usd_value = QLabel("-")
        self.usd_amount_value = QLabel("-")
        self.usd_jpy_value = QLabel("-")
        self.jpy_amount_value = QLabel("-")
        self.rub_jpy_value = QLabel("-")
        self.source_status_value = QLabel("No rates loaded")
        self.source_status_value.setWordWrap(True)
        self.last_update_value = QLabel("-")

        self.calculate_button = QPushButton("Calculate")
        self.refresh_button = QPushButton("Refresh current rates")
        self.calculate_button.clicked.connect(self.calculate)
        self.refresh_button.clicked.connect(self.refresh_requested.emit)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setVerticalSpacing(12)
        form.addRow("Current date", self.date_value)
        form.addRow("Amount in RUB", self.amount_input)
        form.addRow("RUB -> USD rate", self.rub_usd_value)
        form.addRow("Calculated USD", self.usd_amount_value)
        form.addRow("USD -> JPY rate", self.usd_jpy_value)
        form.addRow("Calculated JPY", self.jpy_amount_value)
        form.addRow("RUB -> JPY coefficient", self.rub_jpy_value)
        form.addRow("Source status", self.source_status_value)
        form.addRow("Last successful update", self.last_update_value)

        buttons = QHBoxLayout()
        buttons.addWidget(self.calculate_button)
        buttons.addWidget(self.refresh_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)
        layout.addLayout(form)
        layout.addStretch(1)
        layout.addLayout(buttons)

    def set_loading(self, is_loading: bool) -> None:
        self.refresh_button.setEnabled(not is_loading)
        self.calculate_button.setEnabled(not is_loading)
        if is_loading:
            self.source_status_value.setText("Refreshing current rates...")

    def set_snapshot(self, snapshot: RateSnapshot) -> None:
        self.snapshot = snapshot
        self.date_value.setText(date.today().isoformat())
        self.rub_usd_value.setText(f"{snapshot.rub_usd_rate:.4f}")
        self.usd_jpy_value.setText(f"{snapshot.usd_jpy_rate:.4f}")
        self.rub_jpy_value.setText(f"{snapshot.rub_jpy_rate:.6f}")
        self.last_update_value.setText(snapshot.update_time.strftime("%Y-%m-%d %H:%M:%S"))

        source_status = f"banki.ru: {snapshot.banki_status}; tokyo-card.co.jp: {snapshot.tokyo_card_status}"
        if snapshot.used_cache:
            source_status += "; cached values used"
        if snapshot.warning:
            source_status += f"\n{snapshot.warning}"
        self.source_status_value.setText(source_status)

    def clear_snapshot(self) -> None:
        self.snapshot = None
        self.rub_usd_value.setText("-")
        self.usd_amount_value.setText("-")
        self.usd_jpy_value.setText("-")
        self.jpy_amount_value.setText("-")
        self.rub_jpy_value.setText("-")
        self.source_status_value.setText("No rates loaded")
        self.last_update_value.setText("-")

    def calculate(self) -> None:
        if self.snapshot is None:
            QMessageBox.warning(self, "Rates unavailable", "Refresh current rates or load cached data first.")
            return

        try:
            amount = Decimal(self.amount_input.text().strip().replace(",", "."))
        except InvalidOperation:
            QMessageBox.warning(self, "Invalid amount", "Enter a valid RUB amount.")
            return

        if amount <= 0:
            QMessageBox.warning(self, "Invalid amount", "RUB amount must be greater than zero.")
            return

        usd = (amount / self.snapshot.rub_usd_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        jpy = (usd * self.snapshot.usd_jpy_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        coefficient = (jpy / amount).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

        self.usd_amount_value.setText(f"{usd:,.2f}")
        self.jpy_amount_value.setText(f"{jpy:,.0f}")
        self.rub_jpy_value.setText(f"{coefficient:.6f}")
