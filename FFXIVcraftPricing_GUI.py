import os.path
import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt
import pathlib
import FFXIVcraftPricing as XIVcp


BASE_TITLE = "XIV Craft Pricing"


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, lookup):
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
            icon_name = self.icon_lookup.get(value)
            cwd = str(pathlib.Path(__file__).parent.absolute())
            icon_path = cwd + '/cache/icons/' + icon_name
            icon = QtGui.QIcon(icon_path)
            return icon

    def rowCount(self, index: int = ...):
        return len(self._data)

    def columnCount(self, index: int = ...):
        return len(self._data[0])


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()     
        
        self.setWindowTitle(BASE_TITLE)
        self.setFixedSize(500, 500)

        self.table = QtWidgets.QTableView()

        search_str = "Acqua Pazza"
        self.setWindowTitle(BASE_TITLE + ' - ' + search_str)

        # data = XIVcp.generate_result(search_str)
        with open('tmp.json', 'r', encoding="utf-8") as f:
            import json
            # f.write(json.dumps(data))
            data = json.loads(f.read())

        data_tbl = []
        lookup_tbl = {data.get('name'): data.get('icon')[0].split('/')[-1]}
        
        for itm in data.get('ingredients'):
            name = itm.get('name')
            data_tbl.append([
                name, 
                itm.get('amount'), 
                itm.get('price'), 
                itm.get('price_if_crafted', '')
            ])
            lookup_tbl[name] = itm.get('icon').split('/')[-1]
            
            for itm_itm in itm.get('ingredients'):
                data_tbl.append([
                    '    ' + itm_itm.get('name'), 
                    itm_itm.get('amount'), 
                    itm_itm.get('price'), 
                    itm_itm.get('price_if_crafted', '')
                ])
                lookup_tbl[itm_itm.get('name')] = itm_itm.get('icon').split('/')[-1]

        icons = XIVcp.get_icon_list(data)
        XIVcp.get_icons(icons)
        self.setWindowIcon(QtGui.QIcon('cache/icons/' + lookup_tbl.get(search_str)))

        self.model = TableModel(data_tbl, lookup_tbl)

        self.table.setModel(self.model)
        self.setCentralWidget(self.table)
        
        header = self.table.horizontalHeader() 
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Fixed)

        # window with = 500. half the width is shared between 3 cols.
        header.resizeSection(1, int(500/2/3))
        header.resizeSection(2, int(500/2/3))
        header.resizeSection(3, int(500/2/3))


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
