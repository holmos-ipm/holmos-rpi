# -*- coding: utf-8 -*-
"""
Created on 02.08.2018
"""
import threading

import numpy
import scipy.misc

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

from pc_client.holmos_pc_ui import HolmosClientUI
from pc_client.holo_globals import ProcessingStep
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

        # Control Widgets
        self._modes = ModeSelector()
        self._mode_widget = QtWidgets.QDockWidget(self)
        self._mode_widget.setWidget(self._modes)
        self._mode_widget.show()

        self._worker = ImgToHolo(633e-9, 2e-6)

        self._image_grabber.start()

    def __del__(self):
        print("stopping")

    @QtCore.pyqtSlot('PyQt_PyObject')
    def display_image(self, ndarray):
        scipy.misc.imsave("dump.tiff", ndarray)

        # TODO: move to other thread
        self._worker.set_image(ndarray)
        processing_step = self._modes.processing_step()
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


class ModeSelector(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Modes")

        self._main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self._main_layout)

        self.btn_raw = QtWidgets.QRadioButton("raw")
        self.btn_fft = QtWidgets.QRadioButton("FFT")
        self.btn_holo = QtWidgets.QRadioButton("Hologram")
        self.btn_raw.setChecked(True)
        for btn in (self.btn_raw, self.btn_fft, self.btn_holo):
            self._main_layout.addWidget(btn)

    def processing_step(self):
        if self.btn_raw.isChecked():
            return ProcessingStep.STEP_CAM_IMAGE
        if self.btn_fft.isChecked():
            return ProcessingStep.STEP_FFT
        if self.btn_holo.isChecked():
            return ProcessingStep.STEP_VIS_PHASES_RAW


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



