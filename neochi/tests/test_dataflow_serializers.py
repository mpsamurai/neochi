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


import unittest
import time
from ..core.dataflow import serializers


class MockData:
    def __init__(self):
        self._value = {'key': None}

    @property
    def value(self):
        return self._value['key']

    @value.setter
    def value(self, v):
        self._value['key'] = v

    @classmethod
    def __from_json__(cls, json_obj):
        obj = MockData()
        obj.value = json_obj['key']
        return obj

    def __to_json__(self):
        return self._value


class MockSerializer(serializers.Serializer):
    _schema = {
        'type': 'object',
        'properties': {
            'key0': {'type': 'string'},
            'key1': {
                'type': 'object',
                'properties': {
                    'key1.1': {'type': 'number'},
                    'key1.2': {'type': 'number', 'default': time.time}
                },
                'required': ['key1.2', ]
            },
        },
        'required': ['key0', 'key1', ]
    }


class TestEncoder(unittest.TestCase):
    def test_it_encodes_and_decodes_class(self):
        mc = MockData()
        encoded = serializers.Encoder().encode(mc)
        decoded = serializers.Decoder().decode(encoded)
        self.assertEqual(decoded.value, mc.value)


class TestSerializer(unittest.TestCase):
    def test_it_only_accepts_valid_json(self):
        valid_json_obj = {
            'key0': 'string',
            'key1': {
                'key1.1': 123.,
            }
        }
        serializer = MockSerializer()
        serializer.validate(valid_json_obj)
        self.assertTrue(isinstance(valid_json_obj['key1']['key1.2'], float))

        invalid_json_obj = {
            'key0': 1,
            'key1': {
                'key1.1': 123.,
            }
        }
        with self.assertRaises(serializers.exceptions.ValidationError):
            serializer.validate(invalid_json_obj)

    def test_if_it_serializes_and_deserializes_correctly(self):
        valid_json_obj = {
            'key0': 'string',
            'key1': {
                'key1.1': 123.,
            }
        }
        serializer = MockSerializer()
        serialized = serializer.serialize(valid_json_obj)
        deserialized = serializer.deserialize(serialized)
        self.assertEqual(valid_json_obj['key0'], deserialized['key0'])
        self.assertEqual(valid_json_obj['key1']['key1.1'], deserialized['key1']['key1.1'])
        self.assertTrue(valid_json_obj['key1']['key1.2'], deserialized['key1']['key1.2'])
