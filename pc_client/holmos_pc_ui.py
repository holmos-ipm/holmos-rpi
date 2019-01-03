# -*- coding: utf-8 -*-
"""
Created on 02.08.2018
"""

import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets

from pc_client.holo_globals import ProcessingStep


class HolmosClientUI(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.label_display = QtWidgets.QLabel()  # main Display
        self.label_display.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        dummy_pixmap = QtGui.QPixmap(512, 512)
        self.label_display.setPixmap(dummy_pixmap)
        self.setCentralWidget(self.label_display)

        # Control Widgets
        self.modes = ModeSelector()
        self._mode_widget = QtWidgets.QDockWidget("Modes")
        self._mode_widget.setWidget(self.modes)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self._mode_widget)


class ModeSelector(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setWindowTitle("Modes")

        self._main_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self._main_layout)

        # camera mode
        _cam_mode_widget = QtWidgets.QWidget()
        _cam_mode_layout = QtWidgets.QVBoxLayout(self)
        _cam_mode_widget.setLayout(_cam_mode_layout)
        _cam_mode_layout.addWidget(QtWidgets.QLabel("Camera mode:"))
        self.btn_cam_stream = QtWidgets.QRadioButton("fast MJPEG stream")
        self.btn_cam_raw = QtWidgets.QRadioButton("hifi raw images")
        self.btn_cam_stream.setChecked(True)
        for btn in (self.btn_cam_stream, self.btn_cam_raw):
            _cam_mode_layout.addWidget(btn)

        # processing mode
        _proc_mode_widget = QtWidgets.QWidget()
        _proc_mode_layout = QtWidgets.QVBoxLayout(self)
        _proc_mode_widget.setLayout(_proc_mode_layout)
        _proc_mode_layout.addWidget(QtWidgets.QLabel("Processing mode:"))
        self.btn_raw = QtWidgets.QRadioButton("raw")
        self.btn_fft = QtWidgets.QRadioButton("FFT")
        self.btn_holo = QtWidgets.QRadioButton("Hologram")
        self.btn_raw.setChecked(True)
        for btn in (self.btn_raw, self.btn_fft, self.btn_holo):
            _proc_mode_layout.addWidget(btn)

        # combine everything
        self._main_layout.addWidget(_cam_mode_widget)
        self._main_layout.addWidget(_proc_mode_widget)
        vertical_spacer = QtWidgets.QSpacerItem(1,1,QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self._main_layout.addItem(vertical_spacer)

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
    win = HolmosClientUI()
    win.show()

    sys.exit(app.exec_())

