import os, sys, json
import subprocess, signal
import mq
import datetime
# control.py
# sets up a mqtt subscriber for control events defined in mqtt.yaml
# hook up handlers for each command supported for the device

class Control(object):
    def __init__(self):
        self._mqClient = self._connectMq()

    def listen(self):
        self._mqClient.listen()

    def stop(self):
        self._mqClient.publishState("Offline","STATUS")
        self._mqClient.publishTele("Offline","LWT")
        self._mqClient.disconnect()

    def _connectMq(self):
        mqc = mq.Client()
        mqc.oncmnd = self._oncmnd
        mqc.subscribe()
        mqc.publishTele("Online", "LWT")
        mqc.publishState("Online", "STATUS")
        return mqc

    def _oncmnd(self, topic, msg):
        """ invoke monitor power state"""
        if (topic.endswith("/POWER")):
            if (msg is None or msg == ""):
                self._onpowerq(topic, msg)
            else:
                self._onpower(topic, msg)
        elif(topic.endswith("/MOTION")):
            if (msg is None or msg == ""):
                self._onmotionq(topic, msg)
            else:
                self._onmotion(topic, msg)

    TVSERVICE_EXE = "tvservice"
    TVSERVICE_STATUS = [TVSERVICE_EXE, "-s"]
    TVSERVICE_ON  = [TVSERVICE_EXE, "-p"]
    TVSERVICE_OFF  = [TVSERVICE_EXE,  "-o"]

    def _onpower(self, topic, msg):
        """ invoke monitor power state"""
        if (msg == "ON"):
            output = self._exec_command(TVSERVICE_ON)
        else:
            output = self._exec_command(TVSERVICE_OFF)
        
        self._onpowerq(topic, msg)

    def _onpowerq(self, topic, msg):
        """ query monitor power state"""
        output = self._exec_command(TVSERVICE_STATUS)
        state = "ON"
        if (output == "TV is off"):
            state = "OFF"
        
        self._mqClient.publishState(state, "POWER")

    
    def _onmotion(self, topic, msg):
        """ invoke motion state change"""
    
    def _onmotionq(self, topic, msg):
        """ query monitor service state"""

    def _exec_command(self, data):
        process = subprocess.Popen(data, stdout=subprocess.PIPE)
        try:
            while process.poll() is None: #still running
                line = char = ""
                while char != "\n":
                    line += char
                    char = process.stdout.read(1)
                
                return line
        finally:
            process.stdout.close()
            process.kill()

control = Control()
def signal_handler(sig, frame):
    print("Exiting...")
    control.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print( "Listening for events on " + control._mqClient._subTopic)
print( "Press Ctrl+C to exit")
control.listen()




    