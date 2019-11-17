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


import os
import pickle
import time
import numpy as np
from sklearn.preprocessing.label import LabelEncoder
from neochi import utils
from neochi.core.dataflow.backends import caches
from neochi.core.dataflow.data import eye
from neochi.neochi import settings


def wait(start_time):
    time.sleep(np.max((0, 1. - (time.time() - start_time))))


if __name__ == '__main__':
    cache = caches.get_cache(settings.DATAFLOW['BACKEND']['CACHE']['MODULE'],
                             **settings.DATAFLOW['BACKEND']['CACHE']['KWARGS'])
    image = eye.Image(cache)
    state = eye.State(cache)

    with open(os.path.join(settings.BRAIN['MODEL']['DIR'], 'label_encoder.pickle'), 'rb') as f:
        le = pickle.load(f)

    model = utils.load_module(settings.BRAIN['MODEL']['MODULE'])()
    model.load(settings.BRAIN['MODEL']['DIR'])

    images = []
    history = []
    while True:
        start_time = time.time()
        if not state.value['is_capturing']:
            images = []
            wait(start_time)
            continue

        if len(images) < 5:
            images.append(image.value)
            wait(start_time)
            continue

        if len(images) == 5:
            images.pop(0)
            images.append(image.value)

        X = np.array(images)
        X = X.reshape((-1, 32, 32, 15))
        behavior = le.classes_[model.predict(X)[0]]
        history.append(1 if behavior == 'no_move_laying' else 0)
        if len(history) > 10:
            history.pop(0)
        print('Detected:', behavior)
        print('Possibility', np.sum(history) / len(history))
        wait(start_time)
