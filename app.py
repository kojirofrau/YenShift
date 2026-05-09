import os
import sys
import tempfile
from pathlib import Path

from PySide6.QtGui import QFont
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


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("YenShift")
    app.setOrganizationName("YenShift")
    app.setFont(QFont("Montserrat", 9))

    window = MainWindow()
    window.show()

    return app.exec()
