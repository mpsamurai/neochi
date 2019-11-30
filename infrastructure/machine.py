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
import time
from urllib.parse import urlparse
import boto3


def create_user_data():
    return """#!/usr/bin/env bash
apt-get update
apt-get install -y python3-pip python3-dev git
apt-get remove docker docker-engine docker.io containerd runc
apt-get update
apt-get install -y \\
    apt-transport-https \\
    ca-certificates \\
    curl \\
    wget \\
    jq \\
    gnupg-agent \\
    software-properties-common \\
    qemu-user-static
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
apt-key fingerprint 0EBFCD88
add-apt-repository \\
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io
usermod -aG docker ubuntu
pip3 install docker-compose
pip3 install awscli
"""


class _Config:
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
                    'Value': 'DockerImagePublisher'
                },
            ]
        }, ],
        "IamInstanceProfile": {
            'Name': 'DockerImagePublisherEC2'
        },
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
        if 'UserData' not in self._config:
            self._config['UserData'] = '{}\ntouch /initialized'.format(create_user_data())
        else:
            self._config['UserData'] = '{}\ntouch /initialized'.format(self._config['UserData'])

    def get(self):
        return self._config


class MachineInitializationFailure(Exception):
    pass


class MachineDoesNotExist(Exception):
    pass


class MachineIsInitializing(Exception):
    pass


class MachineIsNotAvailable(Exception):
    pass


class Machine:
    def __init__(self, credential={}):
        self._credential = credential
        self._instance = None
        self._ec2 = None
        self._ssm = None
        self._dynamodb = None
        self._s3 = None

    def _get_resource(self):
        if not self._ec2:
            self._ec2 = boto3.resource('ec2', **self._credential)
        return self._ec2

    def _get_ssm(self):
        if not self._ssm:
            self._ssm = boto3.client('ssm', **self._credential)
        return self._ssm

    def _get_dynamodb(self):
        if not self._dynamodb:
            self._dynamodb = boto3.client('dynamodb', **self._credential)
        return self._dynamodb

    def _get_s3(self):
        if not self._s3:
            self._s3 = boto3.client('s3', **self._credential)
        return self._s3

    def _set_availability(self, availability):
        dynamo_db = self._get_dynamodb()
        dynamo_db.put_item(TableName='DockerImagePublisherInstanceStates', Item={
            'name': {'S': self.name},
            'availability': {'BOOL': availability}
        })

    def _get_availability(self):
        dynamo_db = self._get_dynamodb()
        response = dynamo_db.get_item(TableName='DockerImagePublisherInstanceStates', Key={
            'name': {'S': self.name}
        })
        return list(response['Item']['availability'].values())[0]

    @property
    def name(self):
        return [i['Value'] for i in self._instance.tags if i['Key'] == 'Name'][0]

    @property
    def id(self):
        return self._instance.instance_id

    @property
    def public_dns_name(self):
        return self._instance.public_dns_name

    @property
    def is_available(self):
        return self._get_availability()

    @property
    def is_running(self):
        return self._instance.state['Name'] == 'running'

    @property
    def is_initialized(self):
        ssm = self._get_ssm()
        response = ssm.send_command(
            InstanceIds=[self._instance.instance_id, ],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands': [
                    'bash -c "if [ -f "/initialized" ]; then echo "True"; else echo "False"; fi"'
                ]
            }
        )
        command_id = response['Command']['CommandId']
        output = None
        for _ in range(40):
            response = ssm.list_command_invocations(
                CommandId=command_id,
                Details=True,
            )
            if len(response['CommandInvocations']) == 0:
                pass
            elif response['CommandInvocations'][0]['Status'] == 'Success':
                output = response['CommandInvocations'][0]['CommandPlugins'][0]['Output']
                break
            elif response['CommandInvocations'][0]['Status'] in ['Cancelled', 'TimedOut', 'Failed', 'Cancelling']:
                raise MachineInitializationFailure('Cannot get initialization state of instance {}'.format(self.name))
            time.sleep(1.)
        if output is None:
            raise MachineInitializationFailure('Cannot get initialization state of instance {}'.format(self.name))
        return output.strip() == 'True'

    def attach(self, name=None, id=None):
        if (name is None and id is None) or (name is not None and id is not None):
            raise ValueError('Either name or id must be specified.')
        ec2 = self._get_resource()
        try:
            if name is not None:
                filters = [{'Name': 'instance-state-name', 'Values': ['pending', 'running', 'stopped', ]},
                           {'Name': 'tag:Name', 'Values': [name, ]}]
                instances = ec2.instances.filter(Filters=filters)
            else:
                instances = ec2.instances.filter(InstanceIds=[id, ])
            self._instance = [i for i in instances][0]
        except IndexError:
            raise MachineDoesNotExist('Instance {} does not exist.'.format(name))

    def reload(self):
        self._instance.load(self._instance.instance_id)

    def create(self, config={}):
        ec2 = self._get_resource()
        config = _Config(config)
        self._instance = ec2.create_instances(**config.get())[0]
        self._set_availability(True)

    def start(self):
        self._instance.start()

    def stop(self):
        self._instance.stop()

    def terminate(self):
        self._instance.terminate()
        dynamo_db = self._get_dynamodb()
        dynamo_db.delete_item(TableName='DockerImagePublisherInstanceStates', Key={'name': {'S': self.name}})

    def wait_until_running(self):
        self._instance.wait_until_running()

    def wait_until_initialized(self):
        for i in range(40):
            try:
                if self.is_initialized:
                    return
            except Exception:
                # TODO: Need appropriate error handling.
                pass
            time.sleep(1.)
        raise TimeoutError('Initialization does not complete.')

    def wait_until_stopped(self):
        self._instance.wait_until_stopped()

    def wait_until_terminated(self):
        self._instance.wait_until_terminated()

    def enable(self):
        self._set_availability(True)

    def disable(self):
        self._set_availability(False)

    def command(self, cmd, output_dir):
        parsed_output_dir = urlparse(output_dir)
        ssm = self._get_ssm()
        response = ssm.send_command(
            InstanceIds=[self._instance.instance_id, ],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands': [cmd, ]
            },
            OutputS3BucketName=parsed_output_dir.netloc if output_dir else None,
            OutputS3KeyPrefix=parsed_output_dir.path if output_dir else None
        )
        return response['Command']['CommandId']

    def get_output(self, command_id, n_trials=3):
        output = None
        success = False
        ssm = self._get_ssm()
        for _ in range(n_trials):
            response = ssm.list_command_invocations(
                CommandId=command_id,
                Details=True,
            )
            if len(response['CommandInvocations']) == 0:
                pass
            elif response['CommandInvocations'][0]['Status'] == 'Success':
                success = True
                output = response['CommandInvocations'][0]['CommandPlugins'][0]['Output']
                break
            elif response['CommandInvocations'][0]['Status'] == 'Failed':
                success = False
                output = response['CommandInvocations'][0]['CommandPlugins'][0]['Output']
                break
            elif response['CommandInvocations'][0]['Status'] in ['Cancelled', 'Cancelling']:
                raise SystemError('The command {} at the instance {} was canceled.'.format(command_id, self.name))
            elif response['CommandInvocations'][0]['Status'] == 'TimedOut':
                break
            time.sleep(1.)
        if output is None:
            raise TimeoutError('Could not get the output of the command {} at instance {}.'.format(command_id, self.name))
        return success, output

    def get_output_url(self, command_id):
        url = None
        success = False
        ssm = self._get_ssm()
        for _ in range(40):
            response = ssm.list_command_invocations(
                CommandId=command_id,
                Details=True,
            )
            if len(response['CommandInvocations']) == 0:
                pass
            elif response['CommandInvocations'][0]['Status'] == 'Success':
                success = True
                url = response['CommandInvocations'][0]['CommandPlugins'][0]['StandardOutputUrl']
                break
            elif response['CommandInvocations'][0]['Status'] == 'Failed':
                success = False
                url = response['CommandInvocations'][0]['CommandPlugins'][0]['StandardOutputUrl']
                break
            elif response['CommandInvocations'][0]['Status'] in ['Cancelled', 'Cancelling']:
                raise SystemError('The command {} at the instance {} was canceled.'.format(command_id, self.name))
            elif response['CommandInvocations'][0]['Status'] == 'TimedOut':
                break
            time.sleep(1.)
        if url is None:
            raise TimeoutError('Could not get the output of the command {} at instance {}.'.format(command_id, self.name))
        return success, url

    def get_output_download_url(self, url, expired_in=3600):
        path = urlparse(url).path.split('/')
        s3 = self._get_s3()
        return s3.generate_presigned_url('get_object', Params={
            'Bucket': path[1],
            'Key': '/'.join(path[2:])
        }, ExpiresIn=expired_in)


