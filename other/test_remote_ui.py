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

    def press(self, event):
        self.ys.append(numpy.random.randn())
        self.update_plot()

        print('press', event.key, self.ys)
        sys.stdout.flush()

    def update_plot(self):
        self.plot.set_ydata(self.ys)
        self.plot.set_xdata(range(len(self.ys)))

        self.ax.relim()
        self.ax.autoscale_view()

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


if __name__ == '__main__':
    InteractivePlot()
    plt.show()
