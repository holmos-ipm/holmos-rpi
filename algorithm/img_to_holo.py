# -*- coding: utf-8 -*-
"""
The Holography algorithm are here, in the class ImgToHolo.

No threading, no Qt in here. Indices are Image-like, i.e. y,x (and not Qt-like x,y)

Created on 03.08.2018
"""
import time

import numpy
from algorithm.holo_globals import ProcessingStep


class ImgToHolo:
    """
    This class contains a camera image which can be evaluated to a Hologram.
    The image is a member, so that it can be quickly re-evaluated with different processing settings.
    """
    def __init__(self, laser_lambda_m, pixel_size_m):
        self.laser_lambda_m = laser_lambda_m
        self.pixel_size_m = pixel_size_m

        self.cam_image = numpy.zeros((10,10))

        self.fft_carrier_yxr_rel = [.5, .8, 35/1232]  # given in relative terms (DC at .5,.5) -> independent of image size.

        self.logger = lambda s: s  # do nothing.
        self.size_reduction = 1  # (integer!) factor to reduce size by. 1: full size

    def set_image(self, ndarray):
        self.cam_image = ndarray

    def set_fft_carrier(self, yx=None, r=None):
        """sets location of diffraction term in Fourier space, i.e. carrier frequency, i.e center of area to evaluate
        x,y are 0..1 in the shifted FFT: the DC term is at (.5, .5)"""
        if yx is not None:
            self.fft_carrier_yxr_rel[0:2] = yx
        if r is not None:
            self.fft_carrier_yxr_rel[2] = r

    def process_image(self, processing_step):
        tic = time.time()
        if processing_step == ProcessingStep.STEP_CAM_IMAGE:
            self.logger("return cam image (size reduction {}): {:.1f} s".format(self.size_reduction, time.time()-tic))
            return self.cam_image[::self.size_reduction, ::self.size_reduction]

        if processing_step == ProcessingStep.STEP_FFT:
            h, w = self.cam_image.shape
            h_out = h//self.size_reduction
            w_out = w//self.size_reduction

            fft = numpy.fft.fftshift(numpy.fft.fft2(self.cam_image[h//2-h_out//2: h//2+h_out//2:,
                                                                   w//2-w_out//2: w//2+w_out//2]))  # center of image shows good fringes for FFT

            self.logger("return fft: {:.1f} s".format(time.time()-tic))
            return self.highlight_fft_carrier(fft)

        # need forward fft at full resolution; only inverse may (optionally) be at half res
        fft = numpy.fft.fftshift(numpy.fft.fft2(self.cam_image))
        fft_centered = self.move_diffraction_order_to_center(fft)

        holo = numpy.fft.ifft2(numpy.fft.ifftshift(fft_centered))
        h, w = holo.shape
        holo /= numpy.average(holo[h//2-5:h//2+5, w//2-5:w//2+5])  # Todo: make optional/settable

        if processing_step == ProcessingStep.STEP_VIS_PHASES_RAW:
            self.logger("return phase: {:.1f} s".format(time.time()-tic))
            return numpy.angle(holo)

    def crop_fft(self, fft, size_reduction=None):
        y, x, ry, rx= self.fft_rect_center_yxrr_px(size_reduction=size_reduction)
        return fft[y-ry:y+ry, x-rx:x+rx]

    def move_diffraction_order_to_center(self, fft):
        # cut diffraction order from (full-res) fft and paste into (reduced res) fft center
        _, _, ry, rx = self.fft_rect_center_yxrr_px(size_reduction=1)  # here, have full size always, even for half-sized output.
        h, w = fft.shape
        h //= self.size_reduction
        w //= self.size_reduction
        fft_shifted = numpy.zeros((h, w), dtype=fft.dtype)
        fft_shifted[h//2-ry:h//2+ry, w//2-rx:w//2+rx] = self.crop_fft(fft, size_reduction=1)
        return fft_shifted

    def fft_rect_center_yxrr_px(self, size_reduction=None):
        """integer yx coordinates of fft carrier
        if halfsize=None, uses instance member as default"""
        y_rel, x_rel, r_rel = self.fft_carrier_yxr_rel
        h, w = self.cam_image.shape
        if size_reduction is None:
            size_reduction = self.size_reduction
        h //= size_reduction
        w //= size_reduction
        return int(y_rel*h), int(x_rel*w), int(r_rel*h), int(r_rel*w)

    def highlight_fft_carrier(self, fft):
        """log of fft; highlight diffcation order."""
        y, x, ry, rx = self.fft_rect_center_yxrr_px()
        fft_for_display = numpy.log(numpy.abs(fft))
        fft_for_display[y-ry:y+ry, x-rx:x+rx] *= 2
        return fft_for_display


if __name__ == '__main__':
    import scipy.misc
    import pylab

    img = scipy.misc.imread("dump.tiff")

    worker = ImgToHolo(633e-9, 5e-6)
    worker.set_image(img)
    ret = worker.process_image(ProcessingStep.STEP_FFT)

    pylab.imshow(ret)
    pylab.show()
