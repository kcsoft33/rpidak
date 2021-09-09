import os, sys, json
import subprocess, signal
import mq
import datetime

# control.py
# sets up a mqtt subscriber for control events defined in mqtt.yaml
# hook up handlers for each command supported for the device

class Control(object):
    _uriPushed = []
    _tabIdx = 0
    _lastUri = ''
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
        cmdmap = {
            "POWER": self._onpower, 
            "MOTION": self._onmotion, 
            "KIOSK": self._onkiosk}
        cmdtopic = topic.split('/')[-1]
        if cmdtopic in cmdmap:
            cmdmap[cmdtopic](topic,msg)

    def _onkioskq(self):
        self._mqClient.publishState(self._lastUri, "KIOSK")

    def _onkiosk(self, topic, msg):
        if msg is None or msg == "":
            self._onkioskq()
            return
        elif msg == "tab://":
            #send keys ctrl+tab
            self._runctrltab()
            #calc _lastUri from tabIdx % len(_uriPushed)
            #NOTE: assumes sequential tab order after all Uri's are issued
            lenPublished = len(self._uriPushed)
            if lenPublished > 0:
                self._lastUri = self._uriPushed[self._tabIdx % lenPublished]
                self._tabIdx += 1
                print("{}:{}".format(msg, self._lastUri))
        elif msg.startswith('http://') or msg.startswith('https://'):
            self._uriPushed.append(msg)
            self._lastUri = msg
            BROWSER_CMD = self.BROWSER.copy()
            BROWSER_CMD.append(msg)
            print("launching {}".format(msg))
            subprocess.Popen(BROWSER_CMD)
        elif msg == 'OFF' or msg == 'off':
            self._exec_command(["pkill", "chromium"])
            self._uriPushed.clear()
            self._lastUri = 'OFF'
            self._tabIdx = 0
        elif msg.lower() == 'reload':
            self._runreload()
        self._onkioskq()

    TVSERVICE_EXE = "tvservice"
    TVSERVICE_STATUS = [TVSERVICE_EXE, "-s"]
    TVSERVICE_ON  = [TVSERVICE_EXE, "-p"]
    TVSERVICE_OFF  = [TVSERVICE_EXE,  "-o"]

    def _onpower(self, topic, msg):
        """ invoke monitor power state"""
        if (msg is None or msg == ""):
            self._onpowerq()
            return
        elif msg == "ON":
            output = self._poweron()
        elif msg == "OFF":
            output = self._exec_command(self.TVSERVICE_OFF)
        elif msg == "RESTART":
            # pub off before rebooting since we probably won't have a clean shutdown
            self._mqClient.publishState("OFF", "POWER")
            self._exec_command(['sudo','reboot'])
        print(output)
        self._onpowerq()

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
        if output.find("[TV is off]") != -1:
            state = "OFF"
        self._mqClient.publishState(state, "POWER")

    def _onmotion(self, topic, msg):
        """ invoke motion state change"""
        if (msg is None or msg == ""):
            self._onmotionq(topic, msg)
        # else:

    def _onmotionq(self, topic, msg):
        """ query motion service state"""

    DISPLAY_0 = "DISPLAY=:0" #needed for when running as a service?
    CHROMIUM = "chromium-browser"
    BROWSER = [CHROMIUM, "--disable-session-crashed-bubble", "--noerrdialogs", "--kiosk"]
    XDOTOOL = "xdotool"
    KEY_DOWN = "keydown"
    KEY_UP = "keyup"
    CTRL_TAB = "ctrl+Tab"
    CTRL_R = "ctrl+r"
    CTRL_TAB_BEGIN_CMD = [XDOTOOL, KEY_DOWN, CTRL_TAB]
    CTRL_TAB_END_CMD = [XDOTOOL, KEY_UP, CTRL_TAB]
    CTRL_RELOAD_BEGIN_CMD = [XDOTOOL, KEY_DOWN, CTRL_R]
    CTRL_RELOAD_END_CMD = [XDOTOOL, KEY_UP, CTRL_R]

    def _runctrltab(self):
        self._exec_command(self.CTRL_TAB_BEGIN_CMD)
        self._exec_command(self.CTRL_TAB_END_CMD)

    def _runreload(self):
        self._exec_command(self.CTRL_RELOAD_BEGIN_CMD)
        self._exec_command(self.CTRL_RELOAD_END_CMD)


    def _exec_command(self, data):
        """ exec process """
        print("executing " + ' '.join(data))
        process = subprocess.Popen(data, stdout=subprocess.PIPE)
        line = process.stdout.readline()
        return line.decode('utf-8')

control = Control()
def signal_handler(sig, frame):
    print("Exiting...")
    control.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print( "Listening for events on " + control._mqClient._subTopic)
print( "Press Ctrl+C to exit")
control.listen()

