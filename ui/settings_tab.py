from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class SettingsTab(QWidget):
    refresh_requested = Signal()
    clear_cache_requested = Signal()
    open_database_requested = Signal()

    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self.refresh_button = QPushButton("Refresh current rates")
        self.clear_cache_button = QPushButton("Clear cache")
        self.open_database_button = QPushButton("Open database")
        self.database_label = QLabel(str(database_path))
        self.database_label.setWordWrap(True)
        self.credit_label = QLabel("made by frau kojiro")
        self.credit_label.setAlignment(Qt.AlignRight)
        self.credit_label.setStyleSheet("color: #000000; font-size: 8pt;")

        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        self.clear_cache_button.clicked.connect(self.clear_cache_requested.emit)
        self.open_database_button.clicked.connect(self.open_database_requested.emit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.clear_cache_button)
        layout.addWidget(self.open_database_button)
        layout.addSpacing(12)
        layout.addWidget(QLabel("Database"))
        layout.addWidget(self.database_label)
        layout.addStretch(1)
        layout.addWidget(self.credit_label)
