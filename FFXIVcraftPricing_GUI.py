import os.path
import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt
import pathlib
import FFXIVcraftPricing as XIVcp


BASE_TITLE = "XIV Craft Pricing"


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Search bar + submit button at the top
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search item...")
        self.submit_btn = QtWidgets.QPushButton('Search', self)
        self.submit_btn.setIcon(QtGui.QIcon())
        self.submit_btn.clicked.connect(self.search_item)
        self.header_layout = QtWidgets.QHBoxLayout()
        self.header_layout.addWidget(self.search_bar)
        self.header_layout.addWidget(self.submit_btn)

        # Containers
        self.centralWidget = QtWidgets.QWidget(parent=self)
        self.centralWidget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.header_layout)

        # Tree for results in the middle of the window
        self.tree = QtWidgets.QTreeWidget(parent=self.centralWidget)
        self.layout.addWidget(self.tree)
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Item", "Amount", "MB", "craft"])

        # Window layout
        self.setWindowTitle(BASE_TITLE)
        self.setWindowIcon(QtGui.QIcon('icon'))
        self.setBaseSize(300, 200)
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)

        # Styles
        self.tree.header().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tree.setStyleSheet('''
                    QTreeView::item {
                        border-right: 1px solid #eeeeee;
                    }
                    QTreeView::item:hover {
                        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);
                        border: 1px solid #bfcde4;
                    }
                ''')
        self.light_green = QtGui.QColor("#E0FAD0")
        self.dark_red = QtGui.QColor("#9C0000")

    def search_item(self):
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Loading...")
        QtWidgets.QApplication.processEvents()  # Force interface update

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
        tree_items = QtWidgets.QTreeWidgetItem([data.get('name')])
        rows = 1  # 1 because the top level node is not counted in the loop
        align_right = Qt.AlignmentFlag.AlignRight
        monospace_font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont)
        for itm in data.get('ingredients'):
            name = itm.get('name')
            item = QtWidgets.QTreeWidgetItem([
                name + (f' ({itm.get("amount_result")})' if itm.get("amount_result", 1) > 1 else 'p'),
                str(itm.get('amount')),
                str(itm.get('price')),
                str(itm.get('price_if_crafted', ''))
            ])
            craft = False
            # Paint the cheaper variant (buy from MB vs. craft yourself) green
            if itm.get('price', 1e9) < itm.get('price_if_crafted', 1e9):
                item.setBackground(2, self.light_green)
            elif itm.get('price', 1e9) > itm.get('price_if_crafted', 1e9):
                item.setBackground(3, self.light_green)
                craft = True

            # Align numbers right and set monospace font
            item.setTextAlignment(1, align_right)
            item.setTextAlignment(2, align_right)
            item.setTextAlignment(3, align_right)
            item.setFont(1, monospace_font)
            item.setFont(2, monospace_font)
            item.setFont(3, monospace_font)

            for itm_itm in itm.get('ingredients'):
                name_2 = itm_itm.get('name')
                item_2 = QtWidgets.QTreeWidgetItem([
                    name_2,
                    str(itm_itm.get('amount')),
                    str(itm_itm.get('price')),
                    str(itm_itm.get('price_if_crafted', ''))
                ])
                # Paint ingredients green if cheaper, else paint text red
                if craft:
                    item_2.setBackground(2, self.light_green)
                else:
                    item_2.setForeground(0, self.dark_red)

                # Align numbers right and set monospace font
                item_2.setTextAlignment(1, align_right)
                item_2.setTextAlignment(2, align_right)
                item_2.setTextAlignment(3, align_right)
                item_2.setFont(1, monospace_font)
                item_2.setFont(2, monospace_font)
                item_2.setFont(3, monospace_font)

                item_2.setIcon(0, QtGui.QIcon('cache/icons/' + itm_itm.get('icon').split('/')[-1]))
                rows += 1
                item.addChild(item_2)
            item.setIcon(0, QtGui.QIcon('cache/icons/' + itm.get('icon').split('/')[-1]))
            rows += 1
            tree_items.addChild(item)

        icon_p = ('cache/icons/' + data.get('icon').split('/')[-1])
        QtWidgets.QApplication.processEvents()  # Force interface update
        self.setWindowIcon(QtGui.QIcon(icon_p))
        self.tree.insertTopLevelItems(0, [tree_items])
        self.tree.expandAll()
        self.tree.itemClicked.connect(self.on_tree_item_clicked)

        # Set column width to fit contents
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.tree.setColumnWidth(3, 50)

        # Resize window to fit contents
        self.tree.show()
        width = (self.tree.columnWidth(0) +
                 self.tree.columnWidth(1) +
                 self.tree.columnWidth(2) +
                 self.tree.columnWidth(3) +
                 30)  # window border
        height = rows * 22 + self.tree.header().sizeHint().height() + self.header_layout.sizeHint().height() + 30

        self.setFixedSize(width, height)
        QtWidgets.QApplication.processEvents()  # Force interface update

        # Re-enable search button
        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("Search")
        self.submit_btn.setIcon(QtGui.QIcon())

    @QtCore.pyqtSlot(QtWidgets.QTreeWidgetItem, int)
    def on_tree_item_clicked(self, item, column):
        # TODO: check if this item is craftable as well. If it's craftable, fetch data and append as children
        print(item, column, item.text(column))


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
