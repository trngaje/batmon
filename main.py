#!/usr/bin/python

import RPi.GPIO as GPIO
import time
import signal
import datetime
import os
import subprocess

from config import *
from mcp3551 import MCP3551
from mcp3001 import MCP3001
from mcp3008 import MCP3008
from mcp3208 import MCP3208
from noadc import NOADC

p = subprocess.Popen([BATGUISERVERPATH+"/batguiserver", "-s "+str(ICONSIZE), "-x "+str(ICONX), "-y "+str(ICONY), "-p"], 
                     stdin=subprocess.PIPE)


def change_led(led):
	if (LEDS != 1):
		return

	if (led == "green"):
		GPIO.output(GOODVOLTPIN, GPIO.HIGH)
		GPIO.output(LOWVOLTPIN, GPIO.LOW)

		printf("Changed green LED to on, red LED to off")
	elif (led == "red"):
		GPIO.output(GOODVOLTPIN, GPIO.LOW)
		GPIO.output(LOWVOLTPIN, GPIO.HIGH)

		printf("Changed green LED to off, red LED to on")

def end_process(signalnum = None, handler = None):
	GPIO.cleanup()
	p.stdin.write('[exit]')
	exit(0)

status = 0

# prepare handlers for process exit
signal.signal(signal.SIGTERM, end_process)
signal.signal(signal.SIGINT, end_process)

# initialize ADC
if (ADC == "MCP3551"):
	adc = MCP3551(SPIMISO, SPIMOSI, SPICLK, SPICS)
elif (ADC == "MCP3001"):
	adc = MCP3001(SPIMISO, SPIMOSI, SPICLK, SPICS)
elif (ADC == "MCP3008"):
	adc = MCP3008(SPIMISO, SPIMOSI, SPICLK, SPICS, ADCCHANNEL)
elif (ADC == "MCP3208"):
	adc = MCP3208(SPIMISO, SPIMOSI, SPICLK, SPICS, ADCCHANNEL)
elif (ADC == "NOADC"):
    adc = NOADC(SPIMISO, SPIMOSI, SPICLK, SPICS, ADCCHANNEL)
else:
	print("Unknown ADC type " + str(ADC) + "! Please set ADC in config.py to one of the supported types.")
	exit(0)

adc.setup_pins()

SVOLT100 = VOLT100 * HIGHRESVAL / (LOWRESVAL + HIGHRESVAL)
SVOLT75 = VOLT75 * HIGHRESVAL / (LOWRESVAL + HIGHRESVAL)
SVOLT50 = VOLT50 * HIGHRESVAL / (LOWRESVAL + HIGHRESVAL)
SVOLT25 = VOLT25 * HIGHRESVAL / (LOWRESVAL + HIGHRESVAL)
SVOLT0 = VOLT0 * HIGHRESVAL / (LOWRESVAL + HIGHRESVAL)

ADC100 = SVOLT100 / (ADCVREF / adc.get_resolution())
ADC75 = SVOLT75 / (ADCVREF / adc.get_resolution())
ADC50 = SVOLT50 / (ADCVREF / adc.get_resolution())
ADC25 = SVOLT25 / (ADCVREF / adc.get_resolution())
ADC0 = SVOLT0 / (ADCVREF / adc.get_resolution())

if (DEBUGMSG == 1):
	print("Batteries 100% voltage:		" + str(VOLT100))
	print("Batteries 75% voltage:		" + str(VOLT75))
	print("Batteries 50% voltage:		" + str(VOLT50))
	print("Batteries 25% voltage:		" + str(VOLT25))
	print("Batteries dangerous voltage:	" + str(VOLT0))
	print("ADC 100% value:			" + str(ADC100))
	print("ADC 75% value:			" + str(ADC75))
	print("ADC 50% value:			" + str(ADC50))
	print("ADC 25% value:			" + str(ADC25))
	print("ADC dangerous voltage value:	" + str(ADC0))

# setup LED pins
if (LEDS == 1):
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(GOODVOLTPIN, GPIO.OUT)
	GPIO.setup(LOWVOLTPIN, GPIO.OUT)
	GPIO.output(GOODVOLTPIN, GPIO.LOW)
	GPIO.output(LOWVOLTPIN, GPIO.LOW)

count = 0

if (CSVOUT == 1):
	print("#;Timestamp;Date and time;Raw value;Voltage")

i = 0
battery = [ADC0, ADC25, ADC50, ADC75, ADC100]


while True:
	# measure three times and use the average
	if (ADC == "NOADC"):
 		ret = battery[i]

		i = i + 1

		if (i > 4):
			i = 0
	else:
		ret1 = adc.read_value()
		ret2 = adc.read_value()
		ret3 = adc.read_value()
		ret = (ret1 + ret2 + ret3) / 3



	voltage = ((HIGHRESVAL + LOWRESVAL) * ret * (ADCVREF / adc.get_resolution())) / HIGHRESVAL

	if (CSVOUT == 1):
		print(str(count) + ";" + str(time.time()) + ";" + str(datetime.datetime.now()) + ";" + str(ret) + ";" + str(voltage))

	if (DEBUGMSG == 1):
		print("ADC value: " + str(ret) + " (" + str(voltage) + " V)")

	if (ret < ADC0):
		if (status != 0):
			change_led("red")
			p.stdin.write('[b:0]')


		status = 0
	elif (ret < ADC25):
		if (status != 25):
			change_led("red")
			p.stdin.write('[b:25]')


		status = 25
	elif (ret < ADC50):
		if (status != 50):
			change_led("green")
			p.stdin.write('[b:50]')
		status = 50
	elif (ret < ADC75):
		if (status != 75):
			change_led("green")
			p.stdin.write('[b:75]')


		status = 75
	else:
		if (status != 100):
			change_led("green")
			p.stdin.write('[b:100]')

		status = 100

	count += 1
	time.sleep(REFRESHRATE)
