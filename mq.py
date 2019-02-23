import os, sys
import paho.mqtt.client as mqtt
import yaml

class Client(object):
    """MQTT Wrapper client class.

    This is the main class for simple pub / sub with MQTT broker defined in mqtt.yaml

    General usage flow:
    mqCl = Client()
    mqCl.publishState("Online")
    mqCl.oncmnd_power = onpower
    mqCl.oncmnd_powerquery = onpowerq
    mqCl.listen()
"""
    def publishState(self, msg, suffix = ""):
        """ Publish the configured state topic with supplied message"""
        self._ensureClient()

        # generate state topic based off config
        topic = self._formatTopic("state_prefix", suffix)
        self._client.publish(topic, msg)

    def publishTele(self, msg, suffix = ""):
        """ Publish the configured telemetry topic with supplied message"""
        self._ensureClient()

        # generate state topic based off config
        topic = self._formatTopic("telemetry_prefix", suffix)
        self._client.publish(topic, msg)

    def listen(self):
        self._ensureClient()
        self._client.loop_start()

    def disconnect(self):
        self._client.loop_stop()
        self._client.disconnect()

    def subscribe(self, suffix=""):
        self._subTopic = self._formatTopic("command_prefix", suffix)
        self._ensureClient()
        self._client.subscribe(self._subTopic + "/#")

    @property
    def oncmnd(self):
        """If implemented, called when the broker delivers a command msg."""
        return self._oncmnd

    @oncmnd.setter
    def oncmnd(self, func):
        """ Define the cmnd callback implementation.

        Expected signature is:
            cmnd_callback(topic, msg)

        topic:      fulltopic of the mqtt msg
        msg:        payload of the message
        """
        self._oncmnd = func

    def __init__(self, config=""):
        self._config = os.path.join(sys.path[0], "mqtt.yaml")
        if (config != ""):
            self._config=config

        self._client = None
        self._loadConfig()
    
    def _loadConfig(self):
        with open(self._config, "r") as stream:
                data = yaml.load(stream)
                self._cfgData = data['mqtt']
    
    def _connect(self):
        self._client = mqtt.Client(self._cfgData['client'])
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
#	self._client.username_pw_set(username=self._cfgData['user'],password=self._cfgData['pwd'])
        self._client.connect(self._cfgData['server'], self._cfgData['port'], 60)
        return self._client

    # The callback for when the client receives a CONNACK response from the server.
    def _on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
#        client.subscribe("$SYS/#")

    # The callback for when a PUBLISH message is received from the server.
    def _on_message(self, client, userdata, msg):
        if (self._subTopic is None):
            return
        
        prefix = self._cfgData['command_prefix']
        print(msg.topic)
        if msg.topic.startswith(prefix):
            self.oncmnd(msg.topic, str(msg.payload.decode("utf-8")))
        else:
            print(msg.topic+" "+str(msg.payload))

    def _formatTopic(self, topicType, suffix):
        prefixTopic = self._cfgData[topicType]
        topic = self._cfgData['topic']
        fullTopic = self._cfgData['fulltopic'].replace("%prefix%", prefixTopic).replace("%topic%", topic)
        if suffix != "":
            fullTopic += "/" + suffix
        return fullTopic

    def _ensureClient(self):
        if self._client is None:
            self._client = self._connect()
