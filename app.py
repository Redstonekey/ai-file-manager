import sys
from PyQt5.QtWidgets import QApplication
from ui import FileManagerUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileManagerUI()
    window.show()
    sys.exit(app.exec_())
