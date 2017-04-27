#!/usr/bin/env python

# Quit this script if we're not running on the pi zero
# (otherwise sticking the sd card into my regular pi
# without the button will turn it off immediately
import platform
if platform.machine() != "armv6l":
    exit();

import RPi.GPIO as GPIO
import subprocess

GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.IN)
GPIO.wait_for_edge(7, GPIO.FALLING)

subprocess.call(['service', 'linger_counter.sh', 'stop'], shell=False)
subprocess.call(['shutdown', '-h', 'now'], shell=False)
