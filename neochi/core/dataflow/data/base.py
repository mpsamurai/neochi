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


__author__ = 'Junya Kaneko <junya@mpsamurai.org>'


import time
import copy
import abc
import numpy as np
import base64
from .. import serializers


class Schema:
    _schema = {
        'type': 'object',
        'properties': {
            'header': {
                'type': 'object',
                'properties': {
                    'timestamp': {'type': 'number', 'default': time.time}
                },
                'required': ['timestamp', ]
            },
            'body': {}
        },
        'required': ['header', 'body']
    }

    @classmethod
    def create(cls, header=None, body=None):
        schema = copy.deepcopy(cls._schema)
        if header:
            schema['properties']['header'].update(header)
        if body:
            schema['properties']['body'].update(body)
        return schema


class Serializer(serializers.Serializer):
    _schema = Schema.create()


class Data(abc.ABC):
    _serializer = serializers.Serializer()
    _key = ''

    def __init__(self, cache):
        self._cache = cache
        self._data = {'header': {}, 'body': {}}

    def _update_timestamp(self):
        self._data['header']['timestamp'] = time.time()

    def _download_data(self):
        json_str = self._cache.get(self._key)
        if json_str is None:
            return None
        self._data = self._serializer.deserialize(json_str)

    def _upload_data(self):
        json_str = self._serializer.serialize(self._data)
        self._cache.set(self._key, json_str)

    def _get_value(self):
        raise NotImplementedError

    def _set_value(self, value):
        raise NotImplementedError

    @property
    def timestamp(self):
        return self._data['header']['timestamp']

    @property
    def value(self):
        self._download_data()
        return self._get_value()

    @value.setter
    def value(self, v):
        self._set_value(v)
        self._update_timestamp()
        self._upload_data()


class ImageSerializer(serializers.Serializer):
    _schema = Schema.create(body={
        'height': {'type': 'integer'},
        'width': {'type': 'integer'},
        'channel': {'type': 'integer'},
        'image': {'type': 'string'},
    })


class Image(Data):
    _serializer = ImageSerializer()
    _key = 'image'

    def _set_value(self, value):
        if isinstance(value, list):
            value = np.array(value, dtype=np.uint8)
        if not isinstance(value, np.ndarray):
            raise ValueError('Value must be ndarray.')
        if not (len(value.shape) == 2 or len(value.shape) == 3):
            raise ValueError('Dimension of ndarray must be 2 or 3')
        if len(value.shape) == 3 and value.shape[2] != 3:
            raise ValueError('Channel length must be 3.')
        encoded_image = base64.b64encode(value.tostring()).decode()
        if len(value.shape) == 2:
            self._data['body'] = {'height': value.shape[0],
                                  'width': value.shape[1],
                                  'image': encoded_image}
        elif len(value.shape) == 3:
            self._data['body'] = {'height': value.shape[0],
                                  'width': value.shape[1],
                                  'channel': value.shape[2],
                                  'image': encoded_image}

    def _get_value(self):
        decoded_image = base64.b64decode(self._data['body']['image'].encode())
        if 'channel' in self._data['body']:
            image = np.frombuffer(decoded_image, dtype=np.uint8)\
                .reshape((self._data['body']['height'], self._data['body']['width'], self._data['body']['channel']))
        else:
            image = np.frombuffer(decoded_image, dtype=np.uint8)\
                .reshape((self._data['body']['height'], self._data['body']['width']))
        return image
