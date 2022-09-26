
import os
import json
import logging
from dotenv import load_dotenv
import ibm_boto3
from ibm_botocore.client import Config, ClientError
from utils import CommonUtils

class COS(object):

    def __init__(
        self,
        utils: CommonUtils
    ) -> None:
        load_dotenv()
        self.utils = utils
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.utils.cache['CONFIG']['LOGLEVEL'])
     
        # Constants for IBM COS values
        COS_ENDPOINT = self.utils.cache['CONFIG']['COS_ENDPOINT'] # Current list avaiable at https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints
        COS_API_KEY_ID = self.utils.cache['CONFIG']['COS_API_KEY'] # eg "W00YixxxxxxxxxxMB-odB-2ySfTrFBIQQWanc--P3byk"
        COS_INSTANCE_CRN =self.utils.cache['CONFIG']['COS_INSTANCE_ID'] # eg "crn:v1:bluemix:public:cloud-object-storage:global:a/3bf0d9003xxxxxxxxxx1c3e97696b71c:d6f04d83-6c4f-4a62-a165-696756d63903::"

        try:
            # Create client 
            self.cos = ibm_boto3.client("s3",
                ibm_api_key_id=COS_API_KEY_ID,
                ibm_service_instance_id=COS_INSTANCE_CRN,
                config=Config(signature_version="oauth"),
                endpoint_url=COS_ENDPOINT
            )
        except Exception as err:
            self.logger.error("Error in Initializing Producer: >> ", err)
    
    def publish(self, topic, payload):
        try:
            jd = json.dumps(payload).encode('utf-8')
            self.producer.send(topic, jd)
            self.producer.flush()
        except Exception as err:
            self.logger.info("Error in publishing: >> ", err)

