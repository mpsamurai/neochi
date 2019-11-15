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
            'body': {
                'type': 'object',
                'properties': {}
            }
        },
        'required': ['header', 'body']
    }

    @classmethod
    def create(cls, header=None, body=None):
        schema = copy.deepcopy(cls._schema)
        if header:
            schema['properties']['header']['properties'].update(header)
        if body:
            schema['properties']['body']['properties'].update(body)
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
