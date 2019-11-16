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
import base64
import zipfile
import json
import numpy as np
from sklearn.preprocessing.label import LabelEncoder

from neochi import utils
from neochi.neochi import settings


def fit(zip_path, data_dir, model_dir, model_cls, **kwargs):
    if not os.path.exists(zip_path):
        raise ValueError('data.zip not found.')
    zip = zipfile.ZipFile(zip_path)
    zip.extractall(data_dir)
    zip.close()
    with open(os.path.join(data_dir, 'labels.json')) as f:
        data_json = json.load(f)
    movies = []
    labels = []
    for datum in data_json['labels']:
        dirname = datum['directoryName']
        label = datum['label']
        movie = []
        image_dir = os.path.join(data_dir, dirname)
        for image_file in sorted(os.listdir(image_dir)):
            with open(os.path.join(image_dir, image_file)) as f:
                image_json = json.load(f)
                image = np.fromstring(base64.b64decode(image_json['image']), np.uint8)\
                    .reshape((image_json['height'], image_json['width'], image_json['channel']))
                movie.append(image)
        movies.append(movie)
        labels.append(label)
    X = np.array(movies)
    X = X.reshape((-1, 32, 32, 15))
    le = LabelEncoder()
    y = le.fit_transform(labels)

    model = model_cls(shape=X.shape[1:], labels=labels, **kwargs)
    loss, acc = model.fit(X, y)
    model.save(model_dir)
    return {'loss': loss, 'acc': float(acc)}


if __name__ == '__main__':
    model_cls = utils.load_module(settings.BRAIN['MODEL']['MODULE'])
    fit(settings.BRAIN['DATA']['ZIP_PATH'],
        settings.BRAIN['DATA']['DIR'],
        settings.BRAIN['MODEL']['DIR'],
        model_cls)
