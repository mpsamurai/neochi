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


import json
import importlib
import jsonschema
from . import validators


class Encoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, '__to_json__'):
            json_obj = o.__to_json__()
            json_obj['__json__'] = '{}/{}'.format(o.__module__, o.__class__.__name__)
            return json_obj
        return super().default(o)


class Decoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self._object_hook, *args, **kwargs)

    def _object_hook(self, obj):
        if '__json__' in obj:
            module_path, cls_name = obj['__json__'].split('/')
            cls = getattr(importlib.import_module(module_path), cls_name)
            del obj['__json__']
            return cls.__from_json__(obj)
        else:
            return obj


class BaseSerializer(type):
    def __new__(mcs, name, bases, attrs):
        if '_validator' in attrs:
            attrs['_validator'] \
                = mcs._create_validator(attrs['_validator'], attrs['_validator_extensions'], attrs['_schema'])
        else:
            for base in bases:
                if issubclass(base, Serializer):
                    attrs['_validator'] = getattr(base, '_validator').__class__(attrs[''])
        return type.__new__(mcs, name, bases, attrs)

    @staticmethod
    def _create_validator(validator, extensions, schema):
        for extension in extensions:
            validator = extension(validator)
        return validator(schema)


class Serializer:
    """ Serializing object to JSON and deserializing JSON to object. """
    _encoder = Encoder
    _decoder = Decoder
    _validator = jsonschema.validators.Draft7Validator
    _validator_extensions = [validators.default_value_extension, ]
    _schema = {
        'type': 'object',
        'properties': {},
    }

    def __init__(self):
        self._validator = self._create_validator()

    def _create_validator(self):
        validator = self._validator
        for extension in self._validator_extensions:
            validator = extension(validator)
        return validator(self._schema)

    def validate(self, obj):
        self._validator.validate(obj)

    def serialize(self, obj):
        """
        Encode object to JSON.
        :param obj: object encoded.
        :return: JSON string
        """
        self._validator.validate(obj)
        return json.dumps(obj, cls=self._encoder)

    def deserialize(self, json_str):
        """
        Decode JSON to object.
        :param json_str:
        :return: dict, list or any object having __from_json__ method.
        """
        obj = json.loads(json_str, cls=self._decoder)
        self._validator.validate(obj)
        return obj
