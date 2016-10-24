#
# Shut down on button press
#
# Gerard Kelly, October 2016
#

import RPi.GPIO as GPIO
import subprocess

# set GPIO mode
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# wait for button press
button = 26
GPIO.setup(button, GPIO.IN)
GPIO.wait_for_edge(button, GPIO.FALLING)

# shut down
subprocess.Popen(['sudo', 'halt'])
