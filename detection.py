#!/usr/bin/env python
# -*- coding:utf-8 -*
'''
Programme de détection de QRCODE
pour piloter la cisaille de coupe de la machine d'imprégnation décors OLFA

Usage : python3 detection.py --options
        avec options:
            -s  Affiche la video
            -d  Mode debug : affiche le temps entre chaque mesures
            -t  Mode test : pas d'action sur les GPIO : juste logging

En mode service :
    sudo systemctl enable path_complet/detection.service
'''

# importer les paquets requis pour la Picamera
from picamera.array import PiRGBArray
from picamera.array import PiArrayOutput
from picamera import PiCamera
from picamera import PiCameraClosed

import sys
import time
import cv2
import json
from pyzbar import pyzbar
import imutils
import RPi.GPIO as GPIO
import argparse
from FUTIL.my_logging import *

class Detector():
    '''Un détecteur de QRCode
    '''

    def __init__(self,
                    outputs_pins = [22, 24], #Led_rouge et relais
                    wait_pins = [24],
                    tmp_dir = '/ramdisk/',
                    detection_json = 'detection_json',
                    image_file = 'capture.jpg',
                    resolution = (320,240),
                    framerate = 10,
                    scan_json_file_period = 10,
                    args = None):
        '''Création du détecteur
            tmp_dir            repertoir où vont être stockés les fichiers temporaires
            detection_json      nom du fichier json
            image_file          nom du fichier image
            args                {"show" : True|False, "debug" : True|False, "testmode" : True|False}
        '''
        self.detection_json = tmp_dir + detection_json
        self.image_file = tmp_dir + image_file
        self.resolution = resolution
        self.framerate = framerate
        self.scan_json_file_period = scan_json_file_period
        self.outputs_pins = outputs_pins
        self.wait_pins = wait_pins
        try:
            self.show = args["show"]
        except:
            self.show = False
        try:
            self.debug = args["debug"]
        except:
            self.debug = False
        try:
            self.testmode = args["testmode"]
        except:
            self.testmode = False
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(outputs_pins + wait_pins, GPIO.OUT)
        GPIO.output(outputs_pins, GPIO.LOW)
        GPIO.output(wait_pins, GPIO.HIGH)
#        font = cv2.FONT_HERSHEY_SIMPLEX
        self.camera = None

    def on_detect(self, rect):
        if not self.testmode :
            (x, y, w, h) = rect
            logging.info("QRCODE DETECTE : x:%d%%, y:%d%%"%((x+w/2)*100/self.resolution[0]-50,(y+h/2)*100/self.resolution[1]-50))
            GPIO.output(self.outputs_pins, GPIO.HIGH)
            GPIO.output(self.wait_pins, GPIO.LOW)
            time.sleep(1)
            GPIO.output(self.outputs_pins, GPIO.LOW)
            time.sleep(5)
            GPIO.output(self.wait_pins, GPIO.HIGH)


    def read_file(self):
        try:
            with open(self.detection_json, 'r') as jsonfile:
                datas = json.load(jsonfile)
        except IOError:
            datas = {"active" : True, "visualisation" : False}
        return datas

    def start_camera(self):
        '''Start the camera
        '''
        logging.info("Start Camera...")
        self.camera = PiCamera()
        self.camera.resolution = self.resolution
        self.camera.framerate = self.framerate
        self.rawCapture = PiRGBArray(self.camera)#, size=(160, 120)
        # temps reserve pour l'autofocus
        time.sleep(0.1)
        logging.info("Camera prête. Detection start.")
        self.camera_active = True

    def close_camera(self, cause = ""):
        '''Stop the camera
        '''
        logging.info("Stop Camera %s."%cause)
        self.camera.close()
        self.camera_active = False

    def run(self):
        '''The main programm
        '''
        self.start_camera()
        now = time.time()
        scan_json_file_counter = 0
        # capture du flux video
        while True:
            try:
                for frame in self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True):
                    image = frame.array
                    barcodes = pyzbar.decode(image)
                    if len(barcodes)>0:
                        self.on_detect(barcodes[0].rect)
                    if self.show:
                        for barcode in barcodes:
                        	(x, y, w, h) = barcode.rect
                        	cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
                        	barcodeData = barcode.data.decode("utf-8")
                        	barcodeType = barcode.type
                        cv2.imshow("image", image)
                    self.rawCapture.truncate(0)
                    logging.debug(time.time()-now)
                    now = time.time()
                    scan_json_file_counter +=1
                    if scan_json_file_counter>self.scan_json_file_period:
                        scan_json_file_counter = 0
                        datas = self.read_file()
                        if self.camera_active and not datas["active"]:
                            self.close_camera("by json file")
                        if self.camera_active and datas["visualisation"]:
                            logging.debug("image captured.")
                            cv2.imwrite(self.image_file,image)
                    time.sleep(0.01)
            except PiCameraClosed as e:
                datas = self.read_file()
                if datas["active"]:
                    logging.info("Camera open by json file.")
                    self.start_camera()
                else:
                    time.sleep(1)
            except Exception as e:
                logging.warning("Erreur : %s"%e)
                self.close_camera()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s","--show", help="Show video (Need GUI)", action="store_true")
    parser.add_argument("-d","--debug", help="Debug mode", action="store_true")
    parser.add_argument("-t","--testmode", help="Mode test (pas d'activation du relais)", action="store_true")
    args = parser.parse_args()
    if args.debug:
        my_logging(console_level = DEBUG, logfile_level = INFO, details = False)
    else:
        my_logging(console_level = INFO, logfile_level = INFO, details = False)
    detector = Detector(args = args)
    detector.run()
