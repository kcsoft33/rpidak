# rpidak
Tools to manage RPI 0 W Dakboard and integrate with homeassistant.io

#dependencies
pip install pyyaml
pip install paho-mqtt

# scripts
Motion detected
Presence detected
Power / Screen control

# config
Motion
Monitor
Presence
Mqtt - mqtt.yaml
Kiosk
 * Url
 * Schedule
Hass

# add to Raspberry Pi

~/.config/lxsession/LXDE-pi/autostart
#disable screensave
#@xscreensaver -no-splash

#hide cursor / turn off screen blank / launch control.py
@xset s off
@xset -dpms
@xset s noblank
@lxterminal -e /usr/bin/python3 /home/pi/rpidak/control.py