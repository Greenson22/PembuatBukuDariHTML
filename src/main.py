import sys
from PyQt6.QtWidgets import QApplication
from main_window import HTMLMergerApp

def main():
    app = QApplication(sys.argv)
    window = HTMLMergerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()