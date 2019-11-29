terraform {
  backend "s3" {
    bucket = "org-mpsamurai-neochi"
    key = "terraform.tfstate"
  }
}

provider "aws" {
}

resource "aws_iam_role" "docker_image_publisher_ec2" {
  name = "DockerImagePublisherEC2"

  assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "docker_image_publisher_ec2_ssm" {
  role = "${aws_iam_role.docker_image_publisher_ec2.name}"
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "docker_image_publisher_ec2_s3" {
  role = "${aws_iam_role.docker_image_publisher_ec2.name}"
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_instance_profile" "docker_image_publisher_ec2" {
  name = "${aws_iam_role.docker_image_publisher_ec2.name}"
  role = "${aws_iam_role.docker_image_publisher_ec2.name}"
}

resource "aws_dynamodb_table" "docker_image_publisher_instance_state" {
  name = "DockerImagePublisherInstanceStates"
  read_capacity = 20
  write_capacity = 20
  hash_key = "name"

  attribute {
    name = "name"
    type = "S"
  }
}

resource "aws_sqs_queue" "docker_image_publisher_job_waiting_queue" {
  name = "docker-image-publisher-job-waiting-queue"
}

resource "aws_sqs_queue" "docker_image_publisher_job_running_queue" {
  name = "docker-image-publisher-job-running-queue"
}

resource "aws_dynamodb_table" "docker_image_publisher_job_table" {
  name = "DockerImagePublisherJobTable"
  read_capacity = 20
  write_capacity = 20
  hash_key = "id"

  attribute {
    name = "id"
    type = "S"
  }
}

resource "aws_s3_bucket" "docker_image_publisher_logs" {
  bucket = "com-mpsamurai-docker-image-publisher-logs"
  acl = "private"
}