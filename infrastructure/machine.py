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


import copy
import uuid
import boto3


class Config:
    default = {
        'ImageId': 'ami-0f6b4f4104d26f399',
        'InstanceType': 't2.micro',
        'BlockDeviceMappings': [{
            'DeviceName': '/dev/sda1',
            'Ebs': {
                'VolumeSize': 500,
            }
        }, ],
        'MinCount': 1,
        'MaxCount': 1,
        'KeyName': 'neochi',
        'TagSpecifications': [{
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'Neochi'
                },
            ]
        }, ],
    }

    def __init__(self, params):
        self._config = copy.deepcopy(self.default)
        for spec in self._config['TagSpecifications']:
            if spec['ResourceType'] != 'instance':
                continue
            for tag in spec['Tags']:
                if tag['Key'] == 'Name':
                    tag['Value'] = '{}-{}'.format(tag['Value'], uuid.uuid4())
        self._config.update(params)

    def get(self):
        return self._config


class Machine:
    def __init__(self, credential):
        self._credential = credential
        self._instance = None
        self._ec2 = None

    def _get_resource(self):
        if not self._ec2:
            self._ec2 = boto3.resource('ec2', **self._credential)
        return self._ec2

    @property
    def name(self):
        return [i['Value'] for i in self._instance.tags if i['Key'] == 'Name'][0]

    @property
    def id(self):
        return self._instance.instance_id

    @property
    def public_dns_name(self):
        return self._instance.public_dns_name

    def load(self, name=None, id=None):
        if (name is None and id is None) or (name is not None and id is not None):
            raise ValueError('Either name or id must be specified.')
        ec2 = self._get_resource()
        try:
            if name is not None:
                filters = [{'Name': 'instance-state-name', 'Values': ['stopped', ]},
                           {'Name': 'tag:Name', 'Values': [name, ]}]
                instances = ec2.instances.filter(Filters=filters)
            else:
                instances = ec2.instances.filter(InstanceIds=['id', ])
            self._instance = [i for i in instances][0]
        except IndexError:
            raise ValueError('Instance {} does not exist.'.format(name))

    def reload(self):
        self._instance.load()

    def create(self, config):
        ec2 = self._get_resource()
        config = Config(config)
        self._instance = ec2.create_instances(**config.get())[0]

    def start(self):
        self._instance.start()

    def stop(self):
        self._instance.stop()

    def terminate(self):
        self._instance.terminate()

    def wait_until_running(self):
        self._instance.wait_until_running()

    def wait_until_stopped(self):
        self._instance.wait_until_stopped()

    def wait_until_terminated(self):
        self._instance.wait_until_terminated()
