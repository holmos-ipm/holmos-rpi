# -*- coding: utf-8 -*-
"""
Created on 03.01.2019

@author: beckmann

holmos client for direct execution on rpi
developed for Raspberry Pi 3B
"""
import configparser
import os
import sys
import threading
import time
import multiprocessing
import warnings
from io import BytesIO

import cv2
from PIL import Image

from pc_client.img_to_holo import ImgToHolo

print("cv2 version", cv2.__version__)

import numpy

from pc_client.holo_globals import ProcessingStep

try:
    import picamera
    import picamera.array
except ImportError:
    print("Could not import picamera. Are we running on a Raspberry Pi?")
    exit()


w_full, h_full = 3280, 2464

KEY_FFT_X = "fft_x"  # TODO: use same as holo-software?
KEY_FFT_Y = "fft_y"


class HolmosPlot:
    """interactive matplotlib.figure"""
    w, h = w_full//2, h_full//2  # /2 because resulting images are R-channel only.
    fft_x = int(w*.8)
    fft_y = int(h*.5)
    num_ims = 0
    processing_step = ProcessingStep.STEP_CAM_IMAGE
    ini_path = "holmos_settings.ini"

    def __init__(self, im_pipe):
        self.im_pipe = im_pipe

        self.load_settings()

        self._ith = ImgToHolo(633e-9, 2e-6)
        self._ith.set_fft_carrier(None, r=120/self.w)
        self._ith.logger = lambda s: print(s)
        self._ith.halfsize_output = True

        cv2.startWindowThread()
        cv2.namedWindow("Image")
        cv2.createTrackbar('Mode', "Image", 0, 2, self.mode_change)
        cv2.createTrackbar('FFT X', "Image", self.fft_x, self.w, self.slide_fft_x)
        cv2.createTrackbar('FFT Y', "Image", self.fft_y, self.h, self.slide_fft_y)
        self.set_fft_carrier()

        self.im = numpy.zeros((self.h, self.w))

        self.time_last_draw = time.time()

        self.poll_once()

    def poll_once(self):
        if self.im_pipe.poll(.1):
            im = self.im_pipe.recv()
            print(os.getpid(), "got image:", im.shape)
            sys.stdout.flush()
            self.update_im(im)
        else:
            #print(os.getpid(), "poll empty")
            time.sleep(.01)
        t = threading.Timer(.1, self.poll_once)
        t.start()

    def update_im(self, new_im):
        if new_im.shape != (self.h, self.w):
            warnings.warn(os.getpid(), "got image of shape {}, expected {}".format(new_im.shape, (self.h, self.w)))
        self.im = new_im

        if new_im.dtype == numpy.uint16:
            self.im *= 2**6  # rescale to uppermost of 16 bits, otherwise display is very dark.

        now = time.time()
        if now - self.time_last_draw > .2:
            self.time_last_draw = now

            self._ith.set_image(self.im)
            im_result = self._ith.process_image(self.processing_step)
            if self.processing_step == ProcessingStep.STEP_FFT:
                im_result /= numpy.max(im_result)
            if self.processing_step == ProcessingStep.STEP_VIS_PHASES_RAW:
                im_result += numpy.pi
                im_result /= 2*numpy.pi

            label = "{}".format(self.num_ims)
            im_to_show = im_result
            #cv2.putText(im_to_show, label, (100, 100), cv2.FONT_HERSHEY_PLAIN, 2, 2**16)
            cv2.imshow("Image", im_to_show)
            self.num_ims += 1
            print(os.getpid(), "drew image.")
            sys.stdout.flush()

    def mode_change(self, mode):
        mode_dict = {0: ProcessingStep.STEP_CAM_IMAGE,
                     1: ProcessingStep.STEP_FFT,
                     2: ProcessingStep.STEP_VIS_PHASES_RAW}
        self.processing_step = mode_dict[mode]
        print("mode", mode)
        sys.stdout.flush()

    def slide_fft_x(self, x):
        self.fft_x = x
        self.set_fft_carrier()

    def slide_fft_y(self, y):
        self.fft_y = y
        self.set_fft_carrier()

    def set_fft_carrier(self):
        """apply member settings to ITH"""
        self._ith.set_fft_carrier((self.fft_y/self.h, self.fft_x/self.w))
        self.save_settings()

    def save_settings(self):
        config = configparser.ConfigParser()
        config.set('DEFAULT', KEY_FFT_X, str(self.fft_x))
        config.set('DEFAULT', KEY_FFT_Y, str(self.fft_y))
        with open(self.ini_path, 'w') as ini_handle:
            config.write(ini_handle)

    def load_settings(self):
        if not (os.path.exists(self.ini_path)):
            print("no ini file found")
            return
        config = configparser.ConfigParser()
        config.read(self.ini_path)
        self.fft_x = config.getint('DEFAULT', KEY_FFT_X, fallback=int(self.h*.8))
        self.fft_y = config.getint('DEFAULT', KEY_FFT_Y, fallback=int(self.h*.5))


class HolmosMain:
    def __init__(self):
        pipe_end_0, pipe_end_1 = multiprocessing.Pipe()

        self.ui = HolmosPlot(pipe_end_0)  # plot lives in this (main) process

        self.cam_process = multiprocessing.Process(target=loopcam, args=(pipe_end_1,), daemon=True)  # ...but cam in own proc.
        self.cam_process.start()
        print(self.cam_process.pid)


def loopcam(pipe):
    camera = picamera.PiCamera()
    camera.resolution = (w_full, h_full)
    output_bayer = picamera.array.PiBayerArray(camera)
    output_fast = YuvBufToNumpy()
    capture_bayer = False
    while True:
        tic = time.time()
        print(os.getpid(), "getting image from loopcam")
        sys.stdout.flush()
        output_bayer.truncate(0)

        if capture_bayer:
            camera.capture(output_bayer, 'jpeg', bayer=capture_bayer)
            im = output_bayer.array[1::2, 1::2, 0]  # red, one out of each 2x2
            print(os.getpid(), "Acquire Bayer: {:.1f}".format(time.time() - tic))
        else:
            camera.capture(output_fast, 'yuv')
            im = output_fast.data[::2, ::2]
            print(os.getpid(), "Acquire yuv: {:.1f}".format(time.time() - tic))

        pipe.send(im)
        sys.stdout.flush()


class YuvBufToNumpy(object):
    data = None
    u = None
    v = None

    def write(self, buf):
        w_pad = int(numpy.ceil(w_full/32)*32)  # picamera writes in 32x16 blocks
        h_pad = int(numpy.ceil(h_full/16)*16)
        # YUV420: [w x h: luminance, Y]--[w/2 x h/2 U]--[w/2 x h/2 V]
        self.data = numpy.frombuffer(buf, dtype=numpy.uint8,
                                     count=w_pad*h_pad).reshape((h_pad, w_pad))[:h_full, :w_full]
        ''' # Do not need u,v - but I'll leave this here in case someone needs color later.
        self.u = numpy.frombuffer(buf, dtype=numpy.uint8, offset=w_pad*h_pad,
                                  count=w_pad*h_pad//4).reshape((h_pad//2, w_pad//2))[:h_full//2, :w_full//2]
        self.v = numpy.frombuffer(buf, dtype=numpy.uint8, offset=w_pad*h_pad*5//4,
                                  count=w_pad*h_pad//4).reshape((h_pad//2, w_pad//2))[:h_full//2, :w_full//2]
        '''

    def flush(self):
        pass


if __name__ == '__main__':
    HolmosMain()
