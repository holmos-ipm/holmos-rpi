# -*- coding: utf-8 -*-
"""
Created on 02.08.2018
"""
import threading

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

from pc_client.holmos_pc_ui import HolmosClientUI
from pc_client.network_image_grabber import RemoteImageGrabber


class HolmosMainWindoow(HolmosClientUI):
    def __init__(self):
        super().__init__()

        self.show()

        self._image_grabber = RemoteImageGrabber(None, '10.82.202.30')

        self._image_grabber.refresh_preview.connect(self.display_image)

        self._image_grabber.start()

    @QtCore.pyqtSlot('PyQt_PyObject')
    def display_image(self, ndarray):
        h, w = ndarray.shape
        image = QtGui.QImage(ndarray.data, w, h, QtGui.QImage.Format_Grayscale8)
        pixmap = QtGui.QPixmap.fromImage(image)
        #pixmap = pixmap.scaledToWidth(self.height / 2)
        print("almost there... in {}".format(threading.current_thread()))
        self.label_display.setPixmap(image)


if __name__ == '__main__':
    import sys

    def except_hook(cls, exception, traceback):
    # PyQt5 has changed how it handles exceptions, this restores printing traceback to IDEs
    # https://stackoverflow.com/questions/33736819/pyqt-no-error-msg-traceback-on-exit
        sys.__excepthook__(cls, exception, traceback)
        exit()
    sys.excepthook = except_hook

    app = QtWidgets.QApplication(sys.argv)
    win = HolmosMainWindoow()
    sys.exit(app.exec_())



