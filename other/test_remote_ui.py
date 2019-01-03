# -*- coding: utf-8 -*-
"""
Created on 03.01.2019

@author: beckmann

Can be run from a desktop pycharm to execute on a remote (ssh) raspberry Pi, by setting environment variable:
DISPLAY=:0  lets plots appear on pi
DISPLAY=localhost:10.0  lets plots appear on Pycharm desktop machine

if plot is on Pi:
* Pi keyboard is captured
* plot updates on Pi
* console output arrives in Pycharm.
"""
import time

import matplotlib
print(matplotlib.rcsetup.all_backends)
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
import numpy
import sys


class InteractivePlot:
    def __init__(self):
        self.fig, self.ax = plt.subplots()

        self.fig.canvas.mpl_connect('key_press_event', lambda event: self.press(event))

        self.ys = [0.]
        self.plot, = self.ax.plot(self.ys)

        self.time_last_draw = time.time()

    def press(self, event):
        self.ys.append(numpy.random.randn())

        print('press', event.key, len(self.ys))
        sys.stdout.flush()

        self.update_plot()

    def update_plot(self):
        self.plot.set_ydata(self.ys)
        self.plot.set_xdata(range(len(self.ys)))

        now = time.time()
        if now - self.time_last_draw > .2:
            self.time_last_draw = now
            self.ax.relim()
            self.ax.autoscale_view()
            self.fig.canvas.draw()
        else:
            print("not updating after", now - self.time_last_draw)
        #self.fig.canvas.flush_events()


if __name__ == '__main__':
    InteractivePlot()
    plt.show()
