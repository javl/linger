#!/usr/bin/env python


import RPi.GPIO as GPIO
import subprocess

GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.IN)
GPIO.wait_for_edge(7, GPIO.FALLING)

subprocess.call(['service', 'linger_counter.sh', 'stop'], shell=False)
subprocess.call(['shutdown', '-h', 'now'], shell=False)
