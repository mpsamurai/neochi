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
import urllib.request
import urllib.error


class Message:
    def __init__(self, credential):
        if 'url' not in credential:
            raise ValueError('url must be specified in credential.')
        self._credential = credential

    def post(self, data):
        if 'username' not in data:
            data['username'] = 'Neochi'
        if 'text' not in data:
            raise ValueError('Text must be specified')
        headers = {
            'Content-Type': 'application/json',
        }
        req = urllib.request.Request(self._credential['url'], json.dumps(data).encode(), headers)
        try:
            with urllib.request.urlopen(req) as res:
                return {
                    'statusCode': 200,
                    'body': 'OK'
                }
        except urllib.error.URLError as err:
            return {
                'statusCode': 400,
                'body': err.reason
            }
