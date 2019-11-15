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


from . import base
from .. import serializers


class Image(base.Image):
    _key = 'eye:image'


class State(base.Data):
    class Serializer(serializers.Serializer):
        _schema = base.Schema.create(body={
            'type': 'object',
            'properties': {
                'size': {'type': 'array', 'default': [32, 32]},
                'rotation_pc': {'type': 'number', 'default': 0.},
                'rotation_pi': {'type': 'number', 'default': 90},
                'fps': {'type': 'number', 'default': 1.},
                'is_capturing': {'type': 'boolean', 'default': True}
            },
            'required': ['size', 'rotation_pc', 'rotation_pi', 'fps', 'is_capturing']
        })

    _serializer = Serializer()
    _key = 'eye:state'

    def _get_value(self):
        return self._data['body']

    def _set_value(self, value):
        self._data['body'].update(value)
