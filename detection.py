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
import datetime
import cv2
import json
from pyzbar import pyzbar
import imutils
import RPi.GPIO as GPIO
import argparse
from FUTIL.my_logging import *
import concurrent.futures

class App():
    X = 0
    Y = 1
    NORMAL = 1
    REVERSE = -1

class Detector():
    '''Un détecteur de QRCode
    '''

    def __init__(self,
                    outputs_pins = [17, 24], #Led_rouge et relais
                    detection_pins = [17],
                    wait_pins = [22],
                    output_duration = 1,
                    resolution = (640, 480),
                    distance_camera_papier = 330.0, # mm
                    distance_camera_coupe = 600.0, # mm
                    vitesse_avance = 50.0, # mm/s
                    orientation = App.X,
                    direction = App.NORMAL,
                    framerate = 32,
                    cb_type = 'QRCODE',
                    cb_text = None,
                    args = None,
                    ):
        '''Création du détecteur
            args                {"show" : True|False, "debug" : True|False, "testmode" : True|False}
        '''
        self.resolution = resolution
        self.framerate = framerate
        self.outputs_pins = outputs_pins
        self.wait_pins = wait_pins
        self.detection_pins = detection_pins
        self.output_duration = output_duration
        if args and 'show' in args:
            self.show = args.show
        else:
            self.show = False
        if args and 'debug' in args:
            self.debug = args.debug
        else:
            self.debug = False
        if args and 'testmode' in args:
            self.testmode = args.testmode
        else:
            self.testmode = False
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(outputs_pins + wait_pins, GPIO.OUT)
        GPIO.output(outputs_pins, GPIO.LOW)
        GPIO.output(wait_pins, GPIO.HIGH)
        self.camera = None
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers = 3) #Pour threading
        distance_camera_papier = float(distance_camera_papier)
        self.real_size =  (distance_camera_papier*340.0/330.0, distance_camera_papier*260.0/330.0,)
        self.distance_camera_coupe = float(distance_camera_coupe)
        self.vitesse_avance = float(vitesse_avance)
        self.orientation = orientation
        self.direction = direction
        self.duree_debounce = self.real_size[self.orientation] / self.vitesse_avance
        logging.info("Taille réelle (sens avance): %smm\nDurée debounce : %ss"%(self.real_size[self.orientation],self.duree_debounce))
        if self.orientation == App.X:
            if self.direction == App.NORMAL:
                self.arrow = (
                        (int(self.resolution[0] / 3) ,int(self.resolution[1] / 3)), \
                        (int( 2 * self.resolution[0] / 3), int(self.resolution[1] / 3)), \
                        (0,0,255),5 )
            else:
                self.arrow = (
                        (int( 2 * self.resolution[0] / 3), int(self.resolution[1] / 3)), \
                        (int(self.resolution[0] / 3) ,int(self.resolution[1] / 3)), \
                        (0,0,255),5 )
        else:
            if self.direction == App.NORMAL:
                self.arrow = (
                        (int(self.resolution[0] / 3) ,int(self.resolution[1] / 3)), \
                        (int(self.resolution[0] / 3), 2*int(self.resolution[1] / 3)), \
                        (0,0,255),5 )
            else:
                self.arrow = (
                        (int(self.resolution[0] / 3), int(2 * self.resolution[1] / 3)), \
                        (int(self.resolution[0] / 3) ,int(self.resolution[1] / 3)), \
                        (0,0,255),5 )
        logging.debug("Arrow : %s"%(list(self.arrow)))
        self.cb_type = cb_type
        if cb_text is None:
            self.cb_text = None
        else:
            if type(cb_text) != bytes:
                self.cb_text = cb_text
            else:
                self.cb_text = cb_text.encode('utf-8')


    def on_detect(self, rect):
        if not self.testmode :
            GPIO.output(self.detection_pins, GPIO.HIGH)
            (x, y, w, h) = rect
            position_px = rect[self.orientation] + rect[2 + self.orientation] / 2
            logging.debug("position_px : %s"%position_px)
            now = datetime.datetime.now()
            #logging.info("QRCODE DETECTE %s: x:%d%%, y:%d%%"%(now,(x+w/2)*100/self.resolution[0]-50,(y+h/2)*100/self.resolution[1]-50))
            distance_qrcode_centre = (position_px * self.real_size[self.orientation] / self.resolution[self.orientation]  - self.real_size[self.orientation] / 2.0) * self.direction
            distance_qrcode_coupe = self.distance_camera_coupe - distance_qrcode_centre
            logging.info("QRCODE DETECTE à %smm de la camera => %smm de la coupe"%(int(distance_qrcode_centre), int(distance_qrcode_coupe)))
            tempo = max(0,distance_qrcode_coupe/self.vitesse_avance)
            logging.info("Temporisation de %f secondes"%tempo)
            time.sleep(0.25)
            GPIO.output(self.detection_pins, GPIO.LOW)
            time.sleep(tempo-0.25)
            GPIO.output(self.outputs_pins, GPIO.HIGH)
            time.sleep(self.output_duration)
            GPIO.output(self.outputs_pins, GPIO.LOW)



    def start_camera(self):
        '''Start the camera
        '''
        logging.info("Start Camera...")
        GPIO.output(self.wait_pins, GPIO.HIGH)
        try:
            self.camera = PiCamera()
            self.camera.resolution = self.resolution
            self.camera.framerate = self.framerate
            self.rawCapture = PiRGBArray(self.camera, size=self.resolution)
        # temps reserve pour l'autofocus
            time.sleep(0.1)
            logging.info("Camera prête. Detection start.")
            self.camera_active = True
        except Exception as e:
            logging.error("Error initialising camera : %s"%e)
            self.camera_active = False
            GPIO.output(self.wait_pins, GPIO.LOW)
            time.sleep(1)

    def close_camera(self, cause = ""):
        '''Stop the camera
        '''
        logging.info("Stop Camera %s."%cause)
        try:
            self.camera.close()
            self.camera_active = False
            GPIO.output(self.wait_pins, GPIO.LOW)
        except:
            time.sleep(1)

    def run(self):
        '''The main programm
        '''
        self.start_camera()
        now = time.time()
        scan_json_file_counter = 0
        time_to_debounce = 0
        # capture du flux video
        while True:
            try:
                for frame in self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True):
                    image = frame.array
                    #image = image[int(self.resolution[1]/2):,0:int(self.resolution[0]*4/5)]
                    grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    if time.time() > time_to_debounce:
                        GPIO.output(self.wait_pins, GPIO.HIGH)
                        if self.cb_type == 'QRCODE':
                            barcodes = pyzbar.decode(grey, [pyzbar.ZBarSymbol.QRCODE])
                        else:
                            barcodes = pyzbar.decode(grey)
                        if len(barcodes)>0 and (self.cb_type is None or barcodes[0].type == self.cb_type) and ( self.cb_text is None or barcodes[0].data == self.cb_text):
                            logging.debug("barcode detected : %s"%barcodes)
                            self.executor.submit(self.on_detect, barcodes[0].rect)
                            time_to_debounce = time.time() + self.duree_debounce
                    else:
                        GPIO.output(self.wait_pins, GPIO.LOW)
                        #barcodes = []
                    if self.show:
                        cv2.arrowedLine(image,*self.arrow)
                        for barcode in barcodes:
                        	(x, y, w, h) = barcode.rect
                        	cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        	barcodeData = barcode.data.decode("utf-8")
                        	barcodeType = barcode.type
                        cv2.imshow("image", image)
                        cv2.waitKey(1)
                    self.rawCapture.truncate(0)
                    logging.debug(time.time()-now)
                    now = time.time()
                    time.sleep(0.01)
            except PiCameraClosed as e:
                logging.error("Erreur : %s"%e)
                self.start_camera()
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
