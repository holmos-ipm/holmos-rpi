# -*- coding: utf-8 -*-
"""
The Holography algorithms are here, in the class ImgToHolo.

No threading, no Qt in here. Indices are Image-like, i.e. y,x (and not Qt-like x,y)

Created on 03.08.2018
"""
import os
import time

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

        self.fft_carrier_yx_rel = (.5, .8)  # given in relative terms (DC at .5,.5) -> independent of image size.
        self.fft_rect_radius = 35

    def set_image(self, ndarray):
        self.cam_image = ndarray

    def set_fft_carrier(self, yx):
        """sets location of diffraction term in Fourier space, i.e. carrier frequency, i.e center of area to evaluate
        x,y are 0..1 in the shifted FFT: the DC term is at (.5, .5)"""
        self.fft_carrier_yx_rel = yx

    def process_image(self, processing_step):
        tic = time.time()
        if processing_step == ProcessingStep.STEP_CAM_IMAGE:
            print(os.getpid(), "return cam image: {:.1f} s".format(time.time()-tic))
            return self.cam_image

        # (Forward) FFT:
        fft = numpy.fft.fftshift(numpy.fft.fft2(self.cam_image))

        if processing_step == ProcessingStep.STEP_FFT:
            y, x = self.fft_rect_center_yx_px()
            r = self.fft_rect_radius
            fft_for_display = numpy.log(numpy.abs(fft))
            fft_for_display[y-r:y+r, x-r:x+r] *= 2
            print(os.getpid(), "return fft: {:.1f} s".format(time.time()-tic))
            return fft_for_display

        fft_centered = self.move_diffraction_order_to_center(fft)

        holo = numpy.fft.ifft2(numpy.fft.ifftshift(fft_centered))

        if processing_step == ProcessingStep.STEP_VIS_PHASES_RAW:
            print(os.getpid(), "return phase: {:.1f} s".format(time.time()-tic))
            return numpy.angle(holo)

    def crop_fft(self, fft):
        y, x = self.fft_rect_center_yx_px()
        r = self.fft_rect_radius
        return fft[y-r:y+r, x-r:x+r]

    def move_diffraction_order_to_center(self, fft):
        h, w = fft.shape
        r = self.fft_rect_radius
        fft_shifted = numpy.zeros_like(fft)
        fft_shifted[h//2-r:h//2+r, w//2-r:w//2+r] = self.crop_fft(fft)
        return fft_shifted

    def fft_rect_center_yx_px(self):
        """integer yx coordinates of fft carrier"""
        y_rel, x_rel = self.fft_carrier_yx_rel
        h, w = self.cam_image.shape
        return int(y_rel*h), int(x_rel*w)


if __name__ == '__main__':
    import scipy.misc
    import pylab

    img = scipy.misc.imread("dump.tiff")

    worker = ImgToHolo(633e-9, 5e-6)
    worker.set_image(img)
    ret = worker.process_image(ProcessingStep.STEP_FFT)

    pylab.imshow(ret)
    pylab.show()
