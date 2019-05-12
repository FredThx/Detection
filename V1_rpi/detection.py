# test de la caméra picamera.py
# importer les paquets requis pour la Picaméra
from picamera.array import PiRGBArray
from picamera.array import PiArrayOutput
from picamera import PiCamera
import time
import cv2
from pyzbar import pyzbar
import imutils
import RPi.GPIO as GPIO

show = False
real = True

resolution = (320, 240) # Résolution de la camera

# Initialisation led, buzzer et relais
led=17
buzz = 25
relais = 24
ouputs_pins = [led, buzz,relais]
GPIO.setmode(GPIO.BCM)
GPIO.setup(ouputs_pins, GPIO.OUT)
GPIO.output(ouputs_pins, GPIO.LOW)
def on_detect(rect):
    (x, y, w, h) = rect
    print("QRCODE DETECTE : x:%d%%, y:%d%%"%((x+w/2)*100/resolution[0]-50,(y+h/2)*100/resolution[1]-50))
    GPIO.output(ouputs_pins, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(ouputs_pins, GPIO.LOW)
    time.sleep(5)


# initialisation des paramètres pour la capture
camera = PiCamera()
camera.resolution = resolution
camera.framerate = 32
rawCapture = PiRGBArray(camera)#, size=(160, 120)
# temps réservé pour l'autofocus
time.sleep(0.1)
font = cv2.FONT_HERSHEY_SIMPLEX

# capture du flux vidéo
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    now = time.time()
    image = frame.array
    #image = imutils.resize(image, width=400)
    barcodes = pyzbar.decode(image)
    if real and len(barcodes)>0:
        on_detect(barcodes[0].rect)
    if show:
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
        	print("[INFO] Found {} barcode: {}".format(barcodeType, barcodeData))
        cv2.imshow("image", image)
    rawCapture.truncate(0)
    print(time.time()-now)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
