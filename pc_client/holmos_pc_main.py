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
from pc_client.holmos_pc_worker import HolmosWorker
from pc_client.network_image_grabber import RemoteImageGrabber
from pc_client.holo_globals import ProcessingStep


class HolmosMainWindoow(HolmosClientUI):
    sig_get_bayer = QtCore.pyqtSignal()
    sig_process_images = QtCore.pyqtSignal('PyQt_PyObject')

    def __init__(self):
        super().__init__()

        self.show()

        # Imagge Grabber (is its own thread)
        self._image_grabber = RemoteImageGrabber(None, '10.82.202.30')
        self._image_grabber_thread = QtCore.QThread()
        self._image_grabber.moveToThread(self._image_grabber_thread)
        self._image_grabber_thread.start()

        self._image_grabber.refresh_preview.connect(self.receive_from_cam)
        self._image_grabber.refresh_3d_sig.connect(self.receive_from_cam)
        self.sig_get_bayer.connect(self._image_grabber.order_single_bayer_image)

        # Worker and worker thread
        self._worker = HolmosWorker()
        self._worker_thread = QtCore.QThread()
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.start()

        self.sig_process_images.connect(self._worker.process_image)
        self._worker.sig_have_processed.connect(self.display_image)

        # UI Connections
        self.label_display.mousePressEvent = self.image_clicked

        # Startup
        self.sig_get_bayer.emit()

        self._worker.set_image(scipy.misc.imread("dump.tiff"))

        timer = QtCore.QTimer(self)
        timer.setInterval(500)
        timer.timeout.connect(self.request_processed_image)
        timer.start()

    def __del__(self):
        print("stopping")

    def receive_from_cam(self, ndarray):
        scipy.misc.imsave("dump.tiff", ndarray)
        self._worker.set_image(ndarray)
        self.sig_get_bayer.emit()

    def request_processed_image(self):
        processing_step = self.modes.processing_step()
        print("requesting image processing")
        self.sig_process_images.emit(processing_step)

    @QtCore.pyqtSlot('PyQt_PyObject')
    def display_image(self, ndarray):
        if ndarray is not None:
            scipy.misc.imsave("dump_processed.tiff", ndarray)
            if ndarray.dtype != numpy.uint8: # scale to 0..255 for QImage conversion
                ndarray -= numpy.min(ndarray)
                max = numpy.max(ndarray)
                if max > 2**8:  # Todo: can this be done more elegantly (and still handle integers well)?
                    ndarray //= (max // 2**8)
                else:
                    ndarray *= (2**8 // max)
                ndarray = ndarray.astype(numpy.uint8)

            h, w = ndarray.shape
            image = QtGui.QImage(ndarray.data, w, h, QtGui.QImage.Format_Grayscale8)
            pixmap = QtGui.QPixmap.fromImage(image.scaled(*self.display_size()))
            self.label_display.setPixmap(pixmap)

    def display_size(self):
        size = min(self.label_display.size().height(), self.label_display.size().width())  # todo: non-square
        return (size, size)

    def image_clicked(self, mouse_event):
        assert isinstance(mouse_event, QtGui.QMouseEvent)
        xy_ui = mouse_event.x(), mouse_event.y()
        size_ui = self.display_size()
        size_rel = (1,1)
        xy_rel = scale_point_in_rect(xy_ui, size_ui, size_rel)
        if self.modes.processing_step() == ProcessingStep.STEP_FFT:
            self._worker.fft_rect_center_yx_px(xy_rel)


def scale_point_in_rect(xy_from, wh_from, wh_to):
    """
    scale a 2D point from one rectangle to another
    :param xy_from: point in "from" rectangle
    :param wh_from: size of "from" rectangle
    :param wh_to: size of "to" rectangle
    :return: (x_to, y_to) float(!) coordinates in "to" rectangle
    """
    return tuple(coord_from / size_from * size_to for coord_from, size_from, size_to in zip(xy_from, wh_from, wh_to))


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



