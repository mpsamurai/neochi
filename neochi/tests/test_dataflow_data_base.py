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
from ..core.dataflow.data import base
from ..core.dataflow.backends import caches
from ..neochi import settings


class TestJsonData(unittest.TestCase):
    def setUp(self):
        self.cache = caches.get_cache(settings.DATAFLOW['BACKEND']['CACHE']['MODULE'],
                                      **settings.DATAFLOW['BACKEND']['CACHE']['KWARGS'])

    def test_if_it_accepts_json(self):
        data0 = base.JsonData(self.cache)
        data0.value = {'key': 'value'}
        data1 = base.JsonData(self.cache)
        self.assertEqual(data0.value['key'], data1.value['key'])

    def test_if_it_raises_exception_if_required_fields_are_missed(self):
        class TestClass(base.JsonData):
            _required_field = {'rkey': {'type': str}}

        data = TestClass(self.cache)
        with self.assertRaises(ValueError):
            data.value = {}

    def test_if_it_sets_default_value_if_required_fields_are_missed(self):
        class TestClass(base.JsonData):
            _required_field = {'rkey': {'type': str, 'default': 'default'}}

        data = TestClass(self.cache)
        data.value = {}
        self.assertEqual(data.value['rkey'], 'default')

    def test_if_raises_exception_if_type_of_required_fields_are_mismatched(self):
        class TestClass(base.JsonData):
            _required_field = {'rkey': {'type': str}}

        data = TestClass(self.cache)
        with self.assertRaises(ValueError):
            data.value = {'rkey': 100}
