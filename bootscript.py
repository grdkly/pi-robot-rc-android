#
# Boot script, called by cron using @reboot
#
# Gerard Kelly, October 2016
#

import time
import subprocess
import RPi.GPIO as GPIO

# functions
def speak(phrase):
    p1 = subprocess.Popen(['echo', phrase], stdout=subprocess.PIPE)
    subprocess.Popen(['festival', '--tts'], stdin=p1.stdout).wait()

# main
speak("starting boot script")

# check for valid IP address for up to 20 seconds
# if IPv4 and IPv6 both assigned, IPv4 is first in string
online = False
for i in range(20):
    (stdoutdata, stderrdata) = subprocess.Popen(['hostname','-I'], stdout=subprocess.PIPE).communicate()
    if stdoutdata != '':
        ip = stdoutdata.split()
        ipv4 = ip[0]
        if ipv4.find('.') != -1 and ipv4[0:7] != '169.254':
            online = True     
            ipv4 = ipv4.replace('.', ',. dot,. ') # improve phrasing
            speak("my I P address is,. " + ipv4)
            break
    time.sleep(1)

# start the web server for robot functions
if online:
    speak("starting the web server")
    logfile = open('/home/pi/boot/roboserver.log', 'w')
    errfile = open('/home/pi/boot/roboserver.err', 'w')
    subprocess.Popen(['sudo', 'python', '/home/pi/boot/roboserver.py'], stdout=logfile, stderr=errfile)
else:
    speak("web server not started")

# start the shutdown button monitor
speak("press the red button to shut down")
subprocess.Popen(['sudo', 'python', '/home/pi/boot/shutdownbutton.py'])

# end
