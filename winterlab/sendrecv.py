import sys
import PyQt5.QtCore as qtc

import settings

sys._excepthook = sys.excepthook
sys.excepthook = settings.custom_excepthook

class SendRecvObj(qtc.QObject):
	send_done = qtc.pyqtSignal(float)
	failed = qtc.pyqtSignal()

	def __init__(self, winterlab):
		qtc.QObject.__init__(self)
		self.winterlab = winterlab
		self.trycount = 0

	def send_recv(self, outbound):
		try:
			val = float(self.winterlab.access_serial(1, outbound))
			if val == 1:
				self.trycount += 1
				self.send_recv
			else:
				self.send_done.emit(val)
		except (ValueError, TypeError):
			print('Value/Type Error while send/receiving. Retrying...')
			self.trycount += 1
			if self.trycount < 5:
				self.send_recv(outbound)
			else:
				self.failed.emit()
		except:

			sys.excepthook(*sys.exc_info())