
import os
import json
import socket
import requests
import logging

class Singleton(object):
        def __new__(cls, *args, **kwds):
            it = cls.__dict__.get("__it__")
            if it is not None:
                return it
            cls.__it__ = it = object.__new__(cls)
            it.init(*args, **kwds)
            return it
        def init(self, *args, **kwds):
            pass


class CommonUtils(Singleton):

    def __init__(self) -> None:
        """ Initialize CommonUtils """
        self.cache = {
            'UPDATES': False,
            'CONFIG': {}
        }
    
    def getserial(self):
        cpuserial = "0000000000000000"
        try:
            f = open('/proc/cpuinfo','r')
            for line in f:
                if line[0:6]=='Serial':
                    cpuserial = line[10:26]
            f.close()
        except Exception as err:
            # cpuserial = "darwin"
            # logging.error('Exception in getSeril: >> ', err)
            cpuserial = "10000000f0d61812" 
        
        return cpuserial

    def is_connected(self):
        try:
            sock = socket.create_connection(("www.google.com", 80))
            if sock is not None:
                sock.close
                # TODO: For testing offline feature
                return True 
        except OSError:
            pass
        return False

    def downloadFile(self, file_url, path_to_save):
        file_url = 'https://tfhub.dev/tensorflow/lite-model/efficientdet/lite0/detection/metadata/1?lite-format=tflite'
        response = requests.get(file_url)
        open(path_to_save, "wb").write(response.content)

    def setInCache(self, key, value):
        self.cache[key] = value

    def getFromCache(self, key):
        return self.cache[key]



