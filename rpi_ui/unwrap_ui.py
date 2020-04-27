# -*- coding: utf-8 -*-
"""
Created on 28.01.2019

@author: beckmann
"""
import sys
import time

import PIL.ImageTk
import numpy
import tkinter as tk

from algorithm.unwrap_fft import unwrap_fft
from rpi_ui import w_full, h_full


class HolmosUnwrapUI:
    w, h = w_full//2, h_full//2  # /2 because resulting images are R-channel only.
    phase_img_2pi = None
    unwrapped_rad = None
    tk_photo = None  # Need to keep reference, otherwise image is deleted and disappears from screen

    def __init__(self, filename):

        self.tk_root = tk.Tk()
        self.tk_root.title("HolMOS Unwrapper")

        Frame = tk.Frame(self.tk_root)

        frame_controls = tk.Frame(Frame)
        tk.Button(frame_controls, text="Unwrap", command=self.do_unwrap).pack()
        tk.Button(frame_controls, text="Save unwrapped image", command=self.save_image).pack()
        frame_controls.pack()

        self.canvas_phase = tk.Canvas(Frame, height=self.h / 2, width=self.w / 2)
        self.canvas_phase.place(x=0, y=0)
        self.canvas_phase.pack()

        self.tk_image = self.canvas_phase.create_image(0, 0, anchor=tk.NW)
        Frame.pack()

        self.load_image(filename)

        tk.mainloop()

    def load_image(self, filename):
        self.phase_img_2pi = numpy.array(PIL.Image.open(filename)).astype(float)
        self.phase_img_2pi *= 2*numpy.pi/255  # TODO: assumes 8-bit-image.

        self.show_phase_image(self.phase_img_2pi)

    def show_phase_image(self, phase_img):
        pil_im = self.make_pil_uint(phase_img)
        self.tk_photo = PIL.ImageTk.PhotoImage(image=pil_im)
        self.canvas_phase.itemconfig(self.tk_image, image=self.tk_photo)

    def make_pil_uint(self, phase_img):
        min_val = numpy.min(phase_img)
        max_val = numpy.max(phase_img)
        uint_array = ((phase_img - min_val) / (max_val - min_val) * 255).astype(numpy.uint8)
        return PIL.Image.fromarray(uint_array)

    def do_unwrap(self):
        self.unwrapped_rad = unwrap_fft(self.phase_img_2pi)

        self.show_phase_image(self.unwrapped_rad)

    def save_image(self):
        if self.unwrapped_rad is not None:
            proposed_filename = time.strftime("holmos_unwrapped_%Y-%m-%d_%H.%M.%S.png")
            filename = tk.filedialog.asksaveasfilename(initialfile=proposed_filename, initialdir="~")
            if filename:
                pil_im = self.make_pil_uint(self.unwrapped_rad)
                pil_im.save(filename)
                print("saved to {}".format(filename))


if __name__ == '__main__':
    fn = sys.argv[1]
    HolmosUnwrapUI(fn)