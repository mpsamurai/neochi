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


import redis
from . import base


class RedisCache(base.Cache):
    def __init__(self, host=u'localhost', port=6379, db=0, password=None,
                 socket_timeout=None, socket_connect_timeout=None, socket_keepalive=None, socket_keepalive_options=None,
                 connection_pool=None, unix_socket_path=None, encoding=u'utf-8', encoding_errors=u'strict',
                 charset=None, errors=None, decode_responses=False, retry_on_timeout=False,
                 ssl=False, ssl_keyfile=None, ssl_certfile=None, ssl_cert_reqs=u'required', ssl_ca_certs=None,
                 max_connections=None, single_connection_client=False, health_check_interval=0):
        self._redis = redis.Redis(host=host, port=port, db=db, password=password,
                                  socket_timeout=socket_timeout, socket_connect_timeout=socket_connect_timeout,
                                  socket_keepalive=socket_keepalive,
                                  socket_keepalive_options=socket_keepalive_options,
                                  connection_pool=connection_pool, unix_socket_path=unix_socket_path,
                                  encoding=encoding, encoding_errors=encoding_errors,
                                  charset=charset, errors=errors, decode_responses=decode_responses,
                                  retry_on_timeout=retry_on_timeout,
                                  ssl=ssl, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile,
                                  ssl_cert_reqs=ssl_cert_reqs, ssl_ca_certs=ssl_ca_certs,
                                  max_connections=max_connections, single_connection_client=single_connection_client,
                                  health_check_interval=health_check_interval)

    def set(self, key, value):
        return self._redis.set(key, value)

    def get(self, key):
        return self._redis.get(key)
