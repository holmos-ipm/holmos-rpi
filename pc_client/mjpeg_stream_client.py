# -*- coding: utf-8 -*-
"""
Created on 27.04.2018

@author: beckmann

script to read from mjpg stream.

this does not start the stream, you will need to run somethine like this on the server:
mjpg_streamer -i "input_raspicam.so -x 1024 -y 555"

you may check http://server:8080/?action=stream in a browser to see whether the server is up.
"""

import urllib.request
import io

import numpy
from PIL import Image


def get_array_from_mjpeg_stream(open_stream):
    byte_array = b''
    image_complete = False
    while not image_complete:
        byte_array += open_stream.read(1024)
        if len(byte_array) < 1000:
            print("mjpeg streamer sent very little data:")
            print(byte_array)
            return None
        a = byte_array.find(b'\xff\xd8')
        b = byte_array.find(b'\xff\xd9')
        image_complete = a != -1 and b != -1

    jpg = byte_array[a:b + 2]
    byte_stream = io.BytesIO(jpg)
    im = numpy.array(Image.open(byte_stream))[:, :, 0]

    return im

if __name__ == '__main__':
    remote_server = "10.82.202.30"
    proxies = {}
    opener = urllib.request.URLopener(proxies)
    stream = opener.open('http://'+remote_server+':8080/?action=stream')

    image = get_array_from_mjpeg_stream(stream)

    stream.close()

    if image is not None:
        print("image shape:", image.shape)
        print("image dtype:", image.dtype)
        print(image)
