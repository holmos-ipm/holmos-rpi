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

import cv2
import numpy
import tkinter as tk

from pc_client.holo_globals import ProcessingStep
from pc_client.img_to_holo import ImgToHolo


try:
    import picamera
    import picamera.array
except ImportError:
    print("Could not import picamera. Are we running on a Raspberry Pi?")
    exit()

print("cv2 version", cv2.__version__)

w_full, h_full = 3280, 2464

KEY_FFT_X = "fft_x"  # TODO: use same as holo-software?
KEY_FFT_Y = "fft_y"


class HolmosRequest:
    time_cam_start = None
    time_cam_finish = None
    time_calc_finish = None
    cam_bayer = None
    processing_step = None
    data = None

    def __str__(self):
        acq_s = self.time_cam_finish - self.time_cam_start
        calc_s = self.time_calc_finish - self.time_cam_finish
        desc = "<HolmosReuquest - Acq {:.1f}s, Calc {:.1f}s, Total {:.1f}s>".format(acq_s, calc_s, acq_s+calc_s)
        return desc


class HolmosPlot:
    """interactive matplotlib.figure"""
    w, h = w_full//2, h_full//2  # /2 because resulting images are R-channel only.
    fft_x = int(w*.8)
    fft_y = int(h*.5)
    num_ims = 0
    processing_step = ProcessingStep.STEP_CAM_IMAGE
    ini_path = "holmos_settings.ini"

    def __init__(self, im_pipe):
        self.im_queue = im_pipe

        self.load_settings()

        self._ith = ImgToHolo(633e-9, 2e-6)
        self._ith.set_fft_carrier(None, r=120/self.w)
        #self._ith.logger = lambda s: print(s)
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
        if not self.im_queue.empty():
            request = self.im_queue.get()
            print(os.getpid(), "got image:", request.data.shape)
            sys.stdout.flush()
            request.processing_step = self.processing_step  # once cam image is returned, set the processing step
            self.update_im(request)
        else:
            #print(os.getpid(), "poll empty")
            time.sleep(.01)
        t = threading.Timer(.1, self.poll_once)
        t.start()

    def update_im(self, request):
        assert isinstance(request, HolmosRequest)
        if request.data.shape != (self.h, self.w):
            warnings.warn(os.getpid(), "got image of shape {}, expected {}".format(request.data.shape, (self.h, self.w)))
        self.im = request.data

        if request.data.dtype == numpy.uint16:
            self.im *= 2**6  # rescale to uppermost of 16 bits, otherwise display is very dark.

        now = time.time()
        if now - self.time_last_draw > .2:
            self._ith.set_image(request.data)
            im_result = self._ith.process_image(request.processing_step)
            if request.processing_step == ProcessingStep.STEP_FFT:
                im_result /= numpy.max(im_result)
            if request.processing_step == ProcessingStep.STEP_VIS_PHASES_RAW:
                im_result += numpy.pi
                im_result /= 2*numpy.pi
            request.time_calc_finish = time.time()

            label = "{}".format(self.num_ims)
            im_to_show = im_result
            #cv2.putText(im_to_show, label, (100, 100), cv2.FONT_HERSHEY_PLAIN, 2, 2**16)
            cv2.imshow("Image", im_to_show)
            self.num_ims += 1
            now = time.time()
            print(os.getpid(), "drew image. Total time since last image: {:.1f}s".format(now - self.time_last_draw))
            print(request)
            self.time_last_draw = now
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

        queue = multiprocessing.Queue()

        self.plot = HolmosPlot(queue)  # plot lives in this (main) process
        self.cam = LoopCam()

        self.cam_process = multiprocessing.Process(target=self.cam, args=(queue,), daemon=True)  # ...but cam in own proc.
        self.cam_process.start()

        self.ui = HolmosControls(self.plot, self.cam)


class LoopCam(object):
    capture_bayer = False

    def __init__(self):
        print(os.getpid(), "LoopCam Init")

    def __call__(self, queue):
        camera = picamera.PiCamera()
        camera.resolution = (w_full, h_full)
        output_bayer = picamera.array.PiBayerArray(camera)
        output_fast = YuvBufToNumpy()
        print(os.getpid(), "LoopCam __call__")

        while True:
            request = HolmosRequest()
            request.time_cam_start = time.time()

            output_bayer.truncate(0)

            request.cam_bayer = self.capture_bayer
            if self.capture_bayer:
                camera.capture(output_bayer, 'jpeg', bayer=True)
                request.data = output_bayer.array[1::2, 1::2, 0]  # red, one out of each 2x2
            else:
                camera.capture(output_fast, 'yuv')
                request.data = output_fast.data[::2, ::2]
            request.time_cam_finish = time.time()

            tic = time.time()
            while not queue.empty():
                time.sleep(.1)
            print(os.getpid(), "Waited {:.1f} s for Queue to become ready".format(time.time() - tic))
            queue.put(request)

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


class HolmosControls:
    _plot = None
    _cam = None

    def __init__(self, plot: HolmosPlot, cam: LoopCam):
        self._cam = cam
        self._plot = plot

        self.tk_root = tk.Tk()

        fft_sliders = tk.Frame(self.tk_root)
        fft_slider_x = tk.Scale(fft_sliders, from_=0, to=plot.w, orient=tk.HORIZONTAL, command=self.scale)
        fft_slider_x.pack()

        fft_sliders.pack()

        tk.mainloop()

    def scale(self, n):
        print("SCALE COMMAND", type(n))
        self._plot.slide_fft_x(int(n))




if __name__ == '__main__':
    HolmosMain()
