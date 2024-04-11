# main.py
import sys
from PyQt5.QtWidgets import QApplication
from gui.gui import PDFExtractorGUI

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PDFExtractorGUI()
    sys.exit(app.exec_())