import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt
import FFXIVcraftPricing as XIVcp


BASE_TITLE = "XIV Craft Pricing"


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data
        self.columns = ["Item", "Amount", "P(c)", "P(b)"]
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.columns[section]
        if orientation == Qt.Orientation.Vertical and role == Qt.ItemDataRole.DisplayRole:
            return ""
    
    def data(self, index: QtCore.QModelIndex, role: int = ...):
        if role == Qt.ItemDataRole.DisplayRole:
            return self._data[index.row()][index.column()]
            
        if role == Qt.ItemDataRole.TextAlignmentRole:
            value = self._data[index.row()][index.column()]
            
            if isinstance(value, int) or isinstance(value, float):
                return Qt.AlignmentFlag.AlignVCenter + Qt.AlignmentFlag.AlignRight
                
        if role == Qt.ItemDataRole.BackgroundRole:
            value = self._data[index.row()][index.column()]
            if index.column() == 2:
                if value <= int(self._data[index.row()][index.column()+1] or 0):
                    return QtGui.QColor('#f1ffe8')

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
        
        for itm in data.get('ingredients'):
            name = itm.get('name')
            if itm.get('amount_result', 1) > 1:
                name += f" ({str(itm['amount_result'])})"
            data_tbl.append([
                name, 
                itm.get('amount'), 
                itm.get('price'), 
                itm.get('price_if_crafted', '')
            ])
            
            for itm_itm in itm.get('ingredients'):
                data_tbl.append([
                    '    ' + itm_itm.get('name'), 
                    itm_itm.get('amount'), 
                    itm_itm.get('price'), 
                    itm_itm.get('price_if_crafted', '')
                ])

        icons = XIVcp.get_icon_list(data)
        XIVcp.get_icons(icons)

        self.model = TableModel(data_tbl)

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
