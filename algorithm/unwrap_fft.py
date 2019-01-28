# -*- coding: utf-8 -*-
"""
Created on Tue Jul 02 08:50:17 2013

@author: TBe

Phase unwrapping nach
M. A. Schofield, Optics Letters 28, 14, 1195 (2003)

"""

import numpy


def phi_prime(x):
    idt, dt = numpy.fft.ifft2, numpy.fft.fft2
    r2 = r_squared(x.shape)
    cos = numpy.cos(x)
    sin = numpy.sin(x)

    var = r2 ** -1.0 * dt(
        cos * idt(r2 * dt(sin))
        - sin * idt(r2 * dt(cos)))
    result = idt(var)
    return result


def r_squared(shape):
    dim_x = shape[0] // 2
    dim_y = shape[1] // 2
    x2 = numpy.arange(-dim_x, dim_x)  # ndarray mit x-Koordinate (0,0 liegt in Bildmitte)
    y2 = numpy.arange(-dim_y, dim_y)
    x2 = x2 ** 2  # ndarray mit x^2
    y2 = y2 ** 2
    x2 = numpy.roll(x2, dim_x)
    y2 = numpy.roll(y2, dim_y)
    r2s = numpy.add.outer(x2, y2)  # 2d ndarray mit r^2
    r2s = r2s.astype(numpy.float32)
    r2s += 1e-10  # bitte keine Null
    return r2s


def unwrap_fft(data):
    mirrored = numpy.zeros([x*2 for x in data.shape])
    mirrored[:data.shape[0], :data.shape[1]] = data
    mirrored[data.shape[0]:, :data.shape[1]] = data[::-1, :]
    mirrored[data.shape[0]:, data.shape[1]:] = data[::-1, ::-1]
    mirrored[:data.shape[0], data.shape[1]:] = data[:, ::-1]
    phi_ = phi_prime(mirrored).real[:data.shape[0], :data.shape[1]]

    return data + 2*numpy.pi*numpy.round((phi_ - data)/2/numpy.pi)
