# Original script by Richard IJzermans, with edits by Jasper van Loenen
# https://raspberrytips.nl/tm1637-4-digit-led-display-raspberry-pi/

import sys
import os
import time
import RPi.GPIO as IO

IO.setwarnings(False)
IO.setmode(IO.BCM)

HexDigits = [0x3f,0x06,0x5b,0x4f,0x66,0x6d,0x7d,0x07,0x7f,0x6f,0x77,0x7c,0x39,0x5e,0x79,0x71]

ADDR_AUTO = 0x40
ADDR_FIXED = 0x44
STARTADDR = 0xC0
BRIGHT_DARKEST = 0
BRIGHT_TYPICAL = 2
BRIGHT_HIGHEST = 7
OUTPUT = IO.OUT
INPUT = IO.IN
LOW = IO.LOW
HIGH = IO.HIGH

class TM1637:
	__doublePoint = False
	__Clkpin = 0
	__Datapin = 0
	__brightness = BRIGHT_TYPICAL;
	__currentData = [0,0,0,0];

	def __init__( self, pinClock, pinData, brightness ):
		self.__Clkpin = pinClock
		self.__Datapin = pinData
		self.__brightness = brightness;
		IO.setup(self.__Clkpin,OUTPUT)
		IO.setup(self.__Datapin,OUTPUT)

	def Clear(self):
		b = self.__brightness;
		point = self.__doublePoint;
		self.__brightness = 0;
		self.__doublePoint = False;
		data = [0x7F,0x7F,0x7F,0x7F];
		self.Show(data);
		self.__brightness = b; # restore saved brightness
		self.__doublePoint = point;

	def ShowInt(self, i):
		d = map(int, ','.join(str(i)).split(','))
		# add padding whitespace when using less than 4 digits
		for x in xrange(0, 4-len(d)):
			d.insert(0, 0x7F)
		self.Clear()
		self.Show(d)

	def Show( self, data ):
		for i in range(0,4):
			self.__currentData[i] = data[i];

		self.start();
		self.writeByte(ADDR_AUTO);
		self.stop();
		self.start();
		self.writeByte(STARTADDR);
		for i in range(0,4):
			self.writeByte(self.coding(data[i]));
		self.stop();
		self.start();
		self.writeByte(0x88 + self.__brightness);
		self.stop();

	def SetBrightness(self, brightness):		# brightness 0...7
		if( brightness > 7 ):
			brightness = 7;
		elif( brightness < 0 ):
			brightness = 0;

		if( self.__brightness != brightness):
			self.__brightness = brightness;
			self.Show(self.__currentData);

	def ShowDoublepoint(self, on):			# shows or hides the doublepoint
		if( self.__doublePoint != on):
			self.__doublePoint = on;
			self.Show(self.__currentData);

	def writeByte( self, data ):
		for i in range(0,8):
			IO.output( self.__Clkpin, LOW)
			if(data & 0x01):
				IO.output( self.__Datapin, HIGH)
			else:
				IO.output( self.__Datapin, LOW)
			data = data >> 1
			IO.output( self.__Clkpin, HIGH)

		# wait for ACK
		IO.output( self.__Clkpin, LOW)
		IO.output( self.__Datapin, HIGH)
		IO.output( self.__Clkpin, HIGH)
		IO.setup(self.__Datapin, INPUT)

		while(IO.input(self.__Datapin)):
			time.sleep(0.001)
			if( IO.input(self.__Datapin)):
				IO.setup(self.__Datapin, OUTPUT)
				IO.output( self.__Datapin, LOW)
				IO.setup(self.__Datapin, INPUT)
		IO.setup(self.__Datapin, OUTPUT)

	def start(self):
		IO.output( self.__Clkpin, HIGH) # send start signal to TM1637
		IO.output( self.__Datapin, HIGH)
		IO.output( self.__Datapin, LOW)
		IO.output( self.__Clkpin, LOW)

	def stop(self):
		IO.output( self.__Clkpin, LOW)
		IO.output( self.__Datapin, LOW)
		IO.output( self.__Clkpin, HIGH)
		IO.output( self.__Datapin, HIGH)

	def coding(self, data):
		if( self.__doublePoint ):
			pointData = 0x80
		else:
			pointData = 0;

		if(data == 0x7F):
			data = 0
		else:
			data = HexDigits[data] + pointData;
		return data
