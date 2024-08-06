import os.path
import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt
import pathlib
import FFXIVcraftPricing as XIVcp


BASE_TITLE = "XIV Craft Pricing"


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data=None, lookup=None):
        super(TableModel, self).__init__()
        self._data = data
        self.icon_lookup = lookup
        self.columns = ["Item", "Amount", "P(c)", "P(b)"]
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.columns[section]
        if orientation == Qt.Orientation.Vertical and role == Qt.ItemDataRole.DisplayRole:
            return ""
    
    def data(self, index: QtCore.QModelIndex, role: int = ...):
        if role == Qt.ItemDataRole.DisplayRole:
            return self._data[index.row()][index.column()]

        # Text Alignment
        if role == Qt.ItemDataRole.TextAlignmentRole:
            value = self._data[index.row()][index.column()]
            
            if isinstance(value, int) or isinstance(value, float):
                return Qt.AlignmentFlag.AlignVCenter + Qt.AlignmentFlag.AlignRight

        # Cell Background Color
        if role == Qt.ItemDataRole.BackgroundRole and index.column() == 2:
            value = self._data[index.row()][index.column()]
            if value <= int(self._data[index.row()][index.column()+1] or 0):
                return QtGui.QColor('#f1ffe8')

        # Cell Icon Decor
        if role == Qt.ItemDataRole.DecorationRole and index.column() == 0:
            value = self._data[index.row()][index.column()].strip()
            icon_name = self.icon_lookup.get(value).get('item_id')
            cwd = str(pathlib.Path(__file__).parent.absolute())
            icon_path = cwd + '/cache/icons/' + icon_name
            icon = QtGui.QIcon(icon_path).pixmap(40, 40)
            return icon

    def rowCount(self, index: int = ...):
        return len(self._data)

    def columnCount(self, index: int = ...):
        return len(self._data[0])


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.model = None
        search_str = "Acqua Pazza"

        # Search bar + submit button at the top
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search item...")
        self.submit_btn = QtWidgets.QPushButton('Submit', self)
        self.submit_btn.setIcon(QtGui.QIcon())
        self.submit_btn.clicked.connect(self.search_item)
        self.header_layout = QtWidgets.QHBoxLayout()
        self.header_layout.addWidget(self.search_bar)
        self.header_layout.addWidget(self.submit_btn)

        # Table for results in the middle
        self.table = QtWidgets.QTableView()

        # Window layout
        self.setWindowTitle(BASE_TITLE)
        self.setBaseSize(500, 500)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)
        self.setWindowIcon(QtGui.QIcon('icon'))
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.header_layout)
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

    def search_item(self):
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Loading...")
        QtWidgets.QApplication.processEvents()  # Force interface update

        text = self.search_bar.text()
        if len(text.strip()) == 0:
            return

        self.setWindowTitle(BASE_TITLE + ' - ' + text)

        data = XIVcp.generate_result(text)
        QtWidgets.QApplication.processEvents()  # Force interface update
        if data is None:
            print("Nothing found")
            self.submit_btn.setEnabled(True)
            return

        data_tbl = []
        lookup_tbl = {
            data.get('name'): {
                'icon_id': data.get('icon').split('/')[-1],
            }
        }

        for itm in data.get('ingredients'):
            name = itm.get('name')
            data_tbl.append([
                name,
                itm.get('amount'),
                itm.get('price'),
                itm.get('price_if_crafted', '')
            ])
            QtWidgets.QApplication.processEvents()  # Force interface update
            lookup_tbl[name] = {
                'item_id': itm.get('icon').split('/')[-1],
                'depth': 1
            }

            for itm_itm in itm.get('ingredients'):
                data_tbl.append([
                    '    ' + itm_itm.get('name'),
                    itm_itm.get('amount'),
                    itm_itm.get('price'),
                    itm_itm.get('price_if_crafted', '')
                ])
                QtWidgets.QApplication.processEvents()  # Force interface update
                lookup_tbl[itm_itm.get('name')] = {
                    'item_id': itm_itm.get('icon').split('/')[-1],
                    'depth': 2
                }

        icons = XIVcp.get_icon_list(data)
        QtWidgets.QApplication.processEvents()  # Force interface update
        XIVcp.cache_icons(icons)
        QtWidgets.QApplication.processEvents()  # Force interface update
        icon_p = 'cache/icons/' + lookup_tbl.get(text).get('icon_id')
        QtWidgets.QApplication.processEvents()  # Force interface update
        self.setWindowIcon(QtGui.QIcon(icon_p))
        self.model = TableModel(data_tbl, lookup_tbl)
        self.table.setModel(self.model)
        tbl_header = self.table.horizontalHeader()
        tbl_header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        tbl_header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Fixed)
        tbl_header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Fixed)
        tbl_header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Fixed)

        # window with = 500. half the width is shared between 3 cols.
        tbl_header.resizeSection(1, int(500 / 2 / 3))
        tbl_header.resizeSection(2, int(500 / 2 / 3))
        tbl_header.resizeSection(3, int(500 / 2 / 3))

        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("Submit")
        self.submit_btn.setIcon(QtGui.QIcon())


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
