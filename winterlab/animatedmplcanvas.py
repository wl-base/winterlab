import sys
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import random
import csv
import time
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg

import settings
from wlboard import WLBoard

sys._excepthook = sys.excepthook
sys.excepthook = settings.custom_excepthook

class AnimatedMplCanvas(FigureCanvas):
	saveDirSetSignal = qtc.pyqtSignal(str)
	def __init__(self, parent=None, width=4, height=3, dpi=100, *args, **kwargs):
		FigureCanvas.__init__(self, matplotlib.figure.Figure())
		self.saveDirSet = False
		self.saveFileName = ''

		self.ax1 = self.figure.add_subplot(111)
		self.ax2 = self.ax1.twinx()
		self.ax1.grid()
		self.figure.tight_layout()

		self.ax1_bg = self.copy_from_bbox(self.ax1.bbox)

		self.xdata = np.linspace(0, settings.BATCH_LEN, settings.BATCH_LEN)
		self.xdata = [x * settings.DELTA_X for x in self.xdata]
		self.ydata1 = [random.randint(0, 10) for i in range(settings.BATCH_LEN)]
		self.ydata2 = [random.randint(0, 10) for i in range(settings.BATCH_LEN)]
		self.trig = 127
		self.trigCh = 1
		trigvals = [5.0 - (10.0*float(self.trig)/255.0 - 3.2) for x in self.xdata]

		self.line1, = self.ax1.plot(self.xdata, self.ydata1, lw=2, color='b', animated=True)
		self.line2, = self.ax2.plot(self.xdata, self.ydata2, lw=2, color='g', animated=True)
		self.trigline1, = self.ax1.plot(self.xdata, trigvals, lw=1, color='r', animated=True)
		self.trigline2, = self.ax2.plot([],[], lw=1, color='r', animated=True)
		self.xmin = settings.INITIAL_XMIN
		self.xmax = settings.INITIAL_XMAX
		self.ymin1 = settings.INITIAL_YMIN
		self.ymax1 = settings.INITIAL_YMAX
		self.ymin2 = settings.INITIAL_YMIN
		self.ymax2 = settings.INITIAL_YMAX

		self.ax1.set_xlim(self.xmin, self.xmax)
		self.ax1.set_ylim(self.ymin1, self.ymax1)
		self.ax2.set_ylim(self.ymin2, self.ymax2)

		self.ax1.tick_params(axis='x', colors='white')
		self.ax1.tick_params(axis='y', colors='white')
		self.ax2.tick_params(axis='y', colors='white')

		self.x_div_text = self.ax1.text(0.02, 0.05, '', transform=self.ax1.transAxes)
		self.y1_div_text = self.ax1.text(0.4, 0.05, '', transform=self.ax1.transAxes)
		self.y2_div_text = self.ax1.text(0.75, 0.05, '', transform=self.ax1.transAxes)

		self.mpl_connect('draw_event', self._draw_event)
		self.draw_idle()
		self.draw()

		self.running = True

	def _draw_event(self, evt):
		self.ax1.clear()
		self.ax1.grid()
		self.ax1_bg = self.copy_from_bbox(self.ax1.get_figure().bbox)

	def start_plot(self):
		self.winterlab = WLBoard()
		if not self.winterlab.find_board():
			return 0
		else:
			self.running = True
			return 1

	def update_figure(self):
		if self.running == True:
			self.restore_region(self.ax1_bg)

			ydata1 = self.ydata1
			ydata2 = self.ydata2
			try:
				self.line1.set_ydata(ydata1)
				self.line2.set_ydata(ydata2)
				trigvals = [5.0 - (10.0*float(self.trig)/255.0 - 3.2) for x in self.xdata]
				if self.trigCh == 1:
					self.trigline1.set_data(self.xdata, trigvals)
					self.trigline2.set_data([], [])
				else:
					self.trigline2.set_data(self.xdata, trigvals)
					self.trigline1.set_data([], [])
				self.ax2.draw_artist(self.trigline2)
				self.ax1.draw_artist(self.trigline1)
				self.ax1.draw_artist(self.line1)
				self.ax2.draw_artist(self.line2)
				self.ax1.set_xlim(self.xmin, self.xmax)
				self.ax1.set_ylim(self.ymin1, self.ymax1)
				self.ax2.set_ylim(self.ymin2, self.ymax2)

				self.x_div_text.set_text('x: ' + str(round(((self.xmax - self.xmin)*1e6/5.0), 3)) + ' us/div')
				self.y1_div_text.set_text('Ch1: ' + str(round(((self.ymax1 - self.ymin1)/5.0), 3)) + ' V/div')
				self.y2_div_text.set_text('Ch2: ' + str(round(((self.ymax2 - self.ymin2)/5.0), 3)) + ' V/div')

				self.ax1.draw_artist(self.x_div_text)
				self.ax1.draw_artist(self.y1_div_text)
				self.ax1.draw_artist(self.y2_div_text)

				self.blit(self.ax1.clipbox)
			except:
				print('Uncaught error in update_figure')
				sys.excepthook(*sys.exc_info())
				print(ydata1)
				print(ydata2)
				return
		else:
			return
	
	def set_trig_ch(self, chnum):
		self.trigCh = chnum	

	def set_trig(self, val):
		self.trig = val	

	def update_axes(self):
		self.ax1.set_xlim(self.xmin, self.xmax)
		self.ax1.set_ylim(self.ymin1, self.ymax1)
		self.ax2.set_ylim(self.ymin2, self.ymax2)
		self.ax1.set_xticklabels([])
		self.ax1.set_yticklabels([])
		self.ax2.set_yticklabels([])

	def get_data(self):
		batch = self.read_and_parse()
		
		if len(batch) != 2:
			if batch == [-1]:
				return -1
			print('Batch is wrong length; retrying.')
			return 0
		else:
			try:
				new_data1 = [5.0 - (10.0*float(y)/255.0 - 3.2) for y in batch[0]]
				new_data2 = [5.0 - (10.0*float(y)/255.0 - 3.2) for y in batch[1]]

			except ValueError:
				print('ValueError in function get_data')
				return 0
			except:
				sys.excepthook(*sys.exc_info())
				return -1

			if len(new_data1) != len(self.xdata) or len(new_data2) != len(self.xdata):
				return 0
			else:
				self.ydata1 = new_data1
				self.ydata2 = new_data2
				return 1

	def read_and_parse(self):
		try: 
			res = self.winterlab.access_serial(2, 'Z')
			if res == -1:
				return [-1]
			data_in1, data_in2 = res
		except TypeError:
			print('TypeError in function read_and_parse')
			return [0]
		except serial.SerialException:
			print('Error: board disconnected.')
			return [-1]
		except:
			sys.excepthook(*sys.exc_info())
		try:
			for batch in [data_in1, data_in2]:
				batch = batch.replace('\r', '')
				batch = batch.replace('\n', '')
		except AttributeError:
			print('AttributeError in function read_and_parse')
			return [0]

		values1 = data_in1.split('.')
		values1 = values1[:-1]
		values2 = data_in2.split('.')
		values2 = values2[:-1]
		return values1, values2


	def update_xview(self, scaleDial, posDial):
		xPlotWidth = scaleDial.value() * settings.DELTA_X
		lpos = posDial.value() * settings.DELTA_X
		rpos = lpos + xPlotWidth
		
		self.xmin = (0.5*(lpos + rpos)) - 0.5*xPlotWidth
		self.xmax = (0.5*(lpos + rpos)) + 0.5*xPlotWidth

	def update_yview(self, scaleDial, posDial, ax):
		yPlotHeight = scaleDial.value()/10.0
		bpos = posDial.value()/10.0 #*some factor for scale
		tpos = bpos + yPlotHeight
		
		if int(ax) == 1:
			self.ymin1 = bpos
			self.ymax1 = tpos
		else:
			self.ymin2 = bpos
			self.ymax2 = tpos

	def pause(self):
		self.running = not self.running
		return self.running

	def checkSaveDirSet(self):
		if not self.saveDirSet:
			return 0
		else:
			return 1

	def setSaveDir(self):
		if not self.checkSaveDirSet():
			self.saveDir = qtw.QFileDialog.getExistingDirectory(self, 'Select directory')
			self.saveDirSet = True
			self.saveDirSetSignal.emit(self.saveDir)
		else:
			return 1

	def save_plot(self):
		date = time.strftime('%Y_%m_%d__%H_%M_%S')
		fig = plt.figure()
		ax1 = fig.add_subplot(111)
		ax1.grid()
		ax1.plot(self.xdata, self.ydata1, label='Ch.1', color='b')
		ax1.set_xlim(self.xmin, self.xmax)
		ax1.set_ylim(self.ymin1, self.ymax1)
		ax2 = ax1.twinx()
		ax2.plot(self.xdata, self.ydata2, label='Ch.2', color='g')
		ax2.set_xlim(self.xmin, self.xmax)
		ax2.set_ylim(self.ymin2, self.ymax2)
		fig.legend()
		fig.tight_layout()

		x_div_text = ax1.text(0.02, 0.05, '', transform=self.ax1.transAxes)
		y1_div_text = ax1.text(0.4, 0.05, '', transform=self.ax1.transAxes)
		y2_div_text = ax1.text(0.75, 0.05, '', transform=self.ax1.transAxes)

		x_div_text.set_text('x: ' + str(round(((self.xmax - self.xmin)*1e6/5.0), 3)) + ' us/div')
		y1_div_text.set_text('Ch1: ' + str(round(((self.ymax1 - self.ymin1)/5.0), 3)) + ' V/div')
		y2_div_text.set_text('Ch2: ' + str(round(((self.ymax2 - self.ymin2)/5.0), 3)) + ' V/div')

		ax1.tick_params(axis='x', colors='white')
		ax1.tick_params(axis='y', colors='white')
		ax2.tick_params(axis='y', colors='white')

		if not self.saveDirSet:
			path = qtw.QFileDialog.getSaveFileName(self, 'Save file', '../../', filter='CSV(*.csv)')
			if all(path):
				self.saveDirSet = True
				dissected_path = path[0].split('/')
				self.saveFileName = dissected_path[-1]
				self.saveDir = ''
				for i in dissected_path[1:-1]:
					self.saveDir = self.saveDir + '/' + i
			else:
				return 1
		else:
			self.saveFileName, ok = qtw.QInputDialog.getText(self, 'Choose file name', 'File name: ', qtw.QLineEdit.Normal, '')
			if not ok:
				return 1

		try:
			if self.saveFileName == '':
				fullsavename = self.saveDir + '/' + date
			else:
				fullsavename = self.saveDir + '/' + self.saveFileName
			fig.savefig(fullsavename + '.png')
			savedata = zip(self.xdata, self.ydata1, self.ydata2)
			with open(fullsavename+'.csv', 'w') as f:
				writer = csv.writer(f)
				writer.writerows(savedata)
			return 0
		except:
			sys.excepthook(*sys.exc_info())
			return 1

	def get_range(self):
		ch1_min = min(self.ydata1)
		ch1_max = max(self.ydata1)
		ch2_min = min(self.ydata2)
		ch2_max = max(self.ydata2)
		ch1_range = ch1_max - ch1_min
		ch2_range = ch2_max - ch2_min
		value_string = str(ch1_range) + ' ' + str(ch2_range)
		return ch1_range, ch2_range