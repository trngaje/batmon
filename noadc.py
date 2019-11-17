#!/usr/bin/env python

import RPi.GPIO as GPIO
from adc import ADC

class NOADC(ADC):
	def __init__(self, miso, mosi, clk, cs, channel):
		pass

	def setup_pins(self):
		pass

	def get_resolution(self):
		return 1024.0

	def read_value(self):
		return 0

