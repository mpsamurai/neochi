#!/usr/bin/env bash

#docker-compose -f docker-compose-alpine-run-on-x64.yml build
#docker push mpsamurai/neochi:20191201-x64

docker pull mpsamurai/neochi:20191201-raspbian-base
docker build -t mpsamurai/neochi:20191201-raspbian-base -f raspbian-cv2 .
docker push mpsamurai/neochi:20191201-raspbian-base

docker-compose -f docker-compose-raspbian-run-on-x64.yml build
docker push mpsamurai/neochi:20191201-raspbian