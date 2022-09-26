

import os
import json
import logging
from dotenv import load_dotenv
from kafka import KafkaConsumer
import threading
from utils import CommonUtils

class Consumer(threading.Thread):

    def __init__(self, utils: CommonUtils):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()
        load_dotenv()
        self.utils = utils
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.utils.cache['CONFIG']['LOGLEVEL'])
        
        sasl_mechanism = "PLAIN"
        security_protocol = "SASL_SSL"
        KAFKA_BROKERS= self.utils.cache['CONFIG']['kafka_brokers']        
        kafka_username = self.utils.cache['CONFIG']['kafka_username']
        kafka_password = self.utils.cache['CONFIG']['kafka_password']        

        try:
            self.consumer = KafkaConsumer(bootstrap_servers=KAFKA_BROKERS,
                                security_protocol=security_protocol,
                                ssl_check_hostname=True,
                                ssl_cafile=self.utils.cache['CONFIG']['kafka_certs_path'],
                                sasl_mechanism = sasl_mechanism,
                                sasl_plain_username = kafka_username,
                                sasl_plain_password = kafka_password,
                                group_id=self.utils.cache['thisDevice']['metadata']['entityCategoryId'],
                                auto_offset_reset='latest', enable_auto_commit=False,
                                #   auto_commit_interval_ms=1000,
                                value_deserializer=lambda m: json.loads(m.decode('utf-8')))
        except Exception as err:
            self.logger.error("Error in Initializing Consumer: >> ", err)

    def stop(self):
        self.stop_event.set()
        self.consumer.close()
        self.logger.info('Consumer Closed....')

    def run(self):
        topics = ['updates']
        try:
            if self.consumer:
                self.consumer.subscribe(topics)
                while not self.stop_event.is_set():
                    for message in self.consumer:
                        self.logger.info ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                                                        message.offset, message.key,
                                                        message.value))
                        self.consumer.commit()
                        self.utils.cache['UPDATES'] = True
                        if self.stop_event.is_set():
                            logging.debug('Consumer Stopped >>>>> ')
                            break
        finally:
            if self.consumer:
                self.consumer.close()
            self.logger.info('Consumer Ended....')

