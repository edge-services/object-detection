# Copyright 2022. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# python classify.py --model ./model/model.tflite --maxResults 3

""" Main script to run image classification. """


import os
import argparse
from nis import cat
import sys
import time
import logging
from logging.handlers import RotatingFileHandler

from detect import Detect
from dotenv import load_dotenv

from utils import CommonUtils
from handlers.cloud_sync import CloudSync
from handlers.producer import Producer
from handlers.consumer import Consumer

logging.basicConfig(
        format='%(asctime)s - %(levelname)s:%(message)s',
        handlers=[
            # RotatingFileHandler('logs.log',maxBytes=1000, backupCount=2),
            logging.StreamHandler(), #print to console
        ],
        level=logging.ERROR
    )

def checkDirectories():
    DATA_DIR = os.environ.get("DATA_DIR")
    MODEL_DIR = os.path.join(DATA_DIR, 'model')
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
    return DATA_DIR, MODEL_DIR

def init():
    load_dotenv()
    # logger.basicConfig(level=LOGLEVEL)
    LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
    utils.cache['CONFIG']['LOGLEVEL'] = LOGLEVEL

    global logger
    # logging.basicConfig(format='%(asctime)s - %(levelname)s:%(message)s', level=utils.cache['CONFIG']['LOGLEVEL'])
    logger = logging.getLogger(__name__)
    logger.setLevel(utils.cache['CONFIG']['LOGLEVEL'])
    
    DATA_DIR, MODEL_DIR = checkDirectories()
    utils.cache['CONFIG']['DATA_DIR'] = DATA_DIR
    utils.cache['CONFIG']['MODEL_DIR'] = MODEL_DIR
    utils.cache['CONFIG']['LOCAL_MODEL_PATH'] = os.path.join(MODEL_DIR, 'model.tflite')

    utils.cache['CONFIG']['CLIENT_ID'] = os.environ.get("CLIENT_ID")
    utils.cache['CONFIG']['CLIENT_SECRET'] = os.environ.get("CLIENT_SECRET")
    utils.cache['CONFIG']['kafka_brokers'] = os.environ.get("kafka_brokers")
    utils.cache['CONFIG']['kafka_username'] = os.environ.get("kafka_username")
    utils.cache['CONFIG']['kafka_password'] = os.environ.get("kafka_password")
    utils.cache['CONFIG']['kafka_certs_path'] = os.environ.get("kafka_certs_path")
    
    global cloudAPI
    global detect
    cloudAPI = CloudSync(utils)  
    
    if utils.is_connected:        
        cloudAPI.syncWithCloud()
        # cloudAPI.syncWithLocal()      
    else:
        logger.info('Load data locally >>>')
        cloudAPI.syncWithLocal()
    
    # classify = Classify(utils)    
    consumer = Consumer(utils)
    if consumer:
        consumer.start()


def run() -> None:
    """Continuously run inference on images acquired from the camera.  """
    try:
        detect = Detect(utils)
        detect.execute()
        while True:
            if utils.cache['UPDATES'] == True:
                logger.info('\n\nNEW UPDATES NEED TO MERGE >>>>>>>>>> \n\n')
                if utils.is_connected:        
                    cloudAPI.syncWithCloud()
                    # cloudAPI.syncWithLocal()      
                else:
                    logger.info('Load data locally >>>')
                    cloudAPI.syncWithLocal()
                utils.cache['UPDATES'] = False
                detect = None
                time.sleep(3)
                detect = Detect(utils) 
                detect.execute()
 
    except KeyboardInterrupt as ki:
         logger.error('KeyboardInterrupt in run detection: >> ', ki)
    except Exception as err:
        logger.error('Exception in run detection: >> ', err)
    finally:
        # consumer.stop()
        logger.info('In Finally of Classify.run().....')


def main():
  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
      '--maxResults',
      help='Max of classification results.',
      required=False,
      default=3)
  parser.add_argument(
      '--numThreads',
      help='Number of CPU threads to run the model.',
      required=False,
      default=4)
  parser.add_argument(
      '--enableEdgeTPU',
      help='Whether to run the model on EdgeTPU.',
      action='store_true',
      required=False,
      default=False)
  parser.add_argument(
      '--cameraId', help='Id of camera.', required=False, default=0)
  parser.add_argument(
      '--frameWidth',
      help='Width of frame to capture from camera.',
      required=False,
      default=640)
  parser.add_argument(
      '--frameHeight',
      help='Height of frame to capture from camera.',
      required=False,
      default=480)
  args = parser.parse_args()

  global CONFIG
  CONFIG = {}
  CONFIG['MAX_RESULTS'] = args.maxResults
  CONFIG['NO_THREADS'] = args.numThreads
  CONFIG['ENABLE_EDGE_TPU'] = args.enableEdgeTPU
  CONFIG['CAMERA_ID'] = args.cameraId
  CONFIG['FRAME_WIDTH'] = args.frameWidth
  CONFIG['FRAME_HEIGHT'] = args.frameHeight
  CONFIG['SCORE_THRESHOLD'] = 0.8
  
  global utils
  utils = CommonUtils()
  utils.cache['CONFIG'] = CONFIG

  init()
  run()

if __name__ == '__main__':
  main()