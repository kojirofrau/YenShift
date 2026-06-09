import os
import sys
import tempfile
import ctypes
from pathlib import Path

from PySide6.QtCore import QByteArray
from PySide6.QtGui import QFont, QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
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


INSTANCE_SERVER_NAME = "YenShift.SingleInstance"
INSTANCE_MESSAGE = b"already-running"


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
    app.setQuitOnLastWindowClosed(False)
    app.setFont(QFont("Montserrat", 9))

    if _notify_existing_instance():
        return 0

    icon = QIcon(str(_resource_path("assets/icons/yenshift_petal.ico")))
    app.setWindowIcon(icon)

    instance_server = _create_instance_server()
    window = MainWindow(icon)
    window.setWindowIcon(icon)

    def handle_instance_message() -> None:
        while instance_server.hasPendingConnections():
            socket = instance_server.nextPendingConnection()
            socket.readyRead.connect(lambda active_socket=socket: _read_instance_message(active_socket, window))
            if socket.bytesAvailable():
                _read_instance_message(socket, window)

    instance_server.newConnection.connect(handle_instance_message)
    window.show()

    return app.exec()


def _notify_existing_instance() -> bool:
    socket = QLocalSocket()
    socket.connectToServer(INSTANCE_SERVER_NAME)
    if not socket.waitForConnected(250):
        return False

    socket.write(QByteArray(INSTANCE_MESSAGE))
    socket.flush()
    socket.waitForBytesWritten(250)
    socket.disconnectFromServer()
    return True


def _create_instance_server() -> QLocalServer:
    server = QLocalServer()
    if not server.listen(INSTANCE_SERVER_NAME):
        QLocalServer.removeServer(INSTANCE_SERVER_NAME)
        server.listen(INSTANCE_SERVER_NAME)
    return server


def _read_instance_message(socket: QLocalSocket, window: MainWindow) -> None:
    message = bytes(socket.readAll())
    socket.disconnectFromServer()
    socket.deleteLater()
    if message == INSTANCE_MESSAGE:
        window.notify_already_running()
