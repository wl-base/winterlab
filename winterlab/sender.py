import sys
import PyQt5.QtCore as qtc

import settings

sys._excepthook = sys.excepthook
sys.excepthook = settings.custom_excepthook

class SenderObj(qtc.QObject):
	send_done = qtc.pyqtSignal()
	failed = qtc.pyqtSignal()

	def __init__(self, winterlab):
		qtc.QObject.__init__(self)
		print('initializing sender obj')
		self.winterlab = winterlab
		self.trycount = 0

	def send_str(self, outbound):
		try:
			self.winterlab.write(outbound)
			print('Sending')
			self.send_done.emit()
			print('Done')
		except:
			sys.excepthook(*sys.exc_info())
			self.failed.emit()