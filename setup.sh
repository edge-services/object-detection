#!/bin/bash

while getopts d:a: flag
do
    case "${flag}" in
        a) arch=${OPTARG};;
        d) data=${OPTARG};;
    esac
done

if [ -z $data ]; then
  DATA_DIR="data"
else
  DATA_DIR="$data"
fi

mkdir -p $DATA_DIR/model
mkdir -p $DATA_DIR/frames

# if [ $# -eq 0 ]; then
#   DATA_DIR="./"
# else
#   DATA_DIR="$1"
# fi

# Install Python dependencies
python3 -m pip install pip --upgrade
python3 -m pip install -r requirements.txt

# Download TF Lite models
FILE=${DATA_DIR}/model/model.tflite
if [ ! -f "$FILE" ]; then
  curl \
    -L 'https://tfhub.dev/tensorflow/lite-model/efficientdet/lite0/detection/metadata/1?lite-format=tflite' \
    -o ${FILE}
fi

FILE=${DATA_DIR}/model/model_edgetpu.tflite
if [ ! -f "$FILE" ]; then
  curl \
    -L 'https://storage.googleapis.com/download.tensorflow.org/models/tflite/edgetpu/efficientdet_lite0_edgetpu_metadata.tflite' \
    -o ${FILE}
fi

echo -e "Downloaded files are in ${DATA_DIR}"
