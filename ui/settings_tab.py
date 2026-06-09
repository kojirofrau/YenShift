from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QTime, Signal
from PySide6.QtWidgets import QCheckBox, QFormLayout, QGroupBox, QLabel, QPushButton, QTimeEdit, QVBoxLayout, QWidget


AUTO_REFRESH_KEY = "updates/auto_refresh_on_startup"
SCHEDULED_REFRESH_KEY = "updates/scheduled_refresh_enabled"
SCHEDULED_REFRESH_TIME_KEYS = [
    "updates/scheduled_refresh_time_1",
    "updates/scheduled_refresh_time_2",
    "updates/scheduled_refresh_time_3",
    "updates/scheduled_refresh_time_4",
]
DEFAULT_SCHEDULED_REFRESH_TIMES = ["09:00", "12:00", "15:00", "18:00"]
NOTIFICATION_SOUND_KEY = "notifications/sound_enabled"


class SettingsTab(QWidget):
    refresh_requested = Signal()
    clear_cache_requested = Signal()
    open_database_requested = Signal()
    schedule_changed = Signal()

    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self.settings = QSettings()

        self.auto_refresh_checkbox = QCheckBox("Update rates when the app opens")
        self.auto_refresh_checkbox.setChecked(self.auto_refresh_enabled())
        self.scheduled_refresh_checkbox = QCheckBox("Update rates automatically at selected times")
        self.scheduled_refresh_checkbox.setChecked(self.scheduled_refresh_enabled())
        self.scheduled_time_edits = [self._create_time_edit(time_value) for time_value in self.scheduled_refresh_times()]
        self.update_scheduled_time_edit_state()
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
        self.scheduled_refresh_checkbox.toggled.connect(self.set_scheduled_refresh_enabled)
        for index, time_edit in enumerate(self.scheduled_time_edits):
            time_edit.timeChanged.connect(lambda time, slot=index: self.set_scheduled_refresh_time(slot, time))
        self.notification_sound_checkbox.toggled.connect(self.set_notification_sound_enabled)
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        self.clear_cache_button.clicked.connect(self.clear_cache_requested.emit)
        self.open_database_button.clicked.connect(self.open_database_requested.emit)

        scheduled_group = QGroupBox("Scheduled updates")
        scheduled_layout = QFormLayout(scheduled_group)
        scheduled_layout.setVerticalSpacing(8)
        scheduled_layout.addRow(self.scheduled_refresh_checkbox)
        for index, time_edit in enumerate(self.scheduled_time_edits, start=1):
            scheduled_layout.addRow(f"Time {index}", time_edit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)
        layout.addWidget(self.auto_refresh_checkbox)
        layout.addWidget(scheduled_group)
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

    def scheduled_refresh_enabled(self) -> bool:
        return self.settings.value(SCHEDULED_REFRESH_KEY, False, type=bool)

    def set_scheduled_refresh_enabled(self, enabled: bool) -> None:
        self.settings.setValue(SCHEDULED_REFRESH_KEY, enabled)
        self.update_scheduled_time_edit_state()
        self.schedule_changed.emit()

    def scheduled_refresh_times(self) -> list[str]:
        return [
            _valid_time_text(self.settings.value(key, default, type=str), default)
            for key, default in zip(SCHEDULED_REFRESH_TIME_KEYS, DEFAULT_SCHEDULED_REFRESH_TIMES)
        ]

    def set_scheduled_refresh_time(self, index: int, time: QTime) -> None:
        self.settings.setValue(SCHEDULED_REFRESH_TIME_KEYS[index], time.toString("HH:mm"))
        self.schedule_changed.emit()

    def update_scheduled_time_edit_state(self) -> None:
        enabled = self.scheduled_refresh_checkbox.isChecked()
        for time_edit in self.scheduled_time_edits:
            time_edit.setEnabled(enabled)

    def notification_sound_enabled(self) -> bool:
        return self.settings.value(NOTIFICATION_SOUND_KEY, True, type=bool)

    def set_notification_sound_enabled(self, enabled: bool) -> None:
        self.settings.setValue(NOTIFICATION_SOUND_KEY, enabled)

    def _create_time_edit(self, time_value: str) -> QTimeEdit:
        time_edit = QTimeEdit()
        time_edit.setDisplayFormat("HH:mm")
        time_edit.setTime(QTime.fromString(time_value, "HH:mm"))
        return time_edit


def _valid_time_text(value: str, fallback: str) -> str:
    parsed = QTime.fromString(value, "HH:mm")
    if parsed.isValid():
        return value
    return fallback
