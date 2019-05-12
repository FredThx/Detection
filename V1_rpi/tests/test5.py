
# import the necessary packages
from imutils.video import VideoStream
from pyzbar import pyzbar
import argparse
import datetime
import imutils
import time
import cv2
import time

# initialize the video stream and allow the camera sensor to warm up
print("[INFO] starting video stream...")
# vs = VideoStream(src=0).start()
vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)
print("Camera initialisée.")
# open the output CSV file for writing and initialize the set of
# barcodes found thus far

found = set()

# loop over the frames from the video stream
while True:
    now = time.time()
	# grab the frame from the threaded video stream and resize it to
	# have a maximum width of 400 pixels
    frame = vs.read()
    print("frame readed.")
    #frame = imutils.resize(frame, width=400)
    #print("frame resized.")
	# find the barcodes in the frame and decode each of the barcodes
    barcodes = pyzbar.decode(frame)
    print("Barecodes found : %s"%len(barcodes))
	# loop over the detected barcodes
    for barcode in barcodes:
        # extract the bounding box location of the barcode and draw
        # the bounding box surrounding the barcode on the image
        (x, y, w, h) = barcode.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

        # the barcode data is a bytes object so if we want to draw it
        # on our output image we need to convert it to a string first
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type

        # draw the barcode data and barcode type on the image
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(frame, text, (x, y - 10),
        	cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

	# show the output frame
    cv2.imshow("Barcode Scanner", frame)
    key = cv2.waitKey(1) & 0xFF
    print(time.time()-now)
	# if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break

# close the output CSV file do a bit of cleanup
print("[INFO] cleaning up...")
csv.close()
cv2.destroyAllWindows()
vs.stop()
