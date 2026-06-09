from __future__ import annotations

import os
import sys
from datetime import date, datetime
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, QUrl, Signal, Slot
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QMainWindow, QMessageBox, QTabWidget

from models.rates import RateSnapshot
from services.data_sources import DataSourceManager
from storage.cache_repository import CacheRepository
from ui.chart_tab import ChartTab
from ui.log_tab import LogTab
from ui.main_tab import MainTab
from ui.settings_tab import SettingsTab


NOTIFICATION_SOUND_PATH = "assets/audio/notification_1.mp3"


class RefreshWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, manager: DataSourceManager) -> None:
        super().__init__()
        self.manager = manager

    @Slot()
    def run(self) -> None:
        try:
            self.finished.emit(self.manager.refresh_current_rates())
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.cache = CacheRepository()
        self.manager = DataSourceManager(self.cache)
        self.refresh_thread: QThread | None = None
        self.refresh_worker: RefreshWorker | None = None
        self.last_scheduled_refresh_key = ""
        self.notification_audio = QAudioOutput(self)
        self.notification_player = QMediaPlayer(self)
        self.notification_player.setAudioOutput(self.notification_audio)
        self.notification_audio.setVolume(0.7)

        self.setWindowTitle("YenShift")
        self.setFixedSize(512, 640)

        self.main_tab = MainTab()
        self.log_tab = LogTab()
        self.chart_tab = ChartTab()
        self.settings_tab = SettingsTab(self.cache.database_path)

        tabs = QTabWidget()
        tabs.addTab(self.main_tab, "Convert")
        tabs.addTab(self.log_tab, "History")
        tabs.addTab(self.chart_tab, "Trends")
        tabs.addTab(self.settings_tab, "Settings")
        self.setCentralWidget(tabs)

        self.main_tab.refresh_requested.connect(self.refresh_rates)
        self.log_tab.refresh_requested.connect(self.reload_log)
        self.log_tab.clear_requested.connect(self.clear_cache)
        self.settings_tab.refresh_requested.connect(self.refresh_rates)
        self.settings_tab.clear_cache_requested.connect(self.clear_cache)
        self.settings_tab.open_database_requested.connect(self.open_database)
        self.settings_tab.schedule_changed.connect(self.reset_scheduled_refresh_guard)

        self.schedule_timer = QTimer(self)
        self.schedule_timer.setInterval(30_000)
        self.schedule_timer.timeout.connect(self.check_scheduled_refresh)
        self.schedule_timer.start()

        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #7fffd4;
                color: #202124;
                font-family: Montserrat, Segoe UI, Arial;
            }
            QTabWidget::pane {
                border: 1px solid #111111;
                background: #7fffd4;
            }
            QTabBar::tab {
                background: #dffff5;
                color: #202124;
                padding: 7px 10px;
                border: 1px solid #111111;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background: #ffffff;
            }
            QPushButton {
                background: #ffffff;
                color: #000000;
                border: 1px solid #000000;
                border-radius: 5px;
                padding: 8px 10px;
            }
            QPushButton:hover {
                background: #f0fffb;
            }
            QPushButton:disabled {
                color: #777777;
                border-color: #777777;
                background: #eeeeee;
            }
            QLineEdit {
                background: #ffffff;
                color: #111111;
                border: 1px solid #111111;
                border-radius: 4px;
                padding: 7px;
            }
            QTableWidget {
                background: #ffffff;
                alternate-background-color: #e9fffb;
                color: #111111;
                gridline-color: #9fbdb5;
            }
            QHeaderView::section {
                background: #dffff5;
                color: #111111;
                border: 1px solid #9fbdb5;
                padding: 4px;
            }
            """
        )

        self.load_cached_snapshot()
        self.reload_log()
        if self.settings_tab.auto_refresh_enabled():
            QTimer.singleShot(0, self.refresh_rates)
        QTimer.singleShot(1_000, self.check_scheduled_refresh)

    def load_cached_snapshot(self) -> None:
        snapshot = self.manager.latest_or_none()
        if snapshot is not None:
            self.apply_snapshot(snapshot)

    @Slot()
    def refresh_rates(self) -> None:
        if self.refresh_thread is not None:
            return

        self.main_tab.set_loading(True)
        self.refresh_thread = QThread(self)
        self.refresh_worker = RefreshWorker(self.manager)
        self.refresh_worker.moveToThread(self.refresh_thread)
        self.refresh_thread.started.connect(self.refresh_worker.run)
        self.refresh_worker.finished.connect(self.on_refresh_finished)
        self.refresh_worker.failed.connect(self.on_refresh_failed)
        self.refresh_worker.finished.connect(self.refresh_thread.quit)
        self.refresh_worker.failed.connect(self.refresh_thread.quit)
        self.refresh_thread.finished.connect(self.refresh_worker.deleteLater)
        self.refresh_thread.finished.connect(self.cleanup_refresh_thread)
        self.refresh_thread.start()

    @Slot()
    def check_scheduled_refresh(self) -> None:
        if not self.settings_tab.scheduled_refresh_enabled():
            return

        now = datetime.now()
        current_time = now.strftime("%H:%M")
        if current_time not in set(self.settings_tab.scheduled_refresh_times()):
            return

        refresh_key = f"{now.date().isoformat()} {current_time}"
        if refresh_key == self.last_scheduled_refresh_key:
            return

        self.last_scheduled_refresh_key = refresh_key
        self.refresh_rates()

    @Slot()
    def reset_scheduled_refresh_guard(self) -> None:
        self.last_scheduled_refresh_key = ""

    @Slot(object)
    def on_refresh_finished(self, snapshot: RateSnapshot) -> None:
        self.apply_snapshot(snapshot)
        self.reload_saved_data()
        self.play_notification_sound()
        if snapshot.warning:
            QMessageBox.warning(self, "Rates warning", snapshot.warning)

    @Slot(str)
    def on_refresh_failed(self, message: str) -> None:
        cached = self.manager.latest_or_none()
        if cached is not None:
            self.apply_snapshot(cached)
            QMessageBox.warning(self, "Offline mode", f"No internet connection. Using last saved data.\n\n{message}")
        else:
            QMessageBox.critical(self, "Rates unavailable", message)

    @Slot()
    def cleanup_refresh_thread(self) -> None:
        self.main_tab.set_loading(False)
        self.refresh_worker = None
        if self.refresh_thread is not None:
            self.refresh_thread.deleteLater()
        self.refresh_thread = None

    def apply_snapshot(self, snapshot: RateSnapshot) -> None:
        comparison_snapshot = self.cache.get_latest_snapshot_before_date(date.today())
        self.main_tab.set_snapshot(snapshot, comparison_snapshot)

    def play_notification_sound(self) -> None:
        if not self.settings_tab.notification_sound_enabled():
            return

        sound_path = _resource_path(NOTIFICATION_SOUND_PATH)
        if not sound_path.exists():
            return

        self.notification_player.setSource(QUrl.fromLocalFile(str(sound_path)))
        self.notification_player.play()

    @Slot()
    def reload_log(self) -> None:
        self.reload_saved_data()

    def reload_saved_data(self) -> None:
        snapshots = self.cache.list_snapshots()
        self.log_tab.set_snapshots(snapshots)
        self.chart_tab.set_snapshots(snapshots)

    @Slot()
    def clear_cache(self) -> None:
        answer = QMessageBox.question(self, "Clear cache", "Clear all saved rate records?")
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.cache.clear()
        self.main_tab.clear_snapshot()
        self.log_tab.set_snapshots([])
        self.chart_tab.set_snapshots([])
        QMessageBox.information(self, "Cache cleared", "Saved rate records were cleared.")

    @Slot()
    def open_database(self) -> None:
        try:
            os.startfile(str(self.cache.database_path))
        except OSError as exc:
            QMessageBox.warning(self, "Open database", str(exc))


def _resource_path(relative_path: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base_path / relative_path
