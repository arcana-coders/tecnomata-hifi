"""Tecnomata Hi-Fi — Reproductor retro de escritorio para Navidrome."""
import sys
import os
import traceback
from datetime import datetime
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from src.app import HiFiApp


def setup_exception_handler():
    """Captura excepciones no controladas y las escribe en crash.log para evitar cierres invisibles."""
    log_dir = os.path.join(os.path.expanduser("~"), ".config", "tecnomata-hifi")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "crash.log")

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"CRASH AT {datetime.now().isoformat()}\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
            f.write(f"{'='*50}\n")

        print("Error no controlado registrado en crash.log:", exc_value, file=sys.stderr)

    sys.excepthook = handle_exception


def main():
    setup_exception_handler()

    app = QApplication(sys.argv)
    app.setApplicationName("Tecnomata Hi-Fi")
    app.setOrganizationName("Tecnomata")
    app.setQuitOnLastWindowClosed(False)

    # Establecer ícono oficial de la aplicación
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    hifi = HiFiApp()
    app.aboutToQuit.connect(hifi.cleanup)
    hifi.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
