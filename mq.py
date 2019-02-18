import paho.mqtt.client as mqtt
import yaml

#

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

class Client(object):
    """MQTT Wrapper client class.

    This is the main class for simple pub / sub with MQTT broker defined in mqtt.yaml

    General usage flow:
"""
    def __init__(self, config=""):
        self._config = "mqtt.yaml"
        if (config != ""):
            self._config=config

        self._client = None
        self._loadConfig()
    
    def _loadConfig(self):
        with open(self._config, "r") as stream:
                data = yaml.load(stream)
                self._cfgData = data['mqtt']
    
    def _connect(self):
        self._client = mqtt.Client()
        self._client.on_connect = on_connect
        self._client.on_message = on_message

        self._client.connect(self._cfgData['server'], self._cfgData['port'], 60)
        return self._client

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

    def publishState(self, msg, suffix = ""):
        """ Publish the configured state topic with supplied message"""
        self._ensureClient()

        # generate state topic based off config
        topic = self._formatTopic("state_prefix", suffix)
        self._client.publish(topic, msg)

    def publishTele(self, msg):
        """ Publish the configured telemetry topic with supplied message"""
        self._ensureClient()

        # generate state topic based off config
        topic = self._formatTopic("telemtry_prefix", suffix)
        self._client.publish(topic, msg)

