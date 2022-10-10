
# TensorFlow Lite Python object detection example with Raspberry Pi

This example uses [TensorFlow Lite](https://tensorflow.org/lite) with Python on
a Raspberry Pi to perform real-time object detection using images streamed from
the Pi Camera. It draws a bounding box around each detected object in the camera
preview (when the object score is above a given threshold).

At the end of this page, there are extra steps to accelerate the example using
the Coral USB Accelerator to increase inference speed.

## Set up your hardware

Before you begin, you need to
[set up your Raspberry Pi](https://projects.raspberrypi.org/en/projects/raspberry-pi-setting-up)
with Raspberry Pi OS (preferably updated to Buster).

You also need to
[connect and configure the Pi Camera](https://www.raspberrypi.org/documentation/configuration/camera.md)
if you use the Pi Camera. This code also works with USB camera connect to the
Raspberry Pi.

And to see the results from the camera, you need a monitor connected to the
Raspberry Pi. It's okay if you're using SSH to access the Pi shell (you don't
need to use a keyboard connected to the Pi)—you only need a monitor attached to
the Pi to see the camera stream.

## RUN LOCALLY (From Source)

  - Clone the repository
  - Create virtual environment and activate it

```

git clone https://github.com/edge-services/object-detection.git
cd object-detection

virtualenv venv -p python3.9
source venv/bin/activate

#pip freeze > requirements.txt
pip install -r requirements.txt

sh setup.sh ./app/data

```

## Run the example

```
python detect.py --model efficientdet_lite0.tflite
```

## RUN AS DOCKER CONTAINER (On Raspberry Pi)

```

sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker

docker run --rm -it --name object-detection  \
  --privileged \
  --device /dev/video0 \
  --device /dev/mem   \
  --device /dev/vchiq \
  -v /opt/vc:/opt/vc  \
  -v /tmp:/tmp \
  --env-file .env \
  sinny777/object-detection_arm64:latest


sudo docker run --rm -it --name object-detection  \
  --privileged \
  --device /dev/video0 \
  --device /dev/mem   \
  --device /dev/vchiq \
  -v /opt/vc:/opt/vc  \
  -v /tmp:/tmp \
  --env-file .env \
  3d640b1d083d

```

For more information about executing inferences with TensorFlow Lite, read
[TensorFlow Lite inference](https://www.tensorflow.org/lite/guide/inference).

## Speed up model inference (optional)

If you want to significantly speed up the inference time, you can attach an
[Coral USB Accelerator](https://coral.withgoogle.com/products/accelerator)—a USB
accessory that adds the
[Edge TPU ML accelerator](https://coral.withgoogle.com/docs/edgetpu/faq/) to any
Linux-based system.

If you have a Coral USB Accelerator, you can run the sample with it enabled:

1.  First, be sure you have completed the
    [USB Accelerator setup instructions](https://coral.withgoogle.com/docs/accelerator/get-started/).

2.  Run the object detection script using the EdgeTPU TFLite model and enable
    the EdgeTPU option. Be noted that the EdgeTPU requires a specific TFLite
    model that is different from the one used above.

```
python detect.py --enableEdgeTPU --model efficientdet_lite0_edgetpu.tflite

```

You should see significantly faster inference speeds.

For more information about creating and running TensorFlow Lite models with
Coral devices, read
[TensorFlow models on the Edge TPU](https://coral.withgoogle.com/docs/edgetpu/models-intro/).


## Register Object Detection Service with IBM Edge Application Manager (OpenHorizon)

    - Make sure IEAM Agent is installed on the system that you are using to register edge service (detection) and can access IEAM Hub
    - Clone GIT repo - https://github.com/edge-services/object-detection.git
    - Go inside "horizon" folder
    - Run following commands (CLI for openhorizon)

```

export ARCH=arm64
eval $(hzn util configconv -f hzn.json) 

$hzn exchange service publish -f service.definition.json -P 
<!-- $hzn exchange service list -->
<!-- $hzn exchange service remove ${HZN_ORG_ID}/${SERVICE_NAME}_${SERVICE_VERSION}_${ARCH} -->

$hzn exchange service addpolicy -f service.policy.json ${HZN_ORG_ID}/${SERVICE_NAME}_${SERVICE_VERSION}_${ARCH}
<!-- $hzn exchange service listpolicy ${HZN_ORG_ID}/${SERVICE_NAME}_${SERVICE_VERSION}_${ARCH} -->
<!-- $hzn exchange service removepolicy ${HZN_ORG_ID}/${SERVICE_NAME}_${SERVICE_VERSION}_${ARCH} -->

$hzn exchange deployment addpolicy -f deployment.policy.json ${HZN_ORG_ID}/policy-${SERVICE_NAME}_${SERVICE_VERSION}
<!-- $hzn exchange deployment listpolicy ${HZN_ORG_ID}/policy-${SERVICE_NAME}_${SERVICE_VERSION} -->
<!-- $hzn exchange deployment removepolicy ${HZN_ORG_ID}/policy-${SERVICE_NAME}_${SERVICE_VERSION} -->

```

### Pre-requisites for the Edge Device (Raspberry Pi 4 in this case)

  - [Raspbian 64 bit OS](https://www.makeuseof.com/install-64-bit-version-of-raspberry-pi-os/)
  - Connect a Webcam and make sure following command works
    - raspistill -o test.jpg
  - [Install OpenHorizon Agent (IEAM Agent)](https://github.com/open-horizon/anax/tree/master/agent-install)
    - Below command worked :

```
sudo bash ./agent-install.sh -i . -u $HZN_EXCHANGE_USER_AUTH 

```

  - Export following at Edge Devices or put this at the end of ~/.bashrc (Please change the IP and USER_AUTH)
 
```
export HZN_EXCHANGE_URL=http://169.38.91.92:3090/v1/
export HZN_FSS_CSSURL=http://169.38.91.92:9443/
export CERTIFICATE=agent-install.crt
export HZN_ORG_ID=myorg
export HZN_EXCHANGE_USER_AUTH=admin:HjWsfSKGB9XY3XhLQPOmqpJ6eLWN3U

```

### Commands to test everything's ok

```
curl http://<REPLACE_WITH_HUB_IP>:3090/v1/admin/version
hzn version
hzn exchange service list
hzn agreement list

```

## Register Edge Node with the Hub

  - Create a object-detection.policy.json file with following content

```
{
  "properties": [
    { "name": "hasCamera", "value": true },
    { "name": "object-detection", "value": true },
    { "name": "openhorizon.allowPrivileged", "value": true }    
  ],
  "constraints": [
  ]
}
```
  - Run below command for registering

```
hzn register --policy object-detection.policy.json

```

  - A few useful Horizon commands

```

hzn eventlog list -f
hzn service log -f object-detection

hzn unregister -f

hzn agreement list
hzn node list -v
hzn exchange user list

hzn --help
hzn node --help
hzn exchange pattern --help

```

## Refrences

- [OpenHorizon Agent Install](https://github.com/open-horizon/anax/tree/master/agent-install)
- [RPi4 64 bit OS Install - Advance users](https://qengineering.eu/install-raspberry-64-os.html)

