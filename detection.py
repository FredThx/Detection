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

tmp_dir = '/ramdisk/'
detection_json = 'detection.json'
image_file = 'capture.jpg'

parser = argparse.ArgumentParser()
parser.add_argument("-s","--show", help="Show video (Need GUI)", action="store_true")
parser.add_argument("-d","--debug", help="Debug mode", action="store_true")
parser.add_argument("-t","--testmode", help="Mode test (pas d'activation du relais)", action="store_true")
args = parser.parse_args()
if args.show:
    print("Mode video")
if args.testmode:
    print("Mode test")
if args.debug:
    my_logging(console_level = DEBUG, logfile_level = INFO, details = False)
else:
    my_logging(console_level = INFO, logfile_level = INFO, details = False)


resolution = (320, 240) # Resolution de la camera
scan_json_file_period = 10

# Initialisation leds et relais
led_rouge = 22
led_jaune = 17
relais = 24
outputs_pins = [led_rouge,relais]
wait_pins = [led_jaune]
GPIO.setmode(GPIO.BCM)
GPIO.setup(outputs_pins + wait_pins, GPIO.OUT)
GPIO.output(outputs_pins, GPIO.LOW)
GPIO.output(wait_pins, GPIO.HIGH)
font = cv2.FONT_HERSHEY_SIMPLEX

def on_detect(rect):
    (x, y, w, h) = rect
    logging.info("QRCODE DETECTE : x:%d%%, y:%d%%"%((x+w/2)*100/resolution[0]-50,(y+h/2)*100/resolution[1]-50))
    GPIO.output(outputs_pins, GPIO.HIGH)
    GPIO.output(wait_pins, GPIO.LOW)
    time.sleep(1)
    GPIO.output(outputs_pins, GPIO.LOW)
    time.sleep(5)
    GPIO.output(wait_pins, GPIO.HIGH)


def read_file():
    try:
        with open(tmp_dir+detection_json, 'r') as jsonfile:
            datas = json.load(jsonfile)
    except IOError:
        datas = {"active" : True, "visualisation" : False}
    return datas


# initialisation des parametres pour la capture
logging.info("Start Camera...")
camera = PiCamera()
camera.resolution = resolution
camera.framerate = 10   # Si 30 : plante le Rpi0!
                        # Si 20 : plus lent !
rawCapture = PiRGBArray(camera)#, size=(160, 120)
# temps reserve pour l'autofocus
time.sleep(0.1)
logging.info("Camera prête. Detection start.")
now = time.time()
scan_json_file_counter = 0
camera_active = True

# capture du flux video
while True:
    try:
        for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
            image = frame.array
            #image = imutils.resize(image, width=400)
            barcodes = pyzbar.decode(image)
            if not args.testmode and len(barcodes)>0:
                on_detect(barcodes[0].rect)
            if args.show:
                for barcode in barcodes:

                	# extract the bounding box location of the barcode and draw the
                	# bounding box surrounding the barcode on the image
                	(x, y, w, h) = barcode.rect
                	cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)

                	# the barcode data is a bytes object so if we want to draw it on
                	# our output image we need to convert it to a string first
                	barcodeData = barcode.data.decode("utf-8")
                	barcodeType = barcode.type

                	# draw the barcode data and barcode type on the image
                	text = "{} ({})".format(barcodeData, barcodeType)
                	cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                		0.5, (0, 0, 255), 2)

                	# print the barcode type and data to the terminal
                	logging.info("[INFO] Found {} barcode: {}".format(barcodeType, barcodeData))
                cv2.imshow("image", image)
            rawCapture.truncate(0)
            logging.debug(time.time()-now)
            now = time.time()
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                sys.exit(0)
            scan_json_file_counter +=1
            if scan_json_file_counter>scan_json_file_period:
                scan_json_file_counter = 0
                datas = read_file()
                if camera_active and not datas["active"]:
                    camera_active = False
                    camera.close()
                    logging.info("Camera close by json file.")
                if camera_active and datas["visualisation"]:
                    logging.debug("image captured.")
                    cv2.imwrite(tmp_dir+image_file,image)

    except PiCameraClosed as e:
        datas = read_file()
        if datas["active"]:
            camera = PiCamera()
            logging.info("Camera open by json file.")
            camera.resolution = resolution
            camera.framerate = 32
            rawCapture = PiRGBArray(camera)
            time.sleep(0.1)
            camera_active = True
        else:
            time.sleep(1)
    except Exception as e:
        logging.warning("Erreur : %s"%e)
        camera.close()
        camera_active = False
