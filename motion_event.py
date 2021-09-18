#!/usr/bin/python3
import mq
import sys

# motion_event.py
# script that gets invoked when the motion daemon detects a change in image enough to indicate motion
if (len(sys.argv) > 1):
    motionEvent = sys.argv[1]

    mqPub = mq.Client('mqtt_motion.yaml')
    mqPub.publishState(motionEvent)
