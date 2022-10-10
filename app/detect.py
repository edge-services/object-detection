
import os
from nis import cat
import time
import logging
from dotenv import load_dotenv
import dataclasses

import numpy as np
import cv2
from tflite_support.task import core
from tflite_support.task import processor
from tflite_support.task import vision
from handlers.producer import Producer
from utils import CommonUtils

# Visualization parameters
_MARGIN = 10  # pixels
_ROW_SIZE = 20  # pixels
_LEFT_MARGIN = 24  # pixels
_TEXT_COLOR = (0, 0, 255)  # red
_FONT_SIZE = 1
_FONT_THICKNESS = 1
_FPS_AVERAGE_FRAME_COUNT = 10

@dataclasses.dataclass
class Category(object):
  """A result of a object detection."""
  label: str
  score: float

class Detect(object):

    def __init__(
        self,
        utils: CommonUtils
    ) -> None:
        load_dotenv()
        self.utils = utils
        self.producer = Producer(utils)

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.utils.cache['CONFIG']['LOGLEVEL'])

    def execute(self) -> None:
        """Continuously run inference on images acquired from the camera.  """
        try:
            self.logger.info('\n\nIN Detect RUN method: >>>>>> ')

             # Initialize the object detection model
            base_options = core.BaseOptions(
                file_name=self.utils.cache['CONFIG']['LOCAL_MODEL_PATH'], 
                use_coral=self.utils.cache['CONFIG']['ENABLE_EDGE_TPU'], num_threads=self.utils.cache['CONFIG']['NO_THREADS'])
            detection_options = processor.DetectionOptions(
                max_results=3, score_threshold=0.3)
            options = vision.ObjectDetectorOptions(
                base_options=base_options, detection_options=detection_options)
            detector = vision.ObjectDetector.create_from_options(options)

            labelToDetect = 'Person'
            publishType = 'x-in-y'
            timePeriod = 10
            detectionCount = 20

            rules = self.utils.cache['rules']
            if rules and len(rules) > 0:
                condition = rules[0]['condition']
                # self.logger.info('\n\nCondition: >> %s\n', condition)
                if condition and condition['type'] == 'all':
                    children = condition['children']
                    for child in children:
                        if child['type'] == 'fact':
                            if child['fact']['path'] == '$.class':
                                labelToDetect = child['fact']['value'] 
                            if child['fact']['path'] == '$.confidence' and child['fact']['value'] and (type(child['fact']['value']) == int or float):
                                if child['fact']['value'] > 0:
                                    options.score_threshold = child['fact']['value'] / 100
                                else:
                                    options.score_threshold = child['fact']['value']

                
                event = rules[0]['event']
                # self.logger.info('Event: >> %s\n', event)
                if event and event['params'] and event['params']['publish']:
                    publishType = event['params']['publish']['when']
                    if publishType == 'x-in-y':
                        timePeriod = event['params']['publish']['timePeriod']
                        detectionCount = event['params']['publish']['count']
            
            self.logger.info('LabelToDetect: >> %s', labelToDetect)
            self.logger.info('Threshold: >> %s\n', options.score_threshold)

            # Variables to calculate FPS
            counter, fps, detection_count = 0, 0, 0
            start_time = time.time()
            # self.logger.info('CONFIG: >> ', self.utils.cache['CONFIG'])
            camera = self.getCamera()

            # Continuously capture images from the camera and run inference
            while self.utils.cache['UPDATES'] == False and camera.isOpened():
                success, image = camera.read()
                # time.sleep(0.5)
                if not success:
                    self.logger.info('ERROR: Unable to read from webcam. Please verify your webcam settings.')
                    time.sleep(2)
                    self.getCamera()
                    continue

                counter += 1
                end_time = time.time()
                seconds = end_time - start_time
                fps = _FPS_AVERAGE_FRAME_COUNT / seconds

                image = cv2.flip(image, 1)
                # Convert the image from BGR to RGB as required by the TFLite model.
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                # Create a TensorImage object from the RGB image.
                input_tensor = vision.TensorImage.create_from_array(rgb_image)
                input_tensor._is_from_numpy_array = False

                # Run object detection estimation using the model.
                detection_result = detector.detect(input_tensor)

                # Draw keypoints and edges on input image
                image, categories = self.getResultCategories(image, detection_result)
                # print(categories)
                if len(categories) and categories[0].label == labelToDetect and categories[0].score > options.score_threshold :
                    self.logger.info(categories)
                    # self.logger.info('%s is Detectected %d times in %d seconds: >> %d \n', labelToDetect, detection_count, seconds)
                    category = categories[0]
                    fire_img = image
                    detection_count += 1
                    if publishType == 'every-time' or (publishType == 'x-in-y' and seconds >= timePeriod and detection_count >= detectionCount):
                        self.logger.info('%s is Detectected %d times in %d seconds !!\n', labelToDetect, detection_count, seconds)
                        class_name = category.label
                        score = round(category.score, 2)
                        timestr = time.strftime("%Y%m%d-%H%M%S")
                        serialNumber = self.utils.cache['thisDevice']['deviceSerialNo']
                        result_text = 'Device Serial No: {0}\nDetected: {1} ({2: .2%} confidence ) \nDetection Count: {3}\nSeconds Count: {4: .2f}\nDate & time: {5}'.format(serialNumber, class_name, score, detection_count, seconds, timestr)
                        text_location = (_LEFT_MARGIN, (1) * _ROW_SIZE)
                        cv2.putText(fire_img, result_text, text_location, cv2.FONT_HERSHEY_PLAIN,
                                    _FONT_SIZE, _TEXT_COLOR, _FONT_THICKNESS)

                        frame = serialNumber+'_frame_'+timestr+'.jpg' 
                        cv2.imwrite(os.path.join(self.utils.cache['CONFIG']['DATA_DIR'] + '/frames/' , frame), fire_img)

                        thisDevice = self.utils.cache['thisDevice']

                        event['params']['message'] = event['params']['message'] + '\n\n' +result_text
                        event['params']['metadata'] = {
                                            'deviceId': thisDevice['id'],
                                            'location': thisDevice['location']
                                        }

                        if self.producer:
                            payload = {
                                'topic': 'detection',
                                'event': event
                            }   
                            self.producer.publish('detection', payload)
                        detection_count = 0
                        start_time = time.time()
                    self.logger.info(categories[0])

                # Stop the program if the ESC key is pressed.
                if cv2.waitKey(1) == 27:
                    # consumer.stop()
                    break
                # cv2.imshow('image_classification', image)
            camera.release()
            cv2.destroyAllWindows()
            camera = None
            detect = None
            pass
        # except KeyboardInterrupt as ki:
        #     self.logger.info('KeyboardInterrupt in run detection: >> ', ki)
        # except Exception as err:
        #     self.logger.info('Exception in run detection: >> ', err)
        finally:
            self.logger.info('In Finally of Classify.run().....')
            if camera is not None:
                camera.release()
                cv2.destroyAllWindows()
            
    def getCamera(self):
        # Start capturing video input from the camera
        camera = cv2.VideoCapture(self.utils.cache['CONFIG']['CAMERA_ID'])
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.utils.cache['CONFIG']['FRAME_WIDTH'])
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.utils.cache['CONFIG']['FRAME_HEIGHT'])
        return camera

    def getResultCategories(self, image: np.ndarray, detection_result: processor.DetectionResult):
        categories: Category = []
        for detection in detection_result.detections:
            # Draw bounding_box
            bbox = detection.bounding_box
            start_point = bbox.origin_x, bbox.origin_y
            end_point = bbox.origin_x + bbox.width, bbox.origin_y + bbox.height
            cv2.rectangle(image, start_point, end_point, _TEXT_COLOR, 3)

            # Draw label and score
            category = detection.categories[0]
            category_name = category.category_name
            probability = round(category.score, 2)
            result_text = category_name + ' (' + str(probability) + ')'
            categories.append(Category(label=category_name, score=probability))
            # print(result_text)
            text_location = (_MARGIN + bbox.origin_x,
                            _MARGIN + _ROW_SIZE + bbox.origin_y)
            cv2.putText(image, result_text, text_location, cv2.FONT_HERSHEY_PLAIN,
                        _FONT_SIZE, _TEXT_COLOR, _FONT_THICKNESS)

       
        return image, categories

   