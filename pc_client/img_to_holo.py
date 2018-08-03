# -*- coding: utf-8 -*-
"""
The Holography algorithms are here, in the class ImgToHolo.

No threading, no Qt in here.

Created on 03.08.2018
"""

import numpy
from pc_client.holo_globals import ProcessingStep

class ImgToHolo:
    """
    This class contains a camera image which can be evaluated to a Hologram.
    The image is a member, so that it can be quickly re-evaluated with different processing settings.
    """
    def __init__(self, laser_lambda_m, pixel_size_m):
        self.laser_lambda_m = laser_lambda_m
        self.pixel_size_m = pixel_size_m

        self.cam_image = numpy.zeros((10,10))

        self.fft_rect_center_yx = [512, 920]  # TODO Hardcoded #2
        self.fft_rect_radius = 35

    def set_image(self, ndarray):
        self.cam_image = ndarray

    def process_image(self, processing_step):
        if processing_step == ProcessingStep.STEP_CAM_IMAGE:
            return self.cam_image

        # (Forward) FFT:
        fft = numpy.fft.fftshift(numpy.fft.fft2(self.cam_image))

        if processing_step == ProcessingStep.STEP_FFT:
            y, x = self.fft_rect_center_yx
            r = self.fft_rect_radius
            fft_for_display = numpy.log(numpy.abs(fft))
            fft_for_display[y-r:y+r, x-r:x+r] *= 2
            return fft_for_display.copy()

        fft_shifted = self.shift_fft(fft)

        if processing_step == ProcessingStep.STEP_VIS_PHASES_RAW:
            return numpy.log(numpy.abs(fft_shifted))

    def crop_fft(self, fft):
        y, x = self.fft_rect_center_yx
        r = self.fft_rect_radius
        return fft[y-r:y+r, x-r:x+r]

    def shift_fft(self, fft):
        h, w = fft.shape
        r = self.fft_rect_radius
        fft_shifted = numpy.zeros_like(fft)
        fft_shifted[h//2-r:h//2+r, w//2-r:w//2+r] = self.crop_fft(fft)
        return fft_shifted


if __name__ == '__main__':
    import scipy.misc
    import pylab

    img = scipy.misc.imread("dump.tiff")

    worker = ImgToHolo(633e-9, 5e-6)
    worker.set_image(img)
    ret = worker.process_image(ProcessingStep.STEP_FFT)

    pylab.imshow(ret)
    pylab.show()