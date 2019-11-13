# MIT License
#
# Copyright (c) 2019 Morning Project Samurai (MPS)
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


__author__ = 'Junya Kaneko <junya@mpsamurai.org>'


import unittest
import numpy as np
from ..core.dataflow.data import eye
from ..core.dataflow.backends import caches
from ..neochi import settings


class TestEyeImage(unittest.TestCase):
    def setUp(self):
        self.images = [image for image in np.random.randint(0, 256, size=(10, 240, 320)).astype(np.uint8)]
        self.cache = caches.get_cache(settings.DATAFLOW['BACKEND']['CACHE']['MODULE'],
                                      **settings.DATAFLOW['BACKEND']['CACHE']['KWARGS'])

    def test_if_it_accepts_images(self):
        data0 = eye.Image(self.cache)
        data1 = eye.Image(self.cache)
        for image in self.images:
            data0.value = image
            self.assertTrue(np.all(data0.value == image))
            self.assertTrue(np.all(data0.value == data1.value))


class TestEyeState(unittest.TestCase):
    def setUp(self):
        self.cache = caches.get_cache(settings.DATAFLOW['BACKEND']['CACHE']['MODULE'],
                                      **settings.DATAFLOW['BACKEND']['CACHE']['KWARGS'])

    def test_if_it_accepts_valid_json(self):
        data0 = eye.State(self.cache)
        data1 = eye.State(self.cache)
        data0.value = {'is_capturing': False}
        for key, value in data0.value.items():
            self.assertEqual(value, data1.value[key])

    def test_if_it_does_not_accept_invalid_json(self):
        data = eye.State(self.cache)
        with self.assertRaises(ValueError):
            data.value = {'is_capturing': 100}
