# Raspberry Pi Robot - Android Remote Control #

Remote control of a Raspberry Pi robot from an Android device.

## Hardware Requirements ##

The Raspberry Pi code was developed using a Raspberry Pi 3 Model B and:

- [CamJam EduKit 1 Starter](http://camjam.me/?page_id=236)
- [CamJam EduKit 3 Robotics](http://camjam.me/?page_id=1035)
- [a compatible USB webcam](http://elinux.org/RPi_USB_Webcams)
- earbuds or powered speaker

The Android app was developed with [MIT App Inventor](http://appinventor.mit.edu) and should run on any Android smartphone or tablet.

## Software Requirements ##

The [Flask web server](http://flask.pocoo.org/) is used to enable the Raspberry Pi to respond to HTTP requests, installed as described in this extract from [Getting Started with Raspberry Pi](http://mattrichardson.com/Raspberry-Pi-Flask/).

[SimpleCV](http://simplecv.org/) is used to retrieve images from a webcam attached directly to the Raspberry Pi, installed as described in [this document](http://simplecv.readthedocs.io/en/latest/HOWTO-Install%20on%20RaspberryPi.html). Increasing the delay in the constructor for the Camera object can increase reliability when detecting some webcams.

The [Festival speech synthesiser](http://www.cstr.ed.ac.uk/projects/festival/) is used to make announcements, installed as described on [this page](http://elinux.org/RPi_Text_to_Speech_(Speech_Synthesis)#Festival_Text_to_Speech).

## Installation ##

Create a directory named '/home/pi/boot' and copy the three Python scripts into it. If the scripts are installed to a different directory, the file paths within the scripts should be modified accordingly.

Call bootscript.py at boot time, for example by adding this line to cron with 'sudo crontab -e':

    @reboot python /home/pi/boot/bootscript.py >/home/pi/boot/bootscript.log 2>/home/pi/boot/bootscript.err

## Operation ##

The script **bootscript.py** waits for a network connection to be established, announces the IP address, then starts the robot webserver and the shutdown monitor. This script is optional, but may be useful for headless operation.

The script **shutdownbutton.py** waits for a button to be pressed, then halts the Raspberry Pi. This script is optional, but may be useful for headless operation.

The webserver script **roboserver.py** initialises the Raspberry Pi hardware, then starts a web server to respond to HTTP requests which control the robot. The server returns either robot status information (from the LEDs, ultrasound unit and line follower unit) encoded in [JSON](http://www.w3schools.com/json/) format, or an image captured from the webcam, depending on the request received.

The script may need to be adapted depending on how the hardware components are connected; in particular, when using *EduKit 1* and *EduKit 3* simultaneously, it is necessary to use different GPIO pins for *EduKit 1* than are shown in the CamJam worksheets.

When it is started, the script first flashes the LEDs, then illuminates the yellow LED while the USB camera is detected and initialised. The yellow LED is extinguished when the camera detection routine completes.

The green LED is illuminated when the Flask webserver is started. The robot will respond to commands a few seconds after the LED illuminates. The supported HTTP requests can be seen by inspecting the roboserver.py script.

The red LED is illuminated whenever the motors are active. The yellow LED is illuminated, accompanied by an audible warning from the buzzer, when an object is detected within 10 cm of the infrared unit.

*Note:* The Flask web server needs root permissions to access the network stack, so the roboserver.py script needs to be run as root.

## Android App ##

The **roboclient.apk** file is a packaged Android app that should run successfully on any recent Android device. ‘Sideloading’ of apps needs to be enabled in order to install the client app. On most devices there is a checkbox under *Settings -> Security* that refers to installing apps from unknown or untrusted sources. Some devices will prompt the user to change the setting when an attempt is first made to sideload an app.

Enter the IP address of the Raspberry Pi in the textbox, then click Start. If the server is successfully contacted, an image from the webcam replaces the picture of the EduKit 3 components, and the range measured by the ultrasonic unit is displayed.

Sliding the Raspberry Pi icon around on the blue canvas controls the motors, and affords full control of speed and direction. The robot stops automatically when the icon is released. The slider below the canvas controls the maximum motor speed.

The buttons at the bottom sound the buzzer, speak a preset phrase, and flash the LEDs.
 
## MIT App Inventor ##

The **roboclient.aia** file contains the MIT App Inventor source from which the app is built. This file is not required to use the app.

MIT App Inventor allows Android apps to be easily built using drag-and-drop interfaces for both design and coding. Further information is available at:

[http://appinventor.mit.edu/explore/get-started.html](http://appinventor.mit.edu/explore/get-started.html)

Once an account has been created on App Inventor, roboclient.aia can be imported as a new project in order to examine and modify the code. The app can then be rebuilt and downloaded locally as an APK file, or installed directly to the Android device via a QR code.
 
Gerard Kelly, October 2016
