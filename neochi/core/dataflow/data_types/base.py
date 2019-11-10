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


__author__ = 'Junya Kaneko<junya@mpsamurai.org>'


import copy
import json
import base64
import time
from collections import abc
import importlib
import numpy as np


class PayloadJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, '__json__'):
            json_obj = o.__json__()
            json_obj['__json__'] = '{}/{}'.format(o.__module__, o.__class__.__name__)
            return json_obj
        return super().default(o)


class PayloadJsonDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self._object_hook, *args, **kwargs)

    def _object_hook(self, obj):
        if '__json__' in obj:
            module_path, cls_name = obj['__json__'].split('/')
            cls = getattr(importlib.import_module(module_path), cls_name)
            del obj['__json__']
            return cls(obj)
        else:
            return obj


class TypedDict(abc.MutableMapping):
    _required_fields = {}

    def __init__(self, *args, **kwargs):
        self.__dict__.update(*args, **kwargs)
        self._validate()

    def _validate(self):
        for key, config in self._required_fields.items():
            if key not in self.__dict__:
                if not config['default']:
                    raise ValueError('Key {} is required.'.format(key))
                else:
                    self.__dict__[key] = config['default']() if callable(config['default']) else config['default']
            if not isinstance(self.__dict__[key], config['type']):
                raise ValueError('Type {} is expected for key {}'.format(config['type'], key))

    def __iter__(self):
        return self.__dict__.__iter__()

    def __len__(self):
        return len(self.__dict__)

    def __delitem__(self, v):
        del self.__dict__[v]
        self._validate()

    def __getitem__(self, k):
        return self.__dict__[k]

    def __setitem__(self, k, v):
        self.__dict__[k] = v
        self._validate()

    def __repr__(self):
        return '{}, {}({})'.format(super().__repr__(), self.__class__.__name__, self.__dict__)

    def __json__(self):
        return self.__dict__


class Header(TypedDict):
    _required_fields = {
        'timestamp': {'type': float, 'default': time.time}
    }
    
    @property
    def timestamp(self):
        return self.__dict__['timestamp']

    def update_timestamp(self):
        self.__dict__['timestamp'] = self._required_fields['timestamp']['default']()


class Body(TypedDict):
    pass


class Payload:
    _header_cls = Header
    _body_cls = Body

    def __init__(self, payload={}):
        self._value = {
            'header': self._header_cls({}),
            'body': self._body_cls({})
        }
        if 'header' in payload:
            self._value['header'].update(payload['header'])
        if 'body' in payload:
            self._value['body'].update(payload['body'])

    @property
    def header(self):
        return copy.deepcopy(self._value['header'])

    def set_header(self, header):
        self._value['header'] = self._header_cls(header)
        self._value['header'].update_timestamp()

    def update_header(self, header):
        self._value['header'].update(header)
        self._value['header'].update_timestamp()

    @property
    def body(self):
        return copy.deepcopy(self._value['body'])

    def set_body(self, body):
        self._value['body'] = body
        self._value['header'].update_timestamp()

    def update_body(self, body):
        self._value['body'].update(body)
        self._value['header'].update_timestamp()

    @property
    def value(self):
        return copy.deepcopy(self._value)

    def set_value(self, value):
        self.set_header(value['header'])
        self.set_body(value['body'])

    def update_value(self, value):
        self.update_header(value['header'])
        self.update_body(value['body'])

    def to_json(self):
        return json.dumps(self._value, cls=PayloadJsonEncoder)

    def from_json(self, json_obj):
        self.set_value(json.loads(json_obj, cls=PayloadJsonDecoder))


class BaseDataType:
    readonly = False

    def __init__(self):
        self._payload = Payload()

    def _validate_value(self, value):
        return value

    def _get_value(self):
        return self._payload.body

    def _set_value(self, value):
        self._payload.set_body(self._validate_value(value))

    @property
    def header(self):
        return self._payload.header

    @property
    def value(self):
        return self._get_value()

    @value.setter
    def value(self, val):
        if isinstance(val, bytes):
            self._payload.from_json(val.decode())
        else:
            self._set_value(val)

    def to_json(self):
        return self._payload.to_json()

    def __setattr__(self, key, value):
        if self.readonly and key == 'value':
            raise AttributeError('{} is readonly.'.format(self.__class__.__name__))
        else:
            super().__setattr__(key, value)


class Json(BaseDataType):
    pass


class AtomicDataType(BaseDataType):
    data_type = None
    default_value = None

    def __init__(self):
        super().__init__()
        self._payload.set_body({'value': self.default_value})

    def _validate_value(self, value):
        if not isinstance(value['value'], self.data_type):
            raise ValueError
        return value

    def _get_value(self):
        return super()._get_value()['value']

    def _set_value(self, value):
        super()._set_value({'value': value})


class Null(AtomicDataType):
    data_type = type(None)
    default_value = None
    readonly = True


class Int(AtomicDataType):
    data_type = int
    default_value = 0


class Float(AtomicDataType):
    data_type = float
    default_value = 0.


class Str(AtomicDataType):
    data_type = str
    default_value = ''


class Image(BaseDataType):
    def _set_value(self, value):
        if isinstance(value, list):
            value = np.array(value, dtype=np.uint8)
        if not isinstance(value, np.ndarray):
            raise ValueError('Value must be ndarray')
        if not (len(value.shape) == 2 or len(value.shape) == 3):
            raise ValueError('Dimension of ndarray must be 2 or 3')
        if len(value.shape) == 3 and value.shape[2] != 3:
            raise ValueError('Channel length must be 3.')
        encoded_image = base64.b64encode(value.tostring()).decode()
        if len(value.shape) == 2:
            super()._set_value({'height': value.shape[0],
                                'width': value.shape[1],
                                'image': encoded_image})
        elif len(value.shape) == 3:
            super()._set_value({'height': value.shape[0],
                                'width': value.shape[1],
                                'channel': value.shape[2],
                                'image': encoded_image})

    def _get_value(self):
        value = super()._get_value()
        if not value:
            return None
        if isinstance(value['image'], str):
            decoded_image = base64.b64decode(value['image'].encode())
            if 'channel' in value:
                value['image'] = np.frombuffer(decoded_image, dtype=np.uint8)\
                    .reshape((value['height'], value['width'], value['channel']))
            else:
                value['image'] = np.frombuffer(decoded_image, dtype=np.uint8)\
                    .reshape((value['height'], value['width']))
        return value['image']
