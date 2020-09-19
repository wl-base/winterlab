import sys
import time
import signal
import serial
import serial.tools.list_ports
import PyQt5.QtCore as qtc

import settings

sys._excepthook = sys.excepthook
sys.excepthook = settings.custom_excepthook

class WLBoard:
	def __init__(self):
		self.wl_mutex = qtc.QMutex()
		return

	def find_board(self):
		for port in serial.tools.list_ports.comports():
			print(port.hwid)
			print(port.device)
			if 'PID='+settings.VENDOR_ID+':'+settings.PRODUCT_ID in port.hwid:
				print('Found WinterLab. Connecting...')
				try:
					self.device = serial.Serial(port.device, 
						baudrate = 115200, 
						timeout=2.0, 
						writeTimeout=2.0)
					print('Connected.')
					return 1
				except:
					print('Failed to connect.')
					return 0
			else:
				continue
		print('No WinterLab board found. Please check connection.')
		return 0

	def readline(self):
		try:
			if settings.PYVERSION < 3.0:
				str = self.device.readline()
			else:
				str = self.device.readline().decode()
			time.sleep(0.01)
			return str
		except:
			print('Error communication with device. Check connection.')

	def write(self, outbound):
		try:
			if settings.PYVERSION < 3.0:
				self.device.write('%s' % (outbound))
			else:
				self.device.write(str(outbound).encode())
			time.sleep(0.01)
		except:
			print('Error: Lost board connection.')

	def write_read(self, outbound):
		try:
			if settings.PYVERSION < 3.0:
				self.device.write('%s' % (outbound))
			else:
				self.device.write(str(outbound).encode())
			val = self.readline()
			time.sleep(0.01)
			return val
		except:
			print('Error: Lost board connection.')
			return -1

	def write_doubleread(self, outbound):
		try:
			if settings.PYVERSION < 3.0:
				self.device.write('%s' % (outbound))
			else:
				self.device.write(str(outbound).encode())
			batch1 = self.readline()
			batch2 = self.readline()
			time.sleep(0.01)
			return batch1, batch2
		except:
			print('Error: Lost board connection.')
			return -1

	def access_serial(self, access_type, outbound=None): # 1 for write_read, 2 for write_doubleread
		self.wl_mutex.lock()
		if access_type == 1:
			res = self.write_read(outbound)
		else:
			res = self.write_doubleread(outbound)
		time.sleep(0.01)
		self.wl_mutex.unlock()
		return res
