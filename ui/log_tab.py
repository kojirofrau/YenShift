from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.rates import RateSnapshot


class LogTab(QWidget):
    refresh_requested = Signal()
    clear_requested = Signal()

    HEADERS = [
        "Update time",
        "RUB -> USD",
        "USD -> JPY",
        "RUB -> JPY",
        "banki.ru",
        "tokyo-card",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.refresh_button = QPushButton("Refresh")
        self.clear_button = QPushButton("Clear log")
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        self.clear_button.clicked.connect(self.clear_requested.emit)

        buttons = QHBoxLayout()
        buttons.addWidget(self.refresh_button)
        buttons.addWidget(self.clear_button)
        buttons.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(self.table)
        layout.addLayout(buttons)

    def set_snapshots(self, snapshots: list[RateSnapshot]) -> None:
        self.table.setRowCount(len(snapshots))
        for row_index, snapshot in enumerate(snapshots):
            values = [
                snapshot.update_time.strftime("%Y-%m-%d %H:%M:%S"),
                f"{snapshot.rub_usd_rate:.4f}",
                f"{snapshot.usd_jpy_rate:.4f}",
                f"{snapshot.rub_jpy_rate:.6f}",
                snapshot.banki_status,
                snapshot.tokyo_card_status,
            ]
            for column_index, value in enumerate(values):
                self.table.setItem(row_index, column_index, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()
