#!/usr/bin/env bash

#docker-compose -f docker-compose-alpine-run-on-x64.yml build
#docker push mpsamurai/neochi:20191201-x64

docker build -t mpsamurai/neochi:raspbian-python38 -f Dockerfile-raspbian-python38 .
docker push mpsamurai/neochi:raspbian-python38

docker build -t mpsamurai/neochi:raspbian-cv2 -f Dockerfile-raspbian-cv2 .
docker push mpsamurai/neochi:raspbian-cv2

docker build -t mpsamurai/neochi:raspbian -f Dockerfile-raspbian .
docker push mpsamurai/neochi:raspbian
