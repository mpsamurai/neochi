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
from ..core.dataflow.backends import caches
from ..core.dataflow import serializers
from ..core.dataflow import data
from ..neochi import settings


class SampleSerializer(serializers.Serializer):
    _schema = data.Schema.create(body={
        'type': 'object',
        'properties': {
            'key': {'type': 'string'},
            'value': {'type': 'string', 'default': 'None'},
            'description': {'type': 'string'},
        },
        'required': ['key', 'value']
    })


class SampleData(data.Data):
    _serializer = SampleSerializer()
    _key = 'sample_data'

    def _get_value(self):
        return self._data['body']

    def _set_value(self, value):
        self._data['body'] = value


class TestData(unittest.TestCase):
    def setUp(self):
        self._cache = caches.get_cache(settings.DATAFLOW['BACKEND']['CACHE']['MODULE'],
                                       **settings.DATAFLOW['BACKEND']['CACHE']['KWARGS'])

    def test_if_it_sets_and_gets_value(self):
        d0 = SampleData(self._cache)
        d0.value = {
            'key': 'Hello',
            'value': 'Junya!',
            'description': 'Hello Junya!'
        }
        d1 = SampleData(self._cache)
        self.assertEqual(d1.value['key'], 'Hello')
        self.assertEqual(d1.value['value'], 'Junya!')
        self.assertEqual(d1.value['description'], 'Hello Junya!')

    def test_if_it_raises_validation_error_when_required_field_is_missing(self):
        d0 = SampleData(self._cache)
        with self.assertRaises(serializers.exceptions.ValidationError):
            d0.value = {
                'value': 'Junya!',
                'description': 'Hello Junya!'
            }

    def test_if_it_fills_default_values(self):
        d0 = SampleData(self._cache)
        d0.value = {
            'key': 'Hello',
            'description': 'Hello Junya!'
        }
        self.assertEqual(d0.value['value'], 'None')


class TestImage(unittest.TestCase):
    def setUp(self):
        self._cache = caches.get_cache(settings.DATAFLOW['BACKEND']['CACHE']['MODULE'],
                                       **settings.DATAFLOW['BACKEND']['CACHE']['KWARGS'])
        self._gray_image = np.random.randint(0, 256, size=(32, 32), dtype=np.uint8)
        self._color_image = np.random.randint(0, 256, size=(32, 32, 3), dtype=np.uint8)
        self._invalid_image = np.random.randint(0, 256, size=(32, 32, 2), dtype=np.uint8)

    def test_if_it_sets_and_gets_value(self):
        d0 = data.Image(self._cache)
        d0.value = self._gray_image
        d1 = data.Image(self._cache)
        self.assertTrue(isinstance(d1.value, np.ndarray))
        self.assertTrue(np.any(d0.value == d1.value))

        d0.value = self._color_image
        self.assertTrue(isinstance(d1.value, np.ndarray))
        self.assertTrue(np.any(d0.value == d1.value))

    def test_if_it_does_not_accept_invalid_value(self):
        d0 = data.Image(self._cache)
        with self.assertRaises(ValueError):
            d0.value = self._invalid_image
