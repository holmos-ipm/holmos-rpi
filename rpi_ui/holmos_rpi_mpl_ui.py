# -*- coding: utf-8 -*-
"""
Created on 03.01.2019

@author: beckmann

holmos client for direct execution on rpi
developed for Raspberry Pi 3B
"""
import os
import sys
import threading
import time
import multiprocessing
import warnings

import cv2

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


class HolmosPlot:
    """interactive matplotlib.figure"""
    w, h = w_full//2, h_full//2  # /2 because resulting images are R-channel only.
    fft_x = int(w*.8)
    fft_y = int(h*.5)
    num_ims = 0
    processing_step = ProcessingStep.STEP_CAM_IMAGE

    def __init__(self, im_pipe):
        self.im_pipe = im_pipe

        self._ith = ImgToHolo(633e-9, 2e-6)

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
        self.im = new_im*2**6

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
            im_to_show = numpy.copy(im_result[::2, ::2])
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
        self._ith.set_fft_carrier((self.fft_y/self.h, self.fft_x/self.w))




class HolmosMain:
    def __init__(self):
        pipe_end_0, pipe_end_1 = multiprocessing.Pipe()

        self.ui = HolmosPlot(pipe_end_0)  # plot lives in this (main) process

        self.cam_process = multiprocessing.Process(target=loopcam, args=(pipe_end_1,), daemon=True)  # ...but cam in own proc.
        self.cam_process.start()
        print(self.cam_process.pid)


def loopcam(pipe):
    camera = picamera.PiCamera()
    output = picamera.array.PiBayerArray(camera)
    while True:
        print(os.getpid(), "getting bayer image from loopcam")
        sys.stdout.flush()
        output.truncate(0)
        camera.capture(output, 'jpeg', bayer=True)

        im = output.array[1::2, 1::2, 0]  # red, one out of each 2x2

        pipe.send(im)
        print(os.getpid(), "put image.")
        sys.stdout.flush()


if __name__ == '__main__':
    HolmosMain()
