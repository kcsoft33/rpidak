import appdaemon.plugins.hass.hassapi as hass
from appdaemon.adbase import ADBase
import datetime

#
# Kiosk
#
# Args:
#input: input_boolean.test_kiosk
#state: "on"
#sequence:
#  - uri: https://ha.domain.me
#    delay: 60
#  - uri: https://dakboard.com/app/screenPredefined?p=id
#    delay: 180
#
# on publish <topic> <uri>
# off publish <topic> off
# tab publish <topic> tab://##

class Kiosk(ADBase):
   def initialize(self):
     self.hass = self.get_plugin_api("HASS")
     self.mqtt = self.get_plugin_api("MQTT")
     self.log("Kiosk startup")
     self.log_level = 1
     if "log_level" in self.args:
        self.log_level = self.args["log_level"]
     if "input" in self.args and "topic" in self.args:
        if self.log_level > 0:
           self.log("Subscribing to event for {}".format(self.args["input"]))
        self.hass.listen_state(self.state_change, self.args["input"])
        self.kiosk_index = 0
        self.loop = False
        self.kiosk_enabled = False
        self.switch_enabled = False
        self.send_off()
        if "enabled" in self.args:
           self.kiosk_enabled = self.hass.get_state(self.args["enabled"]) == "on"
           self.hass.listen_state(self.kiosk_state_change, self.args["enabled"])
        self.publish_state = False
        if "state_topic" in self.args:
           self.state_topic = self.args["state_topic"]
           self.publish_state = True

        self.initial_entry = False
        self.sequence = self.args["sequence"]
        if self.hass.get_state(self.args["input"]) == "on" and self.kiosk_enabled:
          self.switch_enabled = True
          self.initial_entry = True
          self.update_kiosk(False)

   def log(self, kwargs):
      self.hass.log(kwargs)
   # def mqtt_sub(self, event_name, data, kwargs):
   #    self.log("T:{} P:{} K:{}".format(event_name, data, kwargs))

   def kiosk_state_change(self, entity, attribute, old, new, kwargs):
      if (new == "on" and old == "off"):
         self.kiosk_enabled = True
         self.state_change(entity, attribute, old, new, kwargs)
      elif(new == "off" and old == "on"):
         self.kiosk_enabled = False
         self.state_change(entity, attribute, old, new, kwargs)

   def send_off(self):
      if "off_payload" in self.args:
         payload = self.args["off_payload"]
      else:
         payload = "off"
      self.switch_enabled = False
      if self.log_level > 0:
         self.log("sending {} to {}".format(payload, self.args["topic"]))
      self.mqtt.mqtt_publish(self.args["topic"], payload = payload)

   def state_change(self, entity, attribute, old, new, kwargs):
      if self.log_level > 0:
         self.log("{} turned {} from {}".format(entity, new, old))
      if (new == "on" and old == "off"):
         self.switch_enabled = True
         self.update_kiosk(False)
      elif new == "off" and old == "on":
         self.kiosk_index = 0
         self.loop = False
         self.send_off()

   def update_kiosk(self, useDelay):
      if (not self.switch_enabled or not self.kiosk_enabled):
         return
      
      entry = self.sequence[self.kiosk_index]
      self.kiosk_index+=1
      loop = False
      if (self.kiosk_index >= len(self.sequence)):
         self.kiosk_index = 0
         if (len(self.sequence) > 1):
            loop = True

      if (self.loop):
         uri = "tab://"
      else:
         uri = entry["uri"]

      if (loop):
         self.loop = loop
      
      if (self.initial_entry and useDelay):
         self.initial_entry = False
         delay = self.sequence[0]["delay"]
      else:
         if (useDelay):
            delay = entry["delay"]
         else:
            delay = 0

      state_payload = ""
      if self.publish_state:
         state_payload = entry["state_payload"]

      if self.log_level > 0:
         self.log("Action {} in {}".format(uri, delay))

      if (useDelay and len(self.sequence) > 1 or not useDelay):
         self.hass.run_in(self.action, delay, topic = self.args["topic"], uri = uri, state_payload = state_payload, fullUri = entry['uri'])

   def action(self, kwargs):
      if self.log_level > 1:
         self.log("Publish {} to {}".format(kwargs["fullUri"], kwargs["topic"]))
      if (not self.kiosk_enabled or not self.switch_enabled):
         if self.log_level > 1:
            self.log("Publish aborted for {}".format(kwargs["fullUri"]))
         return
      self.mqtt.mqtt_publish(kwargs["topic"], payload = kwargs["uri"])
      if (self.publish_state):
         self.mqtt.mqtt_publish(self.state_topic, payload = kwargs["state_payload"])
      if (self.kiosk_enabled):
         self.update_kiosk(True)
