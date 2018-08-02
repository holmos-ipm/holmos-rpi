# -*- coding: utf-8 -*-
"""
Created on 02.08.2018
"""

import PyQt5.QtGui as QtGui
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets


class HolmosClientUI(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.label_display = QtWidgets.QLabel()  # main Display
        self.setCentralWidget(self.label_display)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)

    win = HolmosClientUI()
    win.show()

    sys.exit(app.exec_())
