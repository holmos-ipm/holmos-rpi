# -*- coding: utf-8 -*-
"""
Created on 03.01.2019

@author: beckmann

holmos client for direct execution on rpi
developed for Raspberry Pi 3B
"""
import argparse
import configparser
import os
import sys
import threading
import time
import multiprocessing
import warnings

import PIL.ImageTk  # if this fails: try "sudo apt-get install python3-pil.imagetk"
import numpy
import tkinter as tk
import tkinter.filedialog

from algorithm.holo_globals import ProcessingStep
from algorithm.img_to_holo import ImgToHolo


try:
    import picamera
    import picamera.array
except ImportError:
    print("Could not import picamera. Are we running on a Raspberry Pi?")
    exit()

w_full, h_full = 3280, 2464

KEY_FFT_X = "fft_x"  # TODO: use same as holo-software?
KEY_FFT_Y = "fft_y"


labels_modes = (("Camera image", ProcessingStep.STEP_CAM_IMAGE),
                ("FFT", ProcessingStep.STEP_FFT),
                ("Phase image", ProcessingStep.STEP_VIS_PHASES_RAW))

arg_parser = argparse.ArgumentParser(description="Holmos UI for Raspberry Pi")
arg_parser.add_argument('--size-reduction', dest="size_reduction", default=2, type=int)
arg_parser.add_argument('--transpose', dest="transpose", default=False, action="store_true")
args = arg_parser.parse_args()
print(args)


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
    w, h = w_full//args.size_reduction//2, h_full//args.size_reduction//2  # /2 because resulting images are R-channel only.
    fft_x = int(w*.8)
    fft_y = int(h*.5)
    num_ims = 0
    processing_step = ProcessingStep.STEP_CAM_IMAGE
    ini_path = "holmos_settings.ini"
    tk_photo = None  # Need to keep reference, otherwise image is deleted and disappears from screen
    tk_circle = None
    tk_rect = None
    pil_im = None

    drawing_rect = False

    def __init__(self, im_pipe):
        self.im_queue = im_pipe

        self.load_settings()
        fft_r_relative = .1

        #self._cam = cam
        self.tk_root = tk.Tk()  # If we are remote and this fails, try setting DISPLAY=:0
        self.tk_root.title("HolMOS")
        for key in "<Up>", "<Down>", "<Left>", "<Right>":
            self.tk_root.bind_all(key, self.arrow_key)

        Frame = tk.Frame(self.tk_root)

        frame_controls = tk.Frame(Frame)
        frame_mode = self.make_mode_selector_frame(frame_controls)
        frame_mode.pack(side=tk.LEFT, anchor="n", padx=5, pady=5)

        frame_fft = self.make_fft_slider_frame(frame_controls)
        frame_fft.pack(side=tk.LEFT)

        frame_save = self.make_save_frame(frame_controls)
        frame_save.pack(side=tk.LEFT)
        frame_controls.pack()

        if args.transpose:
            self.canvas = tk.Canvas(Frame, height=self.w, width=self.h)  # ONLY TRANSPOSE IN FINAL PRINT TO CANVAS!
        else:
            self.canvas = tk.Canvas(Frame, height=self.h, width=self.w)
        self.canvas.place(x=0, y=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.mouse_clicked)

        self.tk_image = self.canvas.create_image(0, 0, anchor=tk.NW)
        Frame.pack()

        self._ith = ImgToHolo(633e-9, 2e-6)
        self._ith.set_fft_carrier(None, r=fft_r_relative)
        self._ith.logger = lambda s: print(s)
        self._ith.size_reduction = args.size_reduction

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
        if request.data.shape != (h_full//2, w_full//2):
            # no matter our size reduction, this is always R-channel only, but full resolution -> h_full/2
            warnings.warn("got image of shape {}, expected {}".format(request.data.shape, (h_full//2, w_full//2)))
        self.im = request.data

        if request.data.dtype == numpy.uint16:
            self.im *= 2**6  # rescale to uppermost of 16 bits, otherwise display is very dark.

        now = time.time()
        if now - self.time_last_draw > .2:
            self._ith.set_image(request.data)
            im_result = self._ith.process_image(request.processing_step)
            if request.processing_step == ProcessingStep.STEP_FFT:
                im_result /= numpy.max(im_result)
                im_result *= 255
            if request.processing_step == ProcessingStep.STEP_VIS_PHASES_RAW:
                im_result += numpy.pi
                im_result /= 2*numpy.pi
                im_result *= 255
            request.time_calc_finish = time.time()

            if im_result.dtype == numpy.uint16:
                im_result = im_result/2**8

            if args.transpose:
                im_result = im_result.astype(numpy.uint8).transpose()
            else:
                im_result = im_result.astype(numpy.uint8)
            self.pil_im = PIL.Image.fromarray(im_result)
            self.tk_photo = PIL.ImageTk.PhotoImage(image=self.pil_im)
            self.canvas.itemconfig(self.tk_image, image=self.tk_photo)

            self.draw_fft_rect(request.processing_step, self._ith.fft_rect_center_yxrr_px())

            self.num_ims += 1
            now = time.time()
            print(os.getpid(), "drew image. Total time since last image: {:.1f}s".format(now - self.time_last_draw))
            print(request)
            self.time_last_draw = now
            sys.stdout.flush()

    def draw_fft_rect(self, step, yxrr_px):
        # not sure why, but a mutex leads to deadlock here. Instead, drop requests if drawing already
        if not self.drawing_rect:
            self.drawing_rect = True

            self.canvas.delete(self.tk_circle)  # delete works even if object is None
            self.canvas.delete(self.tk_rect)
            if step == ProcessingStep.STEP_FFT:
                y, x, ry, rx = yxrr_px
                if args.transpose:
                    y, x = x, y
                    ry, rx = rx, ry
                self.tk_circle = self.canvas.create_oval([x-2, y-2, x+2, y+2], fill="blue", outline="")
                self.tk_rect = self.canvas.create_rectangle([x-rx, y-ry, x+rx, y+ry], outline="blue", width=2)
            self.drawing_rect = False

    def mode_change(self, step):
        self.processing_step = step
        print("mode", self.processing_step)
        sys.stdout.flush()

    def slide_fft_x(self, x):
        self.fft_x = int(x)
        self.set_fft_carrier()

    def slide_fft_y(self, y):
        self.fft_y = int(y)
        self.set_fft_carrier()

    def mouse_clicked(self, event: tkinter.Event):
        if self.processing_step == ProcessingStep.STEP_FFT:
            self.fft_x = event.x
            self.fft_y = event.y
            self.apply_self_fft()

    def arrow_key(self, event: tkinter.Event):
        if event.keysym == "Up":
            self.fft_y -= 1
        if event.keysym == "Down":
            self.fft_y += 1
        if event.keysym == "Left":
            self.fft_x -= 1
        if event.keysym == "Right":
            self.fft_x += 1
        self.apply_self_fft()

    def apply_self_fft(self):
        """
        apply current values of self.fft_x/y to sliders and ith, redraw rectangle if appropriate
        """
        self.fft_slider_x.set(self.fft_x)
        self.fft_slider_y.set(self.fft_y)
        self.set_fft_carrier()
        self.draw_fft_rect(self.processing_step, self._ith.fft_rect_center_yxrr_px())

    def set_fft_carrier(self):
        """apply member settings to ITH"""
        self._ith.set_fft_carrier((self.fft_y/self.h, self.fft_x/self.w))
        self.save_settings()

    def save_image(self):
        if self.pil_im is not None:
            proposed_filename = time.strftime("holmos_%Y-%m-%d_%H.%M.%S.png")
            filename = tk.filedialog.asksaveasfilename(initialfile=proposed_filename, initialdir="~")
            if filename:
                self.pil_im.save(filename)
                print("saved to {}".format(filename))

    def save_settings(self):
        config = configparser.ConfigParser()
        config.set('DEFAULT', KEY_FFT_X, str(self.fft_x*self._ith.size_reduction))
        config.set('DEFAULT', KEY_FFT_Y, str(self.fft_y*self._ith.size_reduction))
        with open(self.ini_path, 'w') as ini_handle:
            config.write(ini_handle)

    def load_settings(self):
        if not (os.path.exists(self.ini_path)):
            print("no ini file found")
            self.fft_x = self.w//2
            self.fft_y = self.h//2
            return
        config = configparser.ConfigParser()
        config.read(self.ini_path)
        self.fft_x = config.getint('DEFAULT', KEY_FFT_X, fallback=int(self.h*.8)) // args.size_reduction
        self.fft_y = config.getint('DEFAULT', KEY_FFT_Y, fallback=int(self.h*.5)) // args.size_reduction

    def make_mode_selector_frame(self, parent):
        frame_mode = tk.LabelFrame(parent, text="Processing Mode")

        val_mode = tk.IntVar()  # needed to make group of Radiobuttons exclusive
        tk.Radiobutton(frame_mode, text="Camera image", variable=val_mode, value=0, takefocus=True,
                       command=lambda: self.mode_change(ProcessingStep.STEP_CAM_IMAGE)).pack(anchor="w")
        tk.Radiobutton(frame_mode, text="FFT", variable=val_mode, value=1, takefocus=True,
                       command=lambda: self.mode_change(ProcessingStep.STEP_FFT)).pack(anchor="w")
        tk.Radiobutton(frame_mode, text="Phase image", variable=val_mode, value=2, takefocus=True,
                       command=lambda: self.mode_change(ProcessingStep.STEP_VIS_PHASES_RAW)).pack(anchor="w")
        return frame_mode

    def make_fft_slider_frame(self, frame_controls):
        frame_fft = tk.Frame(frame_controls)
        self.fft_slider_x = tk.Scale(frame_fft, from_=0, to=self.w, orient=tk.HORIZONTAL, command=self.slide_fft_x,
                                label="fft_x", takefocus=True)
        self.fft_slider_x.set(self.fft_x)
        self.fft_slider_y = tk.Scale(frame_fft, from_=0, to=self.h, orient=tk.HORIZONTAL, command=self.slide_fft_y,
                                label="fft_y", takefocus=True)
        self.fft_slider_y.set(self.fft_y)
        self.fft_slider_x.pack()
        self.fft_slider_y.pack()
        return frame_fft

    def make_save_frame(self, frame_controls):
        frame_save = tk.Frame(frame_controls)
        tk.Button(frame_save, text="Save current image", command=self.save_image).pack()
        return frame_save


class HolmosMain:
    def __init__(self):

        queue = multiprocessing.Queue()

        self.plot = HolmosPlot(queue)  # plot lives in this (main) process
        self.cam = LoopCam()

        self.cam_process = multiprocessing.Process(target=self.cam, args=(queue,), daemon=True)  # ...but cam in own proc.
        self.cam_process.start()

        tk.mainloop()


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


if __name__ == '__main__':
    HolmosMain()
