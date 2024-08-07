import sys
from PyQt6 import QtCore, QtGui, QtWidgets
import FFXIVcraftPricing as XIVcp


BASE_TITLE = "XIV Craft Pricing"


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Search bar + submit button at the top
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search item...")
        self.submit_btn = QtWidgets.QPushButton('Submit', self)
        self.submit_btn.clicked.connect(self.search_item)
        self.header_layout = QtWidgets.QHBoxLayout()
        self.header_layout.addWidget(self.search_bar)
        self.header_layout.addWidget(self.submit_btn)

        # Tree for results in the middle of the window
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Item", "Amount", "P(c)", "P(b)"])
        self.tree.setStyleSheet('''
            QTreeView::item:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);
                border: 1px solid #bfcde4;
            }
        ''')

        # Window layout
        self.setWindowTitle(BASE_TITLE)
        self.setBaseSize(500, 500)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.setWindowIcon(QtGui.QIcon('icon'))
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.header_layout)
        self.layout.addWidget(self.tree)
        self.setLayout(self.layout)

    def search_item(self):
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Loading...")
        QtWidgets.QApplication.processEvents()  # Force interface update (disable button)

        text = self.search_bar.text()
        if len(text.strip()) == 0:
            return

        self.setWindowTitle(BASE_TITLE + ' - ' + text)

        data = XIVcp.generate_result(text)

        # Exit procedure if the search query did not return a valid result
        if data is None:
            popup = QtWidgets.QMessageBox.warning(self,
                                                  "Nothing found",
                                                  "Your query returned no results.\n"
                                                  "Please make sure to provide the item's full name."
                                                  )
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Search")
            return

        icons = XIVcp.get_icon_list(data)
        XIVcp.cache_icons(icons)

        self.tree.clear()
        tree_items = []
        for itm in data.get('ingredients'):
            name = itm.get('name')
            item = QtWidgets.QTreeWidgetItem([
                name,
                str(itm.get('amount')),
                str(itm.get('price')),
                str(itm.get('price_if_crafted', ''))
            ])
            for itm_itm in itm.get('ingredients'):
                name_2 = itm_itm.get('name')
                item_2 = QtWidgets.QTreeWidgetItem([
                    name_2,
                    str(itm_itm.get('amount')),
                    str(itm_itm.get('price')),
                    str(itm_itm.get('price_if_crafted', ''))
                ])
                item_2.setIcon(0, QtGui.QIcon('cache/icons/' + itm_itm.get('icon').split('/')[-1]))
                item.addChild(item_2)
            item.setIcon(0, QtGui.QIcon('cache/icons/' + itm.get('icon').split('/')[-1]))
            tree_items.append(item)

        icon_p = ('cache/icons/' + data.get('icon').split('/')[-1])
        QtWidgets.QApplication.processEvents()  # Force interface update
        self.setWindowIcon(QtGui.QIcon(icon_p))
        self.tree.insertTopLevelItems(0, tree_items)
        self.tree.expandAll()

        # Set column width
        self.tree.setColumnWidth(0, int(500 / 2))
        self.tree.setColumnWidth(1, int(500 / 2 / 3))
        self.tree.setColumnWidth(2, int(500 / 2 / 3))
        self.tree.setColumnWidth(3, int(500 / 2 / 3))
        QtWidgets.QApplication.processEvents()  # Force interface update

        # Resize window to fit contents
        self.tree.show()
        self.resize(self.sizeHint())
        QtWidgets.QApplication.processEvents()  # Force interface update

        # Re-enable search button
        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("Submit")


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
