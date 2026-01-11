import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from PySide6.QtWidgets import QApplication
from organizer.ui import FileOrganizerUI


def main():
    app = QApplication(sys.argv)
    win = FileOrganizerUI()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
