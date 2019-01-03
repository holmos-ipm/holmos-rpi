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

import numpy

try:
    import picamera
    import picamera.array
except ImportError:
    print("Could not import picamera. Are we running on a Raspberry Pi?")
    exit()


class HolmosPlot:
    """interactive matplotlib.figure"""
    w, h = 3280//2, 2464//2  # /2 because resulting images are R-channel only.
    num_ims = 0

    def __init__(self, im_pipe):
        self.im_pipe = im_pipe

        cv2.startWindowThread()
        cv2.namedWindow("Image")

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
            print(os.getpid(), "poll empty")
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

            cv2.imshow("Image", self.im[::2, ::2])
            self.num_ims += 1
            print(os.getpid(), "drew image.")
            sys.stdout.flush()

    def press(self, event):
        print(os.getpid(), 'press', event.key)
        sys.stdout.flush()


class HolmosMain:
    def __init__(self):
        pipe_end_0, pipe_end_1 = multiprocessing.Pipe()

        self.ui = HolmosPlot(pipe_end_0)  # plot lives in this (main) process

        self.cam_process = multiprocessing.Process(target=loopcam, args=(pipe_end_1,), daemon=True)  # ...but cam in own proc.
        self.cam_process.start()
        print(self.cam_process.pid)


w_full, h_full = 3280, 2464


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
