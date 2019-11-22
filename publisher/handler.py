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
import boto3
import base64
from botocore.exceptions import ClientError


def create_user_data(**kwargs):
    return """#!/bin/bash
#!/usr/bin/env bash

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
    software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
apt-key fingerprint 0EBFCD88
add-apt-repository \\
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io
usermod -aG docker ubuntu
pip3 install docker-compose

git clone https://github.com/mpsamurai/neochi.git
cd neochi
git checkout feature/dockerize-10

apt-get -y install qemu-user-static
cp /usr/bin/qemu-arm-static .

docker login --username={dockerhub_user} --password={dockerhub_pass}

./build-all.sh

pip3 install awscli
export AWS_ACCESS_KEY_ID={aws_access_key_id}
export AWS_SECRET_ACCESS_KEY={aws_secret_access_key}
export AWS_DEFAULT_REGION={aws_default_region}

S3_LOG={s3_log}
aws s3 cp /var/log/cloud-init-output.log $S3_LOG
S3_LOG_URL=$(aws s3 presign $S3_LOG --expires-in 3600)

for q in $(aws sqs list-queues | jq -r ".QueueUrls[]")
do 
    if [ ${{q##*/}} == "TerminateDockerImagePublisherQueue"  ]
    then 
        aws sqs send-message --queue-url $q \\
            --message-body {{\\"instance_id\\":\\"$(wget -q -O - http://169.254.169.254/latest/meta-data/instance-id)\\"','\\"log\\":\\"$S3_LOG_URL\\"}}
    fi  
done
""".format(**kwargs)


def get_secret():
    secret_name = "neochi"
    region_name = "ap-northeast-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return json.loads(secret)
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            return json.loads(decoded_binary_secret)


def post_message_to_slack(url, username, text):
    data = {
        'username': username,
        'text': text,
    }
    headers = {
        'Content-Type': 'application/json',
    }
    req = urllib.request.Request(url, json.dumps(data).encode(), headers)
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


def create_publisher_instance(event, context):
    if 'instance' in event:
        instance_size = event['instance']
        if instance_size == 'small':
            instance_type = 't2.micro'
        elif instance_size == 'medium':
            instance_type = 't3.medium'
        elif instance_size == 'large':
            instance_type = 't3.2xlarge'
        elif instance_size == 'huge':
            instance_type = 'm5.24xlarge'
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'small, medium, large'})
            }
    else:
        instance_type = 't2.micro'

    secret = get_secret()
    ec2 = boto3.resource('ec2')

    if len([i for i in ec2.instances.filter(Filters=[{'Name': 'instance-state-name',
                                                      'Values': ['pending', 'running']},
                                                     {'Name': 'tag:Name',
                                                      'Values': ['NeochiPublisher']}, ])]):
        return {
            'statusCode': 403,
            'body': json.dumps({'message': 'NeochiPublisher is already running.'})
        }
    instances = ec2.create_instances(ImageId='ami-0f6b4f4104d26f399',
                                     InstanceType=instance_type,
                                     BlockDeviceMappings=[{
                                         'DeviceName': '/dev/sda1',
                                         'Ebs': {
                                             'VolumeSize': 500
                                         }
                                     }, ],
                                     MinCount=1,
                                     MaxCount=1,
                                     UserData=create_user_data(
                                         dockerhub_user=secret['DOCKERHUB_USER'],
                                         dockerhub_pass=secret['DOCKERHUB_PASS'],
                                         aws_access_key_id=secret['AWS_ACCESS_KEY_ID'],
                                         aws_secret_access_key=secret['AWS_SECRET_ACCESS_KEY'],
                                         aws_default_region=secret['AWS_DEFAULT_REGION'],
                                         s3_log=secret['S3_LOG'],
                                     ),
                                     KeyName='junya',
                                     TagSpecifications=[
                                         {
                                             'ResourceType': 'instance',
                                             'Tags': [
                                                 {
                                                     'Key': 'Name',
                                                     'Value': 'NeochiPublisher'
                                                 }
                                             ]
                                         },
                                     ])
    instances[0].wait_until_running()
    instances[0].load()
    post_message_to_slack(secret['SLACK_WEBHOOK_URL'], secret['SLACK_USER'],
                          '======================================\n'
                          'Create an instance to build Neochi\n\n'
                          'Instance ID: {}\n'
                          'SSH login: ```ssh ubuntu@{}```\n'
                          '======================================'
                          .format(instances[0].instance_id, instances[0].public_dns_name))
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'OK'})
    }


def terminate_publisher_instance(event, context):
    ids = []
    logs = []
    for record in event['Records']:
        body = json.loads(record['body'])
        ids.append(body['instance_id'])
        logs.append(body['log'])
    ec2 = boto3.resource('ec2')
    ec2.instances.filter(InstanceIds=ids).terminate()
    secret = get_secret()
    post_message_to_slack(secret['SLACK_WEBHOOK_URL'], secret['SLACK_USER'],
                          '======================================\n'
                          'Terminate the instance building Neochi\n\n'
                          'Instance ID: {}\n'
                          'Log URL: {}\n'
                          '======================================'
                          .format(ids[0], logs[0]))
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'OK'})
    }
