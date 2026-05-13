from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtWidgets import QCheckBox, QLabel, QPushButton, QVBoxLayout, QWidget


AUTO_REFRESH_KEY = "updates/auto_refresh_on_startup"
NOTIFICATION_SOUND_KEY = "notifications/sound_enabled"


class SettingsTab(QWidget):
    refresh_requested = Signal()
    clear_cache_requested = Signal()
    open_database_requested = Signal()

    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self.settings = QSettings()

        self.auto_refresh_checkbox = QCheckBox("Update rates when the app opens")
        self.auto_refresh_checkbox.setChecked(self.auto_refresh_enabled())
        self.notification_sound_checkbox = QCheckBox("Play sound when rates are updated")
        self.notification_sound_checkbox.setChecked(self.notification_sound_enabled())
        self.refresh_button = QPushButton("Refresh current rates")
        self.clear_cache_button = QPushButton("Clear cache")
        self.open_database_button = QPushButton("Open database")
        self.database_label = QLabel(str(database_path))
        self.database_label.setWordWrap(True)
        self.credit_label = QLabel("made by frau kojiro")
        self.credit_label.setAlignment(Qt.AlignRight)
        self.credit_label.setStyleSheet("color: #000000; font-size: 8pt;")

        self.auto_refresh_checkbox.toggled.connect(self.set_auto_refresh_enabled)
        self.notification_sound_checkbox.toggled.connect(self.set_notification_sound_enabled)
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        self.clear_cache_button.clicked.connect(self.clear_cache_requested.emit)
        self.open_database_button.clicked.connect(self.open_database_requested.emit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)
        layout.addWidget(self.auto_refresh_checkbox)
        layout.addWidget(self.notification_sound_checkbox)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.clear_cache_button)
        layout.addWidget(self.open_database_button)
        layout.addSpacing(12)
        layout.addWidget(QLabel("Database"))
        layout.addWidget(self.database_label)
        layout.addStretch(1)
        layout.addWidget(self.credit_label)

    def auto_refresh_enabled(self) -> bool:
        return self.settings.value(AUTO_REFRESH_KEY, False, type=bool)

    def set_auto_refresh_enabled(self, enabled: bool) -> None:
        self.settings.setValue(AUTO_REFRESH_KEY, enabled)

    def notification_sound_enabled(self) -> bool:
        return self.settings.value(NOTIFICATION_SOUND_KEY, True, type=bool)

    def set_notification_sound_enabled(self, enabled: bool) -> None:
        self.settings.setValue(NOTIFICATION_SOUND_KEY, enabled)
