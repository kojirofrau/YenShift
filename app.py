import os
import sys
import tempfile
import ctypes
from pathlib import Path

from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication


def _ensure_matplotlib_config_dir() -> None:
    if "MPLCONFIGDIR" in os.environ:
        return

    candidates = [
        Path(base) / "YenShift" / "matplotlib"
        for base in (os.environ.get("APPDATA"), os.environ.get("LOCALAPPDATA"))
        if base
    ]
    candidates.append(Path(tempfile.gettempdir()) / "YenShift" / "matplotlib")

    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            os.environ["MPLCONFIGDIR"] = str(candidate)
            return
        except OSError:
            continue


_ensure_matplotlib_config_dir()

from ui.main_window import MainWindow


def _resource_path(relative_path: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_path / relative_path


def _set_windows_app_id() -> None:
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("YenShift.YenShift")
    except OSError:
        pass


def run() -> int:
    _set_windows_app_id()

    app = QApplication(sys.argv)
    app.setApplicationName("YenShift")
    app.setOrganizationName("YenShift")
    app.setFont(QFont("Montserrat", 9))

    icon = QIcon(str(_resource_path("assets/icons/yenshift_petal.ico")))
    app.setWindowIcon(icon)

    window = MainWindow()
    window.setWindowIcon(icon)
    window.show()

    return app.exec()
