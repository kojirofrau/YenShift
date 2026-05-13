from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.rates import RateSnapshot
from services.xlsx_exporter import export_snapshots_to_xlsx


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
        self.snapshots: list[RateSnapshot] = []
        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.refresh_button = QPushButton("Refresh")
        self.export_button = QPushButton("Export XLSX")
        self.export_button.setIcon(_excel_icon())
        self.clear_button = QPushButton("Clear log")
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        self.export_button.clicked.connect(self.export_xlsx)
        self.clear_button.clicked.connect(self.clear_requested.emit)

        buttons = QHBoxLayout()
        buttons.addWidget(self.refresh_button)
        buttons.addWidget(self.export_button)
        buttons.addWidget(self.clear_button)
        buttons.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(self.table)
        layout.addLayout(buttons)

    def set_snapshots(self, snapshots: list[RateSnapshot]) -> None:
        self.snapshots = snapshots
        self.export_button.setEnabled(bool(snapshots))
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

    def export_xlsx(self) -> None:
        if not self.snapshots:
            QMessageBox.information(self, "Export XLSX", "There are no saved rate records to export.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export history",
            "yenshift_history.xlsx",
            "Excel Workbook (*.xlsx)",
        )
        if not path:
            return

        export_path = Path(path)
        if export_path.suffix.lower() != ".xlsx":
            export_path = export_path.with_suffix(".xlsx")

        try:
            export_snapshots_to_xlsx(export_path, self.snapshots)
        except OSError as exc:
            QMessageBox.warning(self, "Export XLSX", str(exc))
            return

        QMessageBox.information(self, "Export XLSX", f"History exported to:\n{export_path}")


def _excel_icon() -> QIcon:
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#107c41"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(1, 1, 16, 16, 3, 3)
    painter.setPen(QPen(QColor("#ffffff"), 2))
    painter.drawLine(6, 5, 12, 13)
    painter.drawLine(12, 5, 6, 13)
    painter.end()

    return QIcon(pixmap)
