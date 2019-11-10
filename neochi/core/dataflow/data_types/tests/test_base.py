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


__author__ = 'Junya Kaneko<junya@mpsamurai.org>'


import random
import unittest
import numpy as np
from .. import base


class TestJson(unittest.TestCase):
    def setUp(self):
        self._test_dict = {'int': 10, 'float': 0.1, 'str': 'str'}
        self._test_list = [0, 1, 2., 'str']

    def test_if_it_accepts_dict(self):
        data = base.Json()
        data.value = self._test_dict
        self.assertEqual(len(self._test_dict), len(data.value))
        for key, value in self._test_dict.items():
            self.assertEqual(data.value[key], value)

    def test_if_it_accepts_list(self):
        data = base.Json()
        data.value = self._test_list
        self.assertEqual(len(self._test_list), len(data.value))
        for i, value in enumerate(self._test_list):
            self.assertEqual(data.value[i], value)

    def test_if_timestamp_is_updated_when_value_is_updated(self):
        data = base.Json()
        timestamp = data.header.timestamp
        data.value = {'abc': 123}
        self.assertGreater(data.header.timestamp, timestamp)

    def test_if_timestamp_is_set_at_instantiation(self):
        data0 = base.Json()
        data1 = base.Json()
        self.assertGreater(data1.header.timestamp, data0.header.timestamp)

    def test_if_it_is_json_serializable(self):
        data = base.Json()
        data.to_json()


class TestNull(unittest.TestCase):
    def test_if_it_returns_none(self):
        data = base.Null()
        self.assertEqual(data.value, None)

    def test_if_it_is_readonly(self):
        data = base.Null()
        with self.assertRaises(AttributeError):
            data.value = 'abc'


class TestInt(unittest.TestCase):
    def test_if_it_default_value_is_zero(self):
        data = base.Int()
        self.assertEqual(data.value, 0)

    def test_if_it_accepts_int_values(self):
        data = base.Int()
        for _ in range(1000):
            i = random.randint(-100000000, 1000000000)
            data.value = i
            self.assertEqual(data.value, i)

    def test_if_it_denys_float_values(self):
        data = base.Int()
        for _ in range(1000):
            i = random.random()
            with self.assertRaises(ValueError):
                data.value = i

    def test_if_it_denys_str_values(self):
        data = base.Int()
        with self.assertRaises(ValueError):
            data.value = 'abc'


class TestFloat(unittest.TestCase):
    def test_if_it_default_value_is_zero(self):
        data = base.Float()
        self.assertEqual(data.value, 0.)

    def test_if_it_accepts_float_values(self):
        data = base.Float()
        for _ in range(1000):
            i = random.random()
            data.value = i
            self.assertEqual(data.value, i)

    def test_if_it_denys_int_values(self):
        data = base.Float()
        for _ in range(1000):
            i = random.randint(-100000000, 1000000000)
            with self.assertRaises(ValueError):
                data.value = i

    def test_if_it_denys_str_values(self):
        data = base.Float()
        with self.assertRaises(ValueError):
            data.value = 'abc'


class TestStr(unittest.TestCase):
    def test_if_it_default_value_is_blank(self):
        data = base.Str()
        self.assertEqual(data.value, '')

    def test_if_it_accepts_str_values(self):
        data = base.Str()
        for s in ['abc', 'def', 'ghi']:
            data.value = s
            self.assertEqual(data.value, s)

    def test_if_it_denys_int_values(self):
        data = base.Str()
        with self.assertRaises(ValueError):
            data.value = 0

    def test_if_it_denys_float_values(self):
        data = base.Str()
        with self.assertRaises(ValueError):
            data.value = 0.


class TestImage(unittest.TestCase):
    def setUp(self):
        self.image = np.random.randint(0, 256, (240, 320)).astype(np.uint8)

    def test_if_it_default_value_is_none(self):
        data = base.Image()
        self.assertEqual(data.value, None)

    def test_if_it_accepts_image(self):
        data = base.Image()
        data.value = self.image
        self.assertEqual(data.value.shape[0], self.image.shape[0])
        self.assertEqual(data.value.shape[1], self.image.shape[1])

    def test_if_it_accepts_h_w_list(self):
        data = base.Image()
        data.value = [[1, 2, 3], [4, 5, 6]]
        self.assertEqual(data.value.shape[0], 2)
        self.assertEqual(data.value.shape[1], 3)
        with self.assertRaises(IndexError):
            self.assertEqual(data.value.shape[2], 1)

    def test_if_it_accepts_h_w_c_list(self):
        data = base.Image()
        data.value = [
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
            [[9, 8, 7], [6, 5, 4], [3, 2, 1]],
        ]
        self.assertEqual(data.value.shape[0], 2)
        self.assertEqual(data.value.shape[1], 3)
        self.assertEqual(data.value.shape[2], 3)

    def test_if_it_denys_image_having_channel_size_larger_than_3(self):
        data = base.Image()
        with self.assertRaises(ValueError):
            data.value = np.zeros((32, 32, 32, 32))

    def test_if_it_denys_image_having_channel_size_less_than_2(self):
        data = base.Image()
        with self.assertRaises(ValueError):
            data.value = np.zeros((32, 32, 2)).astype(np.uint8)

    def test_if_it_denys_int(self):
        data = base.Image()
        with self.assertRaises(ValueError):
            data.value = 0

    def test_if_it_denys_float(self):
        data = base.Image()
        with self.assertRaises(ValueError):
            data.value = 0.

    def test_if_it_denys_str(self):
        data = base.Image()
        with self.assertRaises(ValueError):
            data.value = ''
