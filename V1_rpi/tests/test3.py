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
font = cv2.FONT_HERSHEY_SIMPLEX

# capture du flux vidéo
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    now = time.time()
    image = frame.array
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, threshold = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
    ret, contours, _ = cv2.findContours(threshold.copy(), cv2.RETR_LIST  , cv2.CHAIN_APPROX_SIMPLE  )
    for cnt in contours:
        if cv2.arcLength(cnt, True) > 50:
            approx = cv2.approxPolyDP(cnt, 0.01*cv2.arcLength(cnt, True), True)
            cv2.drawContours(image, [approx], 0, (255,0,0), 5)
            x = approx.ravel()[0]
            y = approx.ravel()[1]
            if len(approx) == 3:
                cv2.putText(image, "Triangle", (x, y), font, 0.3, (0))
            elif len(approx) == 4:
                cv2.putText(image, "Rectangle", (x, y), font, 0.3, (0))
            elif len(approx) == 5:
                cv2.putText(image, "Pentagon", (x, y), font, 0.3, (0))
            elif 6 < len(approx) < 15:
                cv2.putText(image, "Ellipse", (x, y), font, 0.3, (0))
            else:
                cv2.putText(image, "Circle", (x, y), font, 0.3, (0))
    cv2.imshow("image", image)
    rawCapture.truncate(0)
    print(time.time()-now)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
