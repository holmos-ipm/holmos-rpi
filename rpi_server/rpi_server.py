# -*- coding: utf-8 -*-
import subprocess
import time
import numpy as np
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

try:
    import picamera
    import picamera.array
except ImportError:
    print("Kamera konnte nicht initalisiert werden. Beende Programm!.")
    exit()


# --------------------Variables--------------------------
w_full, h_full = 3280, 2464  # full resolution - needed for raw (PiBayerArray) mode 3280, 2464
shutter_speed = 60
use_stream = True
proc = None


class CameraArbiter:
    def __init__(self):
        self.streamActive = False
        self.pythonActive = False
        self.proc = None
        self.camera = None

    def activate_stream(self):
        if self.pythonActive:
            self.pythonActive = False
            self.camera.close()
            self.camera = None
        if self.proc is not None:
            self.proc.terminate()
        self.streamActive = True
        self.proc = subprocess.Popen(['mjpg_streamer',
                                     '-o',
                                     'output_http.so',
                                     '-i',
                                     'input_raspicam.so -x 1024 -y 1024 -fps 15'])
        time.sleep(1.5)  # TODO: find better fix for the stream warm up problem

    def deactivate_stream(self):
        if self.streamActive:
            self.proc.terminate()
            self.streamActive = False

    def claim_cam(self):
        if self.streamActive:
            self.proc.terminate()
            self.streamActive = False
        if self.camera is None:
            print("create PiCam")
            self.pythonActive = True
            self.camera = picamera.PiCamera()
            print("Created, waiting.")
            time.sleep(1)
        return self.camera


def activate_stream(mjpeg):
    if use_stream and mjpeg:
        arbiter.activate_stream()
        return True
    else:
        print("Ask for the images on your own!")
        return False


def deactivate_stream():
    print("Stream deactivated")
    arbiter.deactivate_stream()
    return True


def take_single_bayer(w_out, h_out):
    print("got bayer request")
    # arbiter.claim_cam().shutter_speed = shutter_speed  # Auto-Belichtung geht ganz gut.
    arbiter.claim_cam().resolution = (w_full, h_full)
    output = picamera.array.PiBayerArray(arbiter.claim_cam())
    output.truncate(0)
    arbiter.claim_cam().capture(output, 'jpeg', bayer=True)

    im = output.array[1::2, 1::2, 0]  # red, one out of each 2x2

    h_0 = (h_full/2 - h_out) / 2
    w_0 = (w_full/2 - w_out) / 2

    im = im[h_0:h_0 + h_out, w_0:w_0 + w_out]
    print("output: {}x{}, [{}...{}], type {}".format(im.shape[0], im.shape[1], np.min(im), np.max(im), im.dtype))

    return im.astype(np.uint16).tostring()


def take_single_jpeg():
    # Camera in Global and close when bayer is needed
    image = np.empty((1024, 1024, 3), dtype=np.uint8)
    arbiter.claim_cam().shutter_speed = shutter_speed
    arbiter.claim_cam().resolution = (1024, 1024)
    arbiter.claim_cam().capture(image, 'rgb')
    im = image[:, :, 0]
    im = np.divide(im, 2)
    return im.astype(dtype=np.uint8).tostring()


def take_random_16bit(highest, shape):
    array = np.random.randint(highest, size=shape)
    return array.astype(np.uint16).tostring()


def is_online():
    return True


# Create server
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

server = SimpleXMLRPCServer(("", 5117), requestHandler=RequestHandler)
server.register_function(take_single_bayer, 'take_single_bayer')
server.register_function(take_single_jpeg, 'take_single_jpeg')
server.register_function(take_random_16bit, 'take_random_16bit')
server.register_function(activate_stream, 'activate_stream')
server.register_function(deactivate_stream, 'deactivate_stream')
server.register_function(is_online, 'is_online')
# Um die Ip des Servers herauszufinden, folgenden Befehl im Linux terminal ausführen:
# ifconfig eth0 | grep 'inet Adresse'
print("Server up!")

arbiter = CameraArbiter()

server.serve_forever()
