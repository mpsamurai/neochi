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

import uuid
import boto3
import json
from datetime import datetime
from . import machine


class State:
    QUEUED = 'QUEUED'
    INPROGRESS = 'INPROGRESS'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'


class Manager:
    def __init__(self, credential={}):
        self._credential = credential
        self._sqs = None
        self._dynamodb = None

    def _get_sqs(self):
        if self._sqs is None:
            self._sqs = boto3.client('sqs', **self._credential)
        return self._sqs

    def _get_dynamodb(self):
        if self._dynamodb is None:
            self._dynamodb = boto3.resource('dynamodb', **self._credential)
        return self._dynamodb

    def push_job(self, command, output_dir, machine_name):
        job = {
            'config': {
                'command': command,
                'output_dir': output_dir,
                'machine_name': machine_name,
            },
            'id': str(uuid.uuid4()),
            'state': State.QUEUED,
            'created_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            # 'machine_id': '',
            # 'command_id': '',
            # 'success': bool,
            # 'output_url': '',
            # 'output_download_url': '',
            # 'executed_at': '',
            # 'done_at': '',
        }

        dynamodb = self._get_dynamodb()
        job_table = dynamodb.Table('DockerImagePublisherJobTable')
        job_table.put_item(Item=job)

        sqs = self._get_sqs()
        queue_url = sqs.get_queue_url(QueueName='docker-image-publisher-job-waiting-queue')['QueueUrl']
        sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps({'id': job['id']}))
        return job

    def execute(self):
        executed_jobs = []
        errors = []
        dynamodb = self._get_dynamodb()
        job_table = dynamodb.Table('DockerImagePublisherJobTable')

        sqs = self._get_sqs()
        waiting_queue_url = sqs.get_queue_url(QueueName='docker-image-publisher-job-waiting-queue')['QueueUrl']
        running_queue_url = sqs.get_queue_url(QueueName='docker-image-publisher-job-running-queue')['QueueUrl']
        messages = sqs.receive_message(QueueUrl=waiting_queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=10)
        if 'Messages' not in messages:
            return {'jobs': executed_jobs, 'errors': errors}
        for message in messages['Messages']:
            job_id = json.loads(message['Body'])['id']
            try:
                job = job_table.get_item(TableName='DockerImagePublisherJobTable', Key={'id': job_id}, )['Item']
            except KeyError:
                continue
            try:
                m = machine.Machine(self._credential)
                m.attach(name=job['config']['machine_name'])
                if not m.is_running:
                    m.start()
                    continue
                if not m.is_initialized:
                    continue
                if m.is_available:
                    m.disable()
                    job['machine_id'] = m.id
                    job['command_id'] = m.command(job['config']['command'], job['config']['output_dir'])
                    job['state'] = State.INPROGRESS
                    job['executed_at'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                    job_table.put_item(Item=job)
                    sqs.send_message(QueueUrl=running_queue_url, MessageBody=json.dumps({'id': job['id']}))
                    sqs.delete_message(QueueUrl=waiting_queue_url, ReceiptHandle=message['ReceiptHandle'])
                    executed_jobs.append(job)
            except KeyError:
                pass
            except machine.MachineDoesNotExist:
                errors.append({'id': job_id,
                               'code': 'machine_does_not_exist',
                               'message': job['config']['machine_name']})
        return {'jobs': executed_jobs, 'errors': errors}

    def collect_outputs(self):
        outputs = []
        dynamodb = self._get_dynamodb()
        job_table = dynamodb.Table('DockerImagePublisherJobTable')

        sqs = self._get_sqs()
        queue_url = sqs.get_queue_url(QueueName='docker-image-publisher-job-running-queue')['QueueUrl']
        messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=10)
        if 'Messages' not in messages:
            return outputs
        for message in messages['Messages']:
            try:
                body = json.loads(message['Body'])
                job = job_table.get_item(TableName='DockerImagePublisherJobTable', Key={'id': body['id']}, )['Item']
                m = machine.Machine(self._credential)
                m.attach(id=job['machine_id'])
                success, job['output_url'] = m.get_output_url(job['command_id'])
                if success:
                    job['state'] = State.SUCCESS
                else:
                    job['state'] = State.FAILED
                job['output_download_url'] = m.get_output_download_url(job['output_url'])
                job['done_at'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                job_table.put_item(Item=job)
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message['ReceiptHandle'])
                m.stop()
                m.enable()
                outputs.append(job)
            except KeyError:
                pass
            except TimeoutError:
                pass
            except SystemError:
                pass
        return outputs

    def get(self, job_id):
        dynamodb = self._get_dynamodb()
        job_table = dynamodb.Table('DockerImagePublisherJobTable')
        try:
            return job_table.get_item(TableName='DockerImagePublisherJobTable', Key={'id': job_id}, )['Item']
        except KeyError:
            return None
