import sys
from PySide6 import QtCore, QtWidgets, QtGui
import FFXIVcraftPricing as XIVCP


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        
        # layout
        self.main_frame = QtWidgets.QFrame(self)
        self.layout_wrapper = QtWidgets.QVBoxLayout(self.main_frame)
        self.layout_search = QtWidgets.QHBoxLayout(self.layout_wrapper)
        
        # elements
        self.txt_query = QtWidgets.QLineEdit("", placeholderText="Enter item name")
        self.btn_submit = QtWidgets.QPushButton("search")
        self.txt_processing = QtWidgets.QLabel("results come here", alignment=QtCore.Qt.AlignCenter)
        self.txt_result = QtWidgets.QLabel("", alignment=QtCore.Qt.AlignLeft)
        
        # add elements to layout
        self.layout_search.addWidget(self.txt_query)
        self.layout_search.addWidget(self.btn_submit)
        
        self.layout_wrapper.addWidget(self.txt_result)

        self.btn_submit.clicked.connect(self.search)

    @QtCore.Slot()
    def search(self):
        self.query = self.txt_query.text()
        self.txt_result.setText(sys.stdout)
        self.txt_result.setText(XIVCP.generate_result(self.query))
        

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())