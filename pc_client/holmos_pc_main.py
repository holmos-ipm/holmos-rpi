# -*- coding: utf-8 -*-
"""
Created on 02.08.2018
"""

import numpy
import scipy.misc

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

from pc_client.holmos_pc_ui import HolmosClientUI, ModeSelector
from pc_client.img_to_holo import ImgToHolo
from pc_client.network_image_grabber import RemoteImageGrabber


class HolmosMainWindoow(HolmosClientUI):
    def __init__(self):
        super().__init__()

        self.show()

        # Imagge Grabber (is its own thread)
        self._image_grabber = RemoteImageGrabber(None, '10.82.202.30')
        self._image_grabber.refresh_preview.connect(self.display_image)
        self._image_grabber.refresh_3d_sig.connect(self.display_image)

        self._worker = ImgToHolo(633e-9, 2e-6)

        self._image_grabber.start()

    def __del__(self):
        print("stopping")

    @QtCore.pyqtSlot('PyQt_PyObject')
    def display_image(self, ndarray):
        scipy.misc.imsave("dump.tiff", ndarray)

        # TODO: move to other thread
        self._worker.set_image(ndarray)
        processing_step = self.modes.processing_step()
        ndarray = self._worker.process_image(processing_step)
        scipy.misc.imsave("dump_processed.tiff", ndarray)
        #
        if ndarray is not None:
            if ndarray.dtype != numpy.uint8: # scale to 0..255 for QImage conversion
                ndarray -= numpy.min(ndarray)
                ndarray *= 2**8 / numpy.max(ndarray)
                ndarray = ndarray.astype(numpy.uint8)

            h, w = ndarray.shape
            image = QtGui.QImage(ndarray.data, w, h, QtGui.QImage.Format_Grayscale8)
            pixmap = QtGui.QPixmap.fromImage(image)
            self.label_display.setPixmap(pixmap)


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



