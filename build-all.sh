#!/usr/bin/env bash

usage() {
  echo "Usage: $0: [-b branch name] [-p number of processors]" 2>&1
  exit 1
}


while getopts ":b:p:" o
do
  case $o in
  b)
    b=${OPTARG}
    ;;
  p)
    p=${OPTARG}
    ;;
  *)
    usage
    ;;
  esac
done

if [ -z "$b" ] || [ -z "$p" ]
then
  usage
fi

#echo "========================================================="
#echo "Build mpsamurai/neochi:raspbian-python38"
#echo "========================================================="
#docker build -t mpsamurai/neochi:raspbian-python38 --build-arg n_proc="$p" -f Dockerfile-raspbian-python38 .
#docker push mpsamurai/neochi:"$b"-python38
#
#echo "========================================================="
#echo "Build mpsamurai/neochi:raspbian-cv2"
#echo "========================================================="
#docker build -t mpsamurai/neochi:raspbian-cv2 --build-arg n_proc="$p" -f Dockerfile-raspbian-cv2 .
#docker push mpsamurai/neochi:"$b"-cv2
#
#echo "========================================================="
#echo "Build mpsamurai/neochi:raspbian"
#echo "========================================================="
#docker build -t mpsamurai/neochi:raspbian --build-arg n_proc="$p" -f Dockerfile-raspbian .
#docker push mpsamurai/neochi:"$b"

echo "========================================================="
echo "Build mpsamurai/neochi:raspbian"
echo "========================================================="
docker build -t mpsamurai/neochi:raspbian --build-arg n_proc="$p" -f Dockerfile-raspbian .
docker push mpsamurai/neochi:"$b"