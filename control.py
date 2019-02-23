import os, sys, json
import subprocess, signal
import mq
import datetime

# import ptvsd
# Allow other computers to attach to ptvsd at this IP address and port.
# ptvsd.enable_attach(address=('192.168.0.121', 3000), redirect_output=True)

# Pause the program until a remote debugger is attached
# ptvsd.wait_for_attach()

# control.py
# sets up a mqtt subscriber for control events defined in mqtt.yaml
# hook up handlers for each command supported for the device

class Control(object):
    def __init__(self):
        self._mqClient = self._connectMq()
        self._onpowerq()

    def start(self):
        """ kicks off thread to listen for MQTT events, requires calls to loop() to pump msgs"""
        self._active = True
        self._mqClient.start()

    def loop(self):
        self._mqClient.loop()

    def listen(self):
        self._active = True
        self._mqClient.listen()

    def stop(self):
        self._mqClient.publishState("Offline","STATUS")
        self._mqClient.publishTele("Offline","LWT")
        self._mqClient.disconnect()
        self._active = False

    def active(self):
        return self._active

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
                self._onpowerq()
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
            output = self._poweron()
        else:
            output = self._exec_command(self.TVSERVICE_OFF)
        print(output)
        self._onpowerq(topic, msg)

    def _poweron(self):
        out = self._exec_command(self.TVSERVICE_ON)
        SUDO = "sudo"
        CHVT = "chvt"
        CHVT_SW1 = [SUDO, CHVT, "6"]
        CHVT_SW2 = [SUDO, CHVT, "7"]
        self._exec_command(CHVT_SW1)
        self._exec_command(CHVT_SW2)
        return out

    def _onpowerq(self):
        """ query monitor power state"""
        print('querying display power')
        output = self._exec_command(self.TVSERVICE_STATUS)
        state = "ON"
        if (output.find('[TV is off]') != -1):
            state = "OFF"
        self._mqClient.publishState(state, "POWER")

    def _onmotion(self, topic, msg):
        """ invoke motion state change"""

    def _onmotionq(self, topic, msg):
        """ query monitor service state"""

    def _exec_command(self, data):
        """ exec process """
        print("executing " + ' '.join(data))
        process = subprocess.Popen(data, stdout=subprocess.PIPE)
        line = process.stdout.readline()
        return line

control = Control()
def signal_handler(sig, frame):
    print("Exiting...")
    control.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print( "Listening for events on " + control._mqClient._subTopic)
print( "Press Ctrl+C to exit")
control.listen()

