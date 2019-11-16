# MIT License
#
# Copyright (c) 2019 Morning Project Samurai Inc. (MPS)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__author__ = 'Junya Kaneko <junya@mpsamurai.org>, Yutaro Kida'


import time
import cv2
import numpy as np

try:
    PI_CAMERA = True
    from picamera.array import PiRGBArray
    from picamera import PiCamera
except ImportError:
    PI_CAMERA = False

from neochi.core.dataflow import data


class Capture:
    def __init__(self, size, rotation):
        self._size = size
        self._rotation = rotation
        self._frame = None

    def capture(self):
        ret, frame = self._capture()
        return ret, frame

    def _capture(self):
        raise NotImplementedError


class CvCapture(Capture):
    def __init__(self, size, rotation):
        super().__init__(size, rotation)
        self._cap = cv2.VideoCapture(0)
        self._rotation = rotation

    def _capture(self):
        ret, frame = self._cap.read()
        if ret and frame is not None:
            # TODO: rotation should be taken into account.
            self._frame = cv2.cvtColor(cv2.resize(frame, tuple(self._size)), cv2.COLOR_BGR2RGB)
        return ret, self._frame

    def release(self):
        self._cap.release()


class PiCapture(Capture):
    def __init__(self, size, rotation):
        super().__init__(size, rotation)
        self._camera = PiCamera(resolution=size)
        self._camera.rotation = self._rotation
        self._cap = PiRGBArray(self._camera)

    def _capture(self):
        self._camera.capture(self._cap, format='rgb', use_video_port=True)
        frame = self._cap.array
        if frame.shape is None:
            return False, frame
        self._cap.truncate(0)
        self._frame = frame
        return True, self._frame

    def release(self):
        self._camera.close()


def get_capture(size, rotation_pc=0, rotation_pi=90):
    """
    :param image_size:
    :param fps[float]:
    :return image: captured image. array(image_size,3)
    """
    print('START CAPTURE.')
    if not PI_CAMERA:
        print("PC_CAMERA:")
        return CvCapture(size, rotation_pc)
    else:
        print("PI_CAMERA")
        return PiCapture(size, rotation_pi)


class Eye:
    def __init__(self, cache, size=[32, 32], rotation_pc=0., rotation_pi=90., fps=0.5, init=True):
        self._cache = cache
        self._image = data.eye.Image(cache)
        self._state = data.eye.State(cache)
        if init:
            self._state.value = {'size': size,
                                 'rotation_pc': rotation_pc,
                                 'rotation_pi': rotation_pi,
                                 'fps': fps,
                                 'is_capturing': False}

    @property
    def image(self):
        return self._image.value

    @property
    def state(self):
        return self._state.value

    def update_state(self, size=None, rotation_pc=None, rotation_pi=None, fps=None, is_capturing=None):
        value = {}
        if size:
            value['size'] = size
        if rotation_pc:
            value['rotation_pc'] = rotation_pc
        if rotation_pi:
            value['rotation_pi'] = rotation_pi
        if fps:
            value['fps'] = fps
        if is_capturing:
            value['is_capturing'] = is_capturing
        self._state.value = value

    def start_capture(self):
        cap = None
        fps = 0.5
        current_state = self._state.value
        while True:
            start_time = time.time()
            prev_state = current_state
            current_state = self._state.value
            if current_state['is_capturing'] and \
                    (cap is None or not np.all([prev_state[key] == value for key, value in current_state.items()])):
                try:
                    cap = get_capture(current_state['size'], current_state['rotation_pc'], current_state['rotation_pi'])
                    fps = current_state['fps']
                except KeyError:
                    print('EYE STATE ERROR:', current_state)
            elif not current_state['is_capturing']:
                if cap is not None:
                    cap.release()
                    cap = None
                time.sleep(0.1)
                continue
            captured, image = cap.capture()
            if not captured:
                continue
            self._image.value = image
            sleep_duration = 1. / fps - (time.time() - start_time)
            if sleep_duration > 0:
                time.sleep(sleep_duration)
