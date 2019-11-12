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


from .. import data_types


class BaseData:
    _data_type_cls = None
    _key = ''

    def __init__(self, cache):
        self._cache = cache
        self._data_type = self._data_type_cls()

    def _validate(self, value):
        return value

    @property
    def timestamp(self):
        return self._data_type.header.timestamp

    @property
    def value(self):
        self._data_type.value = self._cache.get(self._key)
        return self._validate(self._data_type.value)

    @value.setter
    def value(self, val):
        self._data_type.value = self._validate(val)
        self._cache.set(self._key, self._data_type.to_json())


class JsonData(BaseData):
    _data_type_cls = data_types.Json
    _key = ''
    _required_field = {}

    def _validate(self, value):
        for key in self._required_field:
            if key not in value:
                if 'default' in self._required_field[key]:
                    if callable(self._required_field[key]['default']):
                        value[key] = self._required_field[key]['default']()
                    else:
                        value[key] = self._required_field[key]['default']
                else:
                    raise ValueError('Key "{}" is required.'.format(key))
            if not isinstance(value[key], self._required_field[key]['type']):
                raise ValueError('Key "{}" expects type "{}" but type "{}" is given.'.format(
                    key, self._required_field[key]['type'], type(value[key])))
        return value