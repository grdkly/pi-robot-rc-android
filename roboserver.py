# 
# Web server for control of CamJam EduKit1 LEDs, EduKit3 Robot, and USB camera
#
# Gerard Kelly, October 2016
#

import RPi.GPIO as GPIO
import time
import subprocess
from flask import Flask, request, jsonify, send_file
from SimpleCV import Camera
from urllib import unquote_plus

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#
# initialise GPIO pins for LEDs, buzzer and button
#

pinLEDs = {16:'red', 20:'yellow', 21:'green'}
for pin in pinLEDs:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

pinButton = 26
GPIO.setup(pinButton, GPIO.IN)

pinBuzzer = 19
GPIO.setup(pinBuzzer, GPIO.OUT)
GPIO.output(pinBuzzer, GPIO.LOW)

#
# initialise GPIO motor controller pins
#

pinMotorAForwards = 9
pinMotorABackwards = 10
pinMotorBForwards = 7
pinMotorBBackwards = 8

GPIO.setup(pinMotorAForwards, GPIO.OUT)
GPIO.setup(pinMotorABackwards, GPIO.OUT)
GPIO.setup(pinMotorBForwards, GPIO.OUT)
GPIO.setup(pinMotorBBackwards, GPIO.OUT)

# PWM parameters
Frequency  = 20  # hertz
DutyCycleA = 100 # max 100, adjust to equalise motors
DutyCycleB = 100 # max 100, adjust to equalise motors
Stop = 0

# enable PWM mode for motor control pins
pwmMotorAForwards  = GPIO.PWM(pinMotorAForwards, Frequency)
pwmMotorABackwards = GPIO.PWM(pinMotorABackwards, Frequency)
pwmMotorBForwards  = GPIO.PWM(pinMotorBForwards, Frequency)
pwmMotorBBackwards = GPIO.PWM(pinMotorBBackwards, Frequency)

# start the software PWM with a duty cycle of zero (stop)
pwmMotorAForwards.start(Stop)
pwmMotorABackwards.start(Stop)
pwmMotorBForwards.start(Stop)
pwmMotorBBackwards.start(Stop)

#
# initialise ultrasound module
#

# GPIO ultrasound module pins
pinTrigger = 17
pinEcho = 18
GPIO.setup(pinTrigger, GPIO.OUT)
GPIO.setup(pinEcho, GPIO.IN)
GPIO.output(pinTrigger, GPIO.LOW)

#
# initialise line detector module
#

# GPIO line detector pin
pinLineFollower = 25
GPIO.setup(pinLineFollower, GPIO.IN)

#
# LED functions
#

def ledson():
    for pin in pinLEDs:
        GPIO.output(pin, GPIO.HIGH)

def ledsoff():
    for pin in pinLEDs:
        GPIO.output(pin, GPIO.LOW)

def flashleds(count):
    for i in range(count):
        ledsoff()
        time.sleep(0.2)
        ledson()
        time.sleep(0.2)
        ledsoff()

def ledcontrol(colour, state):
    for pin in pinLEDs:
        if pinLEDs[pin] == colour:
            if state == 'on':
                 GPIO.output(pin, GPIO.HIGH)
            elif state == 'off':
                 GPIO.output(pin, GPIO.LOW)
                 
#
# buzzer functions
#

def buzzerbeep():
    GPIO.output(pinBuzzer, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(pinBuzzer, GPIO.LOW)
    time.sleep(0.1)

#
# ultrasound functions
#

def MeasureDistance():
    
    # send 10us pulse to Trigger
    GPIO.output(pinTrigger, GPIO.HIGH)
    time.sleep(0.000010)
    GPIO.output(pinTrigger, GPIO.LOW)
    
    # wait for start of Echo pin pulse
    StartTime = time.time()
    while GPIO.input(pinEcho) == GPIO.LOW:
        StartTime = time.time()
        
    # wait for end of Echo pin pulse
    StopTime = time.time()
    while GPIO.input(pinEcho) == GPIO.HIGH:
        StopTime = time.time()
        # long pulse indicates object is out of range (too near or too far)
        if StopTime - StartTime >= 0.030:
            StopTime = StartTime
            break
        
    # distance to object (in metres) is half of echo pulse length times speed of sound (m/s)
    distance = (StopTime - StartTime) * 343.26 / 2

    # warn if close to an obstacle
    if distance < 0.10 and distance != 0:
        ledcontrol('yellow', 'on')
        buzzerbeep()
    else:
        ledcontrol('yellow', 'off')

    return distance

#
# line detector functions
#

def BlackOrWhite():
    # sensor is high when reflection detected
    if GPIO.input(pinLineFollower) == GPIO.HIGH:
        return 'White'
    else:
        return 'Black'

#
# motor control functions
#

def StopMotors():
    pwmMotorAForwards.ChangeDutyCycle(Stop)
    pwmMotorABackwards.ChangeDutyCycle(Stop)
    pwmMotorBForwards.ChangeDutyCycle(Stop)
    pwmMotorBBackwards.ChangeDutyCycle(Stop)

def Forwards():
    pwmMotorAForwards.ChangeDutyCycle(DutyCycleA)
    pwmMotorABackwards.ChangeDutyCycle(Stop)
    pwmMotorBForwards.ChangeDutyCycle(DutyCycleB)
    pwmMotorBBackwards.ChangeDutyCycle(Stop)

def Backwards():
    pwmMotorAForwards.ChangeDutyCycle(Stop)
    pwmMotorABackwards.ChangeDutyCycle(DutyCycleA)
    pwmMotorBForwards.ChangeDutyCycle(Stop)
    pwmMotorBBackwards.ChangeDutyCycle(DutyCycleB)

def TurnLeft():
    pwmMotorAForwards.ChangeDutyCycle(Stop)
    pwmMotorABackwards.ChangeDutyCycle(DutyCycleA)
    pwmMotorBForwards.ChangeDutyCycle(DutyCycleB)
    pwmMotorBBackwards.ChangeDutyCycle(Stop)

def TurnRight():
    pwmMotorAForwards.ChangeDutyCycle(DutyCycleA)
    pwmMotorABackwards.ChangeDutyCycle(Stop)
    pwmMotorBForwards.ChangeDutyCycle(Stop)
    pwmMotorBBackwards.ChangeDutyCycle(DutyCycleB)

# inputs are integers in range [-100, +100]
def MotorSpeed(left, right):
    if left > 0:
        pwmMotorAForwards.ChangeDutyCycle(DutyCycleA * left / 100)
        pwmMotorABackwards.ChangeDutyCycle(Stop)
    else:
        pwmMotorAForwards.ChangeDutyCycle(Stop)
        pwmMotorABackwards.ChangeDutyCycle(DutyCycleA * abs(left) / 100)
    if right > 0:
        pwmMotorBForwards.ChangeDutyCycle(DutyCycleA * right / 100)
        pwmMotorBBackwards.ChangeDutyCycle(Stop)
    else:
        pwmMotorBForwards.ChangeDutyCycle(Stop)
        pwmMotorBBackwards.ChangeDutyCycle(DutyCycleA * abs(right) / 100)

#
# web server functions
#

app = Flask(__name__)

@app.route("/")
def root():
    return jsonstatus()

@app.route("/beep")
def beep():
    buzzerbeep()
    return jsonstatus()

@app.route("/led")
def led():
    return jsonstatus()

@app.route("/led/flash")
def ledflash():
    flashleds(3)
    ledcontrol('green', 'on')
    return jsonstatus()
    
@app.route("/led/<colour>/<state>")
def ledstate(colour, state):
    ledcontrol(colour, state)
    return jsonstatus()

@app.route("/robot")
def robot():
    StopMotors()
    ledcontrol('red', 'off')
    return jsonstatus()

@app.route("/robot/stop")
def robotstop():
    StopMotors()
    ledcontrol('red', 'off')
    return jsonstatus()

@app.route("/robot/forwards")
def robotforwards():
    Forwards()
    ledcontrol('red', 'on')
    return jsonstatus()

@app.route("/robot/backwards")
def robotbackwards():
    Backwards()
    ledcontrol('red', 'on')
    return jsonstatus()

@app.route("/robot/left")
def robotleft():
    TurnLeft()
    ledcontrol('red', 'on')
    return jsonstatus()

@app.route("/robot/right")
def robotright():
    TurnRight()
    ledcontrol('red', 'on')
    return jsonstatus()

@app.route("/robot/motors/<left>/<right>")
def robotmotors(left, right):
    # convert string arguments to integers
    left = int(left)
    right = int(right)
    # allowed range [-100, +100]
    if left > 100:
        left = 100
    elif left < -100:
        left = -100
    if right > 100:
        right = 100
    elif right < -100:
        right = -100
    MotorSpeed(left,right)
    ledcontrol('red', 'on')
    return jsonstatus()

@app.route("/speak/<phrase>")
def speak(phrase):
    phrase = unquote_plus(phrase)
    p1 = subprocess.Popen(['echo', phrase], stdout=subprocess.PIPE)
    subprocess.Popen(['festival', '--tts'], stdin=p1.stdout) # don't wait for process to end
    return jsonstatus()

@app.route("/webcam/image.jpg")
def image_jpg():
    myCamera.getImage().save('/home/pi/boot/image.jpg')
    return send_file('/home/pi/boot/image.jpg', attachment_filename='image.jpg')

def jsonstatus():
    status = {}
    for pin in pinLEDs:
        status[pinLEDs[pin]] = str(GPIO.input(pin))
    status['distance'] = str(round(MeasureDistance() * 100, 1)) + ' cm'
    status['surface'] = BlackOrWhite()
    return jsonify(**status)

#
# Main
#

# signal camera startup
flashleds(3)
ledcontrol('yellow', 'on')

# create Camera object (delay helps detect some USB webcams)
myCamera = Camera(camera_index=0, prop_set={'width': 320, 'height': 240, 'delay':5})

# signal server startup
ledcontrol('yellow', 'off')
ledcontrol('green', 'on')

# start web server
app.run(host="0.0.0.0", port=80, debug=False)
