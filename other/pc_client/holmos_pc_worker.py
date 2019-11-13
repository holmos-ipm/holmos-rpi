# -*- coding: utf-8 -*-
"""
Created on 07.08.2018

@author: beckmann
"""
import threading

import PyQt5.QtCore as QtCore

from algorithm.img_to_holo import ImgToHolo


class HolmosWorker(QtCore.QObject):
    """Qt Wrapper around an ImgToholo"""

    sig_have_processed = QtCore.pyqtSignal('PyQt_PyObject')

    def __init__(self):
        super().__init__()
        self._ith = ImgToHolo(633e-9, 2e-6)

    def set_image(self, ndarray):
        self._ith.set_image(ndarray)

    def fft_rect_center_yx_px(self, xy):  # takes xy
        self._ith.set_fft_carrier((xy[1], xy[0]))  # takes yx

    def process_image(self, processing_step):
        print("starting image processing in {}".format(threading.current_thread()))
        result = self._ith.process_image(processing_step)

        self.sig_have_processed.emit(result.copy())