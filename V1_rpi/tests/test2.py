# test de la caméra picamera.py
# importer les paquets requis pour la Picaméra
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2

# initialisation des paramètres pour la capture
camera = PiCamera()
camera.resolution = (800, 600)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(800, 600))

# temps réservé pour l'autofocus
time.sleep(0.1)

# capture du flux vidéo
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    now = time.time()
    image = frame.array
    cv2.imshow("Image", image)
    rawCapture.truncate(0)
    print(time.time()-now)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
