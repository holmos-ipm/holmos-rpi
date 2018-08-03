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

    def except_hook(cls, exception, traceback):
    # PyQt5 has changed how it handles exceptions, this restores printing traceback to IDEs
    # https://stackoverflow.com/questions/33736819/pyqt-no-error-msg-traceback-on-exit
        sys.__excepthook__(cls, exception, traceback)
        exit()
    sys.excepthook = except_hook

    app = QtWidgets.QApplication(sys.argv)
    win = HolmosClientUI()
    win.show()

    sys.exit(app.exec_())
