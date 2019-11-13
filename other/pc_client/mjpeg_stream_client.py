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
    start_pos = -1
    num_bytes = -1
    while not image_complete:
        byte_array += open_stream.read(1024)
        if len(byte_array) < 1000:
            print("mjpeg streamer sent very little data:")
            print(byte_array)
            return None
        start_pos = byte_array.find(b'\xff\xd8')
        if start_pos != -1:
            num_bytes = byte_array[start_pos:].find(b'\xff\xd9')  # stop - search after a only
        image_complete = start_pos != -1 and num_bytes != -1

    print("found jpg in stream at", start_pos, "length", num_bytes)
    jpg = byte_array[start_pos: start_pos + num_bytes + 2]
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
