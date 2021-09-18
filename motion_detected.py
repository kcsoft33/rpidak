#!/usr/bin/python3
import mq
import sys
import os

#motion_detected.py
# script that gets invoked when the motion daemon detects a change in image enough to indicate motion
# input should be a path to a mjpeg video or jpeg snapshot of the last capture
# Take the input and send off MQTT msg with the data payload to let the home automation know of the change
# expected that this should be a fire and forget but may expand in the future to some more processing

#open connection to mqtt broker
#send msg + payload

data = None

if (len(sys.argv) > 1):
    imageFileName = sys.argv[1]
    # with open(imageFileName, "rb") as imageFile: 
    #     imageData = imageFile.read() 
    #     data = bytearray(imageData) 

    mqPub = mq.Client('mqtt_capture.yaml')
    mqPub.publishState(imageFileName,"MOTION")

        # os.remove(imageFileName)