import sys
import time
import PyQt5.QtCore as qtc

import settings

sys._excepthook = sys.excepthook
sys.excepthook = settings.custom_excepthook

class PlotterObj(qtc.QObject):
	ready_to_fetch = qtc.pyqtSignal()
	ready_to_update = qtc.pyqtSignal()
	kill_signal = qtc.pyqtSignal()

	def __init__(self, scope_display):
		qtc.QObject.__init__(self)
		self.scope_display = scope_display
		self.running = True

	def do_fetch(self):
		try:
			res = self.scope_display.get_data()
			return res
		except:
			sys.excepthook(*sys.exc_info())
			print('Exception while fetching in PlotterThread')
			self.kill_signal.emit()
		
	def run(self):
		try:
			while(self.running):
				fetched = self.do_fetch()
				if fetched == 0:
					print('not ready')
					time.sleep(0.1) # if you couldn't get the batch, wait briefly and try again
					self.run()
				else:
					if fetched == -1:
						self.running = False
						self.kill_signal.emit()
					self.ready_to_update.emit() # got the batch; update GUI graph pls
					time.sleep(0.1)
		except:
			
			sys.excepthook(*sys.exc_info())
			self.running = False
			self.kill_signal.emit()
