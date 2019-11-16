#!/usr/bin/env bash

#docker-compose -f docker-compose-alpine-run-on-x64.yml build
#docker push mpsamurai/neochi:20191201-x64

docker-compose -f docker-compose-raspbian-run-on-x64.yml build
docker push mpsamurai/neochi:20191201-raspbian