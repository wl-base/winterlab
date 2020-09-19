import sys
import numpy as np
import math
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import random
import csv
import time
import signal
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg

import settings
from animatedmplcanvas import AnimatedMplCanvas
from plotter import PlotterObj
from sendrecv import SendRecvObj
from sender import SenderObj
from sweepdialog import SweepDialog

sys._excepthook = sys.excepthook
sys.excepthook = settings.custom_excepthook

class GUI(qtw.QWidget):

	send_signal = qtc.pyqtSignal(str)
	sr_out_signal = qtc.pyqtSignal(str)

	def __init__(self):
		qtw.QWidget.__init__(self)
		self.setAttribute(qtc.Qt.WA_DeleteOnClose)
		self.setWindowTitle('WinterLab')
		signal.signal(signal.SIGINT, self.sigquit_handler)
		signal.signal(signal.SIGTERM, self.sigquit_handler)	
		self.scope_display = AnimatedMplCanvas()
	

		'''
		Define default values
		'''
		self.freq = 1000 # sic
		self.newFreq = self.freq
		self.M = 1 # tuning word

		self.amp = 2.0
		self.newAmp = self.amp

		self.offset = 0.0
		self.newOffset = self.offset

		self.DC = 0.0
		self.newDC = self.DC

		'''
		Scope widgets
		'''
		mainLayout = qtw.QGridLayout()

		# TODO: finish implementing drop-down menus + functions
		# self.menuFrame = self.qtFrame(mainLayout, qtw.QFrame.StyledPanel, row=0, column)
		self.topMenu = qtw.QMenuBar()
		self.file_menu = self.topMenu.addMenu('File')
		self.setSaveDirAction = qtw.QAction('Set save directory')
		self.setSaveDirAction.triggered.connect(self.scope_display.setSaveDir)
		self.file_menu.addAction(self.setSaveDirAction)
		self.scope_display.saveDirSetSignal.connect(self.scope_display.setSaveDir)
		# mainLayout.addWidget(self.topMenu, 0, 0)

		self.scopeFrame = self.qtFrame(mainLayout, qtw.QFrame.StyledPanel, row=1, column=0)
		scopeLayout = qtw.QHBoxLayout(self.scopeFrame)

		scopeLayout.addWidget(self.scope_display)

		scopeGraphLayout = qtw.QVBoxLayout()
		scopeLayout.addLayout(scopeGraphLayout)

		self.scopeButtonsFrame = self.qtFrame(scopeLayout, qtw.QFrame.StyledPanel)
		scopeButtonsLayout = qtw.QVBoxLayout(self.scopeButtonsFrame)

		self.scopeVertFrame = self.qtFrame(scopeLayout, qtw.QFrame.StyledPanel)
		scopeVertLayout = qtw.QHBoxLayout(self.scopeVertFrame)

		scopeVert1Layout = qtw.QVBoxLayout()
		scopeVertLayout.addLayout(scopeVert1Layout)

		scopeVert2Layout = qtw.QVBoxLayout()
		scopeVertLayout.addLayout(scopeVert2Layout)

		self.scopeHorizFrame = self.qtFrame(scopeLayout, qtw.QFrame.StyledPanel)
		scopeHorizLayout = qtw.QVBoxLayout(self.scopeHorizFrame)

		self.scopeTrigFrame = self.qtFrame(scopeLayout, qtw.QFrame.StyledPanel)
		scopeTrigLayout = qtw.QVBoxLayout(self.scopeTrigFrame)

		self.runButton = self.qtButton(scopeButtonsLayout, 'Run/Pause', self.runButtonPress, checkable=True)
		self.saveButton = self.qtButton(scopeButtonsLayout, 'Save', self.saveButtonPress)
		self.saveStatLabel = self.qtLabel(scopeButtonsLayout, '')
		self.saveSweepButton = self.qtButton(scopeButtonsLayout, 'Save Sweep', self.saveSweepPress)
		self.quitButton = self.qtButton(scopeButtonsLayout, 'Quit', self.closeEventButton)

		self.xSectionLabel = self.qtLabel(scopeHorizLayout, 'Horizontal')
		self.xPanDial = self.qtDial(scopeHorizLayout, 'Position', 
			lambda: self.scope_display.update_xview(self.xScaleDial, self.xPanDial),
			0, 3*settings.VIEW_LEN/4, interval=5)
		self.xScaleDial = self.qtDial(scopeHorizLayout, 'Scale\n(S/DIV)', 
			lambda: self.scope_display.update_xview(self.xScaleDial, self.xPanDial),
			0, settings.VIEW_LEN, interval=5)

		self.scopeVert1Widget = qtw.QWidget()
		self.scopeVert2Widget = qtw.QWidget()

		self.y1SectionLabel = self.qtLabel(scopeVert1Layout, 'Ch1')
		self.y1PanDial = self.qtDial(scopeVert1Layout, 'Position', 
			lambda: self.scope_display.update_yview(self.y1ScaleDial, self.y1PanDial, 1),
			-50, 50, interval=0.1)
		self.y1ScaleDial = self.qtDial(scopeVert1Layout, 'Scale\n(V/DIV)', 
			lambda: self.scope_display.update_yview(self.y1ScaleDial, self.y1PanDial, 1),
			10, 100, interval=0.5)
		self.y2SectionLabel = self.qtLabel(scopeVert2Layout, 'Ch2')
		self.y2PanDial = self.qtDial(scopeVert2Layout, 'Position',
			lambda: self.scope_display.update_yview(self.y2ScaleDial, self.y2PanDial, 2),
			-50, 50, interval=0.5)
		self.y2ScaleDial = self.qtDial(scopeVert2Layout, 'Scale\n(V/DIV)',
			lambda: self.scope_display.update_yview(self.y2ScaleDial, self.y2PanDial, 2),
			10, 100, interval=0.5)

		self.trigLabel = self.qtLabel(scopeTrigLayout, 'Trigger')
		self.trigBtnGroup = qtw.QButtonGroup()
		self.trigCh1Btn = self.qtButton(scopeTrigLayout, 'Ch1', function=lambda: self.setTrigChannel(1), checkable=True, group=self.trigBtnGroup)
		self.trigCh1Btn.setChecked(True)
		self.trigCh2Btn = self.qtButton(scopeTrigLayout, 'Ch2', function=lambda: self.setTrigChannel(0), checkable=True, group=self.trigBtnGroup)
		self.trigDial = self.qtDial(scopeTrigLayout, 'Level', function=self.setTrig, llim=0, ulim=255)
		self.trigDial.sliderReleased.connect(self.sendTrig)


		'''
		Function Generator
		'''

		self.fgFrame = self.qtFrame(mainLayout, qtw.QFrame.StyledPanel, row=2, column=0)
		fgLayout = qtw.QHBoxLayout(self.fgFrame)

		self.waveButtons = qtw.QButtonGroup()
		self.waveBtnFrame = self.qtFrame(fgLayout, qtw.QFrame.StyledPanel)
		fgButtonGrid = qtw.QGridLayout(self.waveBtnFrame)
		self.sineButton = self.qtButton(fgButtonGrid, 'Sine', lambda: self.sendWaveSelect('S'), 0, 0, checkable=True, group=self.waveButtons)
		self.squareButton = self.qtButton(fgButtonGrid, 'Square', lambda: self.sendWaveSelect('Q'), 0, 1, checkable=True, group=self.waveButtons)
		self.triButton = self.qtButton(fgButtonGrid, 'Triangle', lambda: self.sendWaveSelect('R'), 1, 0, checkable=True, group=self.waveButtons)
		self.sawButton = self.qtButton(fgButtonGrid, 'Sawtooth', lambda: self.sendWaveSelect('U'), 1, 1, checkable=True, group=self.waveButtons)
		self.noiseButton = self.qtButton(fgButtonGrid, 'Noise', lambda: self.sendWaveSelect('W'), 2, 0, checkable=True, group=self.waveButtons)
		self.flatButton = self.qtButton(fgButtonGrid, 'Flat', lambda: self.sendWaveSelect('B'), 2, 1, checkable=True, group=self.waveButtons)
		self.flatButton.setChecked(True)

		self.freqFrame = self.qtFrame(fgLayout, qtw.QFrame.StyledPanel)
		fgFreqLayout = qtw.QGridLayout(self.freqFrame)
		self.freqCurrentName = self.qtLabel(fgFreqLayout, 'Freq.: ', 0, 0)
		self.freqCurrentDisplay = self.qtLabel(fgFreqLayout, self.freq, 0, 1)
		self.freqCurrentUnits = self.qtLabel(fgFreqLayout, ' Hz', 0, 2)
		self.freqEntryBox = qtw.QLineEdit()
		fgFreqLayout.addWidget(self.freqEntryBox, 1, 1)
		self.freqEntryBox.returnPressed.connect(self.setFreqBox)
		self.freqEntryBoxBtn = self.qtButton(fgFreqLayout, 'Set', self.setFreqBox, 1, 2)
		self.freqNewDisplay = self.qtLabel(fgFreqLayout, '', 2, 1)
		self.freqUpButton = self.qtButton(fgFreqLayout, '+', lambda: self.incFreq(0), 3, 0)
		self.freqDownButton = self.qtButton(fgFreqLayout, '-', lambda: self.incFreq(1), 3, 1)
		self.freqSetButton = self.qtButton(fgFreqLayout, 'Set', self.setFreq, 3, 2)
		
		self.ampFrame = self.qtFrame(fgLayout, qtw.QFrame.StyledPanel)
		fgAmpLayout = qtw.QGridLayout(self.ampFrame)
		self.ampCurrentName = self.qtLabel(fgAmpLayout, 'Amp.: ', 0, 0)
		self.ampCurrentDisplay = self.qtLabel(fgAmpLayout, self.amp, 0, 1)
		self.ampCurrentUnits = self.qtLabel(fgAmpLayout, ' V', 0, 2)
		self.ampEntryBox = qtw.QLineEdit()
		fgAmpLayout.addWidget(self.ampEntryBox, 1, 1)
		self.ampEntryBox.returnPressed.connect(self.setAmpBox)
		self.ampEntryBoxBtn = self.qtButton(fgAmpLayout, 'Set', self.setAmpBox, 1, 2)
		self.ampNewDisplay = self.qtLabel(fgAmpLayout, '', 2, 1)
		self.ampUpButton = self.qtButton(fgAmpLayout, '+', lambda: self.incAmp(0), 3, 0)
		self.ampDownButton = self.qtButton(fgAmpLayout, '-', lambda: self.incAmp(1), 3, 1)
		self.ampSetButton = self.qtButton(fgAmpLayout, 'Set', self.setAmp, 3, 2)
		
		self.offsetFrame = self.qtFrame(fgLayout, qtw.QFrame.StyledPanel)
		fgOffsetLayout = qtw.QGridLayout(self.offsetFrame)
		self.offsetCurrentName = self.qtLabel(fgOffsetLayout, 'Offset: ', 0, 0)
		self.offsetCurrentDisplay = self.qtLabel(fgOffsetLayout, self.offset, 0, 1)
		self.offsetCurrentUnits = self.qtLabel(fgOffsetLayout, ' V', 0, 2)
		self.offsetEntryBox = qtw.QLineEdit()
		fgOffsetLayout.addWidget(self.offsetEntryBox, 1, 1)
		self.offsetEntryBox.returnPressed.connect(self.setOffsetBox)
		self.offsetEntryBoxBtn = self.qtButton(fgOffsetLayout, 'Set', self.setOffsetBox, 1, 2)
		self.offsetNewDisplay = self.qtLabel(fgOffsetLayout, '', 2, 1)
		self.offsetUpButton = self.qtButton(fgOffsetLayout, '+', lambda: self.incOffset(0), 3, 0)
		self.offsetDownButton = self.qtButton(fgOffsetLayout, '-', lambda: self.incOffset(1), 3, 1)
		self.offsetSetButton = self.qtButton(fgOffsetLayout, 'Set', self.setOffset, 3, 2)

		'''
		MultiMeter
		'''

		self.mmFrame = self.qtFrame(mainLayout, qtw.QFrame.StyledPanel, row=3, column=0)
		mmLayout = qtw.QHBoxLayout(self.mmFrame)

		mmVMLayout = qtw.QVBoxLayout()
		mmLayout.addLayout(mmVMLayout)

		mmCMLayout = qtw.QVBoxLayout()
		mmLayout.addLayout(mmCMLayout)

		mmRMLayout = qtw.QVBoxLayout()
		mmLayout.addLayout(mmRMLayout)

		self.VMLabel = self.qtLabel(mmVMLayout, 'Voltage')
		self.VMDisplay = self.qtLabel(mmVMLayout, '--')
		self.VMButton = self.qtButton(mmVMLayout, 'Measure', self.VMMeasure)

		self.CMLabel = self.qtLabel(mmCMLayout, 'Capacitance')
		self.CMDisplay = self.qtLabel(mmCMLayout, '--')
		self.CMButton = self.qtButton(mmCMLayout, 'Measure', self.CMMeasure)

		self.RMLabel = self.qtLabel(mmRMLayout, 'Resistance')
		self.RMDisplay = self.qtLabel(mmRMLayout, '--')
		self.RMButton = self.qtButton(mmRMLayout, 'Measure', self.RMMeasure)

		self.rangeFrame = self.qtFrame(mmLayout, qtw.QFrame.StyledPanel)
		mmRangeLayout = qtw.QHBoxLayout(self.rangeFrame)
		self.rangeLabel = self.qtLabel(mmRangeLayout, 'Select range: ')
		self.rangeBtnGroup = qtw.QButtonGroup()
		self.range100Btn = self.qtButton(mmRangeLayout, '100', function=lambda: self.setRange(2), checkable=True, group=self.rangeBtnGroup)
		self.range1kBtn = self.qtButton(mmRangeLayout, '1k', function=lambda: self.setRange(3), checkable=True, group=self.rangeBtnGroup)
		self.range10kBtn = self.qtButton(mmRangeLayout, '10k', function=lambda: self.setRange(4), checkable=True, group=self.rangeBtnGroup)
		self.range100kBtn = self.qtButton(mmRangeLayout, '100k', function=lambda: self.setRange(5), checkable=True, group=self.rangeBtnGroup)
		self.range1MegBtn = self.qtButton(mmRangeLayout, '1M', function=lambda: self.setRange(6), checkable=True, group=self.rangeBtnGroup)

		mmVSLayout = qtw.QVBoxLayout()
		mmLayout.addLayout(mmVSLayout)

		self.VSLabel = self.qtLabel(mmVSLayout, 'DC Supply')
		self.VSDisplayLabel = self.qtLabel(mmVSLayout, 'Output: 0.0 V')
		mmVSEntryLayout = qtw.QHBoxLayout()
		mmVSLayout.addLayout(mmVSEntryLayout)
		self.VSEntryBox = qtw.QLineEdit()
		mmVSEntryLayout.addWidget(self.VSEntryBox)
		self.VSEntryBox.returnPressed.connect(self.setDCBox)
		self.VSEntryBoxBtn = self.qtButton(mmVSEntryLayout, 'Set', self.setDCBox)
		self.VSNewDisplay = self.qtLabel(mmVSLayout, '')
		mmVSBtnLayout = qtw.QHBoxLayout()
		mmVSLayout.addLayout(mmVSBtnLayout)
		self.VSUpBtn = self.qtButton(mmVSBtnLayout, '+', lambda: self.incDC(0))
		self.VSDownBtn = self.qtButton(mmVSBtnLayout, '-', lambda: self.incDC(1))
		self.VSSetBtn = self.qtButton(mmVSBtnLayout, 'Set', self.setDC)

		self.setLayout(mainLayout)
		self.resize(self.sizeHint())
		self.center()

		self.show()

		try:
			self.plotter = PlotterObj(self.scope_display)

			self.plot_thread = qtc.QThread()
			self.send_thread = qtc.QThread()
			self.sr_thread = qtc.QThread()
			
			if not self.scope_display.start_plot():
				self.openDialog('Error', 'WinterLab board not found. Please check connection and try again.')

			else:
				self.scope_display.start_plot()
				self.winterlab = self.scope_display.winterlab 

				self.sender = SenderObj(self.winterlab)
				self.sender.moveToThread(self.send_thread)
				self.send_signal.connect(self.sender.send_str)
				self.send_thread.start()
				self.send_thread.setPriority(qtc.QThread.HighPriority)

				self.send_recver = SendRecvObj(self.winterlab)
				self.send_recver.moveToThread(self.sr_thread)
				self.sr_out_signal.connect(self.send_recver.send_recv)
				self.send_recver.send_done.connect(self.updateVMDisplay)
				self.prev_slot_sr = self.updateVMDisplay # the previous slot that the send-receive thread signalled
				self.sr_thread.start()
				self.send_thread.setPriority(qtc.QThread.HighPriority)

				self.plotter.moveToThread(self.plot_thread)
				self.plotter.ready_to_update.connect(self.scope_display.update_figure)
				self.plot_thread.started.connect(self.plotter.run)
				self.plotter.kill_signal.connect(self.closeOnLostConnection)
				self.plot_thread.start()
		except:
			sys.excepthook(*sys.exc_info())

	def reconnect(self, signal, new, prev):
		signal.disconnect(prev)
		signal.connect(new)
		self.prev_slot_sr = new

	def openDialog(self, title, message):
		dialog = qtw.QDialog()
		label = qtw.QLabel(message)
		dialog.setWindowTitle('Error')
		qbutton = qtw.QPushButton('Quit', dialog)
		qbutton.clicked.connect(self.closeEventButton)
		dialogLayout = qtw.QHBoxLayout()
		dialogLayout.addWidget(label)
		dialogLayout.addWidget(qbutton)
		dialog.setLayout(dialogLayout)
		dialog.setWindowModality(qtc.Qt.ApplicationModal)
		dialog.exec_()

	def unlock_widgets(self, widgets):
		for widget in widgets:
			widget.setEnabled(True)

	def lock_widgets(self, widgets):
		for widget in widgets:
			widget.setEnabled(False)
		
	def setRange(self, val):
		#val = 4
		try:
			self.lock_widgets([self.range100Btn, self.range1kBtn,
				self.range10kBtn, self.range100kBtn, self.range1MegBtn])
			#self.send_signal.emit('H'+str(val))
			self.sr_out_signal.emit('H'+str(val))
			qtc.QTimer.singleShot(500, lambda: self.unlock_widgets([self.range100Btn, 
				self.range1kBtn, self.range10kBtn, self.range100kBtn, self.range1MegBtn]))
		except:
			sys.excepthook(*sys.exc_info())

	def setTrig(self):
		#print(self.trigDial.value())
		self.scope_display.set_trig(self.trigDial.value())

	def sendTrig(self):
		try:
			self.lock_widgets([self.trigDial])
			#self.send_signal.emit('T'+str(self.scope_display.trig))
			self.sr_out_signal.emit('T'+str(self.scope_display.trig))
			qtc.QTimer.singleShot(200, lambda: self.unlock_widgets([self.trigDial]))
		except:
			sys.excepthook(*sys.exc_info())
		
	def setTrigChannel(self, chnum):
		try:
			self.scope_display.trigCh = chnum
			self.lock_widgets([self.trigCh1Btn, self.trigCh2Btn])
			#self.send_signal.emit('C'+str(self.scope_display.trigCh))
			self.sr_out_signal.emit('C'+str(self.scope_display.trigCh))
			qtc.QTimer.singleShot(500, lambda: self.unlock_widgets([self.trigCh1Btn, self.trigCh2Btn]))
		except:
			sys.excepthook(*sys.exc_info())

	def VMMeasure(self):
		try:
			self.lock_widgets([self.VMButton])
			self.sr_out_signal.emit('M')
			self.reconnect(self.send_recver.send_done, self.updateVMDisplay, self.prev_slot_sr)
			self.unlock_widgets([self.VMButton])
		except:
			
			sys.excepthook(*sys.exc_info())

	def updateVMDisplay(self, value):
		if value == 255 or value == 0:
			self.VMDisplay.setText('RAIL')
		else:
			#self.VMDisplay.setText(str(round((-9.3/255.)*value + 4.7, 2)))
			self.VMDisplay.setText(str(round((-1.0/25.6)*(value - 129), 2)) + ' V')
		self.unlock_widgets([self.VMButton])

	def CMMeasure(self):
		try:
			self.lock_widgets([self.CMButton])
			self.sr_out_signal.emit('I')
			self.reconnect(self.send_recver.send_done, self.updateCMDisplay, self.prev_slot_sr)
			self.unlock_widgets([self.CMButton])
		except:
			self.unlock_widgets([self.CMButton])
			sys.excepthook(*sys.exc_info())

	def updateCMDisplay(self, value):
		if value < 0:
			self.CMDisplay.setText('RANGE')
		else:
			self.CMDisplay.setText(str(value) + 'uF')
		self.unlock_widgets([self.CMButton])
		
	def RMMeasure(self):
		try:
			self.lock_widgets([self.RMButton])
			self.sr_out_signal.emit('O')
			self.reconnect(self.send_recver.send_done, self.updateRMDisplay, self.prev_slot_sr)
			self.unlock_widgets([self.RMButton])
		except:
			self.unlock_widgets([self.RMButton])
			sys.excepthook(*sys.exc_info())


	def updateRMDisplay(self, value):
		if value < 0:
			self.RMDisplay.setText('RANGE')
		else:
			self.RMDisplay.setText(str(value) + ' ohms')
		self.unlock_widgets([self.RMButton])
		
	def sendWaveSelect(self, wave):
		try:
			#self.send_signal.emit(wave)
			#self.send_signal.emit(wave)
			self.sr_out_signal.emit(wave)
			self.lock_widgets([self.sineButton, self.squareButton, 
				self.triButton, self.sawButton, self.flatButton, self.noiseButton])

			qtc.QTimer.singleShot(200, lambda: self.unlock_widgets([self.sineButton, self.squareButton, 
				self.triButton, self.sawButton, self.flatButton, self.noiseButton]))
		except:
			#self.handleSerialTimeout()
			sys.excepthook(*sys.exc_info())
		
	def incFreq(self, updown):
		if updown == 0: # up
			# self.M = self.M + 1

			self.newFreq = self.newFreq + 1000
			if self.newFreq > settings.MAX_FREQ:
				self.newFreq = settings.MAX_FREQ
		elif updown == 1:
			self.newFreq = self.newFreq - 1000
			if self.newFreq < 0:
				self.newFreq = 0
			# self.M = self.M - 1
			# if self.M <= 1:
			# 	self.M = 1
		else:
			print('Invalid increment/decrement.')

		#self.newFreq = int(F_CLK / (WTABLELEN / self.M))
		self.freqNewDisplay.setText(str(round(self.newFreq, 1)))

	# TODO: update frequency displays
	def setFreq(self):
		try:
			self.lock_widgets([self.freqSetButton])
			self.sr_out_signal.emit('F'+str(self.newFreq))
			self.freq = self.newFreq
			qtc.QTimer.singleShot(10, lambda: self.freqCurrentDisplay.setText(str(round(self.freq, 1))))
			qtc.QTimer.singleShot(200, lambda: self.unlock_widgets([self.freqSetButton]))
		except ValueError:
			return
		except:
			sys.excepthook(*sys.exc_info())

	def setFreqBox(self):
		try:
			self.lock_widgets([self.freqSetButton])
			freq = math.ceil(int(self.freqEntryBox.text())/1000.0) * 1000.
			if freq > 0 and freq < settings.MAX_FREQ:
				self.newFreq = freq
				qtc.QTimer.singleShot(10, lambda: self.freqNewDisplay.setText(''))
			else:
				self.freqNewDisplay.setText('LIMIT')
				qtc.QTimer.singleShot(1000, lambda: self.freqNewDisplay.setText(''))
				return
			#self.send_signal.emit('F'+str(self.newFreq))
			self.sr_out_signal.emit('F'+str(self.newFreq))
			self.freq = self.newFreq
			
		except ValueError:
			pass
		except:
			sys.excepthook(*sys.exc_info())
		qtc.QTimer.singleShot(10, lambda: self.freqCurrentDisplay.setText(str(round(self.freq, 1))))
		
		qtc.QTimer.singleShot(200, lambda: self.unlock_widgets([self.freqSetButton]))
		
	def incAmp(self, updown):
		if updown == 0: # up
			self.newAmp = self.newAmp + 0.1
			if self.newAmp > settings.MAX_AMP:
				self.newAmp = settings.MAX_AMP
		else:
			self.newAmp = self.newAmp - 0.1
			if self.newAmp < settings.MIN_AMP:
				self.newAmp = settings.MIN_AMP
		self.ampNewDisplay.setText(str(round(self.newAmp, 1)))

	def setAmpBox(self):
		try:
			self.lock_widgets([self.ampSetButton])
			amp = float(self.ampEntryBox.text())
			if amp > 0 and amp < settings.MAX_AMP:
				self.newAmp = amp
				qtc.QTimer.singleShot(10, lambda: self.ampNewDisplay.setText(''))
			else:
				self.ampNewDisplay.setText('LIMIT')
				qtc.QTimer.singleShot(1000, lambda: self.ampNewDisplay.setText(''))
				return
			self.sr_out_signal.emit('A'+str(round((4095.0/9.75)*self.newAmp)))
			self.amp = self.newAmp

		except ValueError:
			pass
		except:
			sys.excepthook(*sys.exc_info())
		qtc.QTimer.singleShot(10, lambda: self.ampCurrentDisplay.setText(str(round(self.amp,1))))
		qtc.QTimer.singleShot(200, lambda: self.unlock_widgets([self.ampSetButton]))

	def setAmp(self):
		try:
			self.lock_widgets([self.ampSetButton])
			self.sr_out_signal.emit('A'+str(round((4095.0/9.75)*self.newAmp)))
			self.amp = self.newAmp

			qtc.QTimer.singleShot(10, lambda: self.ampCurrentDisplay.setText(str(round(self.amp,1))))
			qtc.QTimer.singleShot(200, lambda: self.unlock_widgets([self.ampSetButton]))
		except:
			sys.excepthook(*sys.exc_info())

	def incOffset(self, updown):
		if updown == 0: # up
			self.newOffset = self.newOffset + 0.1
			if self.newOffset > settings.MAX_OFFSET:
				self.newOffset = settings.MAX_OFFSET
		else:
			self.newOffset = self.newOffset - 0.1
			if self.newOffset < settings.MIN_OFFSET:
				self.newOffset = settings.MIN_OFFSET
		self.offsetNewDisplay.setText(str(round(self.newOffset, 1)))

	def setOffset(self):
		try:
			self.lock_widgets([self.offsetSetButton])
			#self.send_signal.emit('D'+str(self.newOffset))
			self.sr_out_signal.emit('D'+str(round((-409.5*self.newOffset + 2047))))
			self.offset = self.newOffset
			qtc.QTimer.singleShot(10, lambda: self.offsetCurrentDisplay.setText(str(round(self.offset,1))))
			qtc.QTimer.singleShot(10, lambda: self.offsetNewDisplay.setText(''))
			qtc.QTimer.singleShot(200, lambda: self.unlock_widgets([self.offsetSetButton]))
		except:
			sys.excepthook(*sys.exc_info())

	def setOffsetBox(self):
		try:
			self.lock_widgets([self.offsetSetButton])
			offset = float(self.offsetEntryBox.text())
			if offset < settings.MAX_OFFSET and offset > settings.MIN_OFFSET:
				self.newOffset = offset
				qtc.QTimer.singleShot(10, lambda: self.offsetNewDisplay.setText(''))
			else:
				self.offsetNewDisplay.setText('LIMIT')
				qtc.QTimer.singleShot(1000, lambda: self.offsetNewDisplay.setText(''))
				return
			self.sr_out_signal.emit('D'+str(round((-409.5*self.newOffset + 2047))))
			self.offset = self.newOffset
			
		except ValueError:
			pass
		except:
			sys.excepthook(*sys.exc_info())
		qtc.QTimer.singleShot(10, lambda: self.offsetCurrentDisplay.setText(str(round(self.offset,1))))
		qtc.QTimer.singleShot(200, lambda: self.unlock_widgets([self.offsetSetButton]))

	def incDC(self, updown):
		if updown == 0:
			self.newDC = self.newDC + 0.1
			if self.newDC > settings.MAX_DC:
				self.newDC = settings.MAX_DC
		else:
			self.newDC = self.newDC - 0.1
			if self.newDC < settings.MIN_DC:
				self.newDC = settings.MIN_DC
		self.VSNewDisplay.setText(str(round(self.newDC,1)))

	def setDC(self):
		try:
			self.lock_widgets([self.VSSetBtn])
			self.sr_out_signal.emit('J'+str(round(-25.6*self.newDC + 128)))
			self.DC = self.newDC
			qtc.QTimer.singleShot(10, lambda: self.VSDisplayLabel.setText('Output: ' + str(round(self.DC, 1)) + ' V'))
			qtc.QTimer.singleShot(10, lambda: self.VSNewDisplay.setText(''))
			qtc.QTimer.singleShot(200, lambda: self.unlock_widgets([self.VSSetBtn]))
		except:
			sys.excepthook(*sys.exc_info())

	def setDCBox(self):
		try:
			self.lock_widgets([self.VSEntryBoxBtn])
			dc = float(self.VSEntryBox.text())
			if dc <= settings.MAX_DC and dc >= settings.MIN_DC:
				self.newDC = dc
				qtc.QTimer.singleShot(10, lambda: self.VSNewDisplay.setText(''))
			
			else:
				self.VSNewDisplay.setText('LIMIT')
				qtc.QTimer.singleShot(1000, lambda: self.VSNewDisplay.setText(''))
				return
			self.sr_out_signal.emit('J'+str(round(-25.6*self.newDC + 128)))
			self.DC = self.newDC
			qtc.QTimer.singleShot(10, lambda: self.VSDisplayLabel.setText('Output: ' + str(round(self.DC, 1)) + ' V'))
			qtc.QTimer.singleShot(200, lambda: self.unlock_widgets([self.VSEntryBoxBtn]))
		except ValueError:
			print('ValueError in function setDCBox')
			qtc.QTimer.singleShot(200, lambda: self.unlock_widgets([self.VSEntryBoxBtn]))
			pass
		except:
			sys.excepthook(*sys.exc_info())

	def saveButtonPress(self):
		if self.scope_display.save_plot() == 0:
			self.saveStatLabel.setText('SAVED')
		else:
			self.saveStatLabel.setText('NOT SAVED')
		qtc.QTimer.singleShot(3000, lambda:self.saveStatLabel.setText(''))

	def saveSweepPress(self):
		print('opening new sweep window')
		sweepwindow = SweepDialog()
		sweepwindow.gotValues.connect(self.doSweep)
		sweepwindow.exec_()
		sweepwindow.show()

	def doSweep(self, value_string): # TODO check range is not out of bounds
		try:
			start = float(value_string.split()[0])
			stop = float(value_string.split()[1])
			numSteps = float(value_string.split()[3])
		except:
			print('Invalid frequency in sweep range.')
			return
		# try:
			#stype = value_string.split()[2]
		stype = 'lin'
		if stype == 'lin':
			srange = np.linspace(start, stop, numSteps)
		elif stype == 'log':
			srange = np.logspace(start, stop, numSteps)
		else:
			print('Invalid sweep type chosen.')
			return
		self.ch1_range = []
		self.ch2_range = [] # TODO lock rest of gui?
		self.sweepindex = 0
		self.sweeptimer = qtc.QTimer(self)
		self.sweeptimer.setInterval(3000)
		self.sweeptimer.timeout.connect(lambda: self.sweepMeasure(srange))
		self.sweeptimer.start()

	# TODO: get working with savefiledirectory
	def sweepFinish(self, srange):
		self.sweepindex = 0
		srange = [f*1000 for f in srange]
		savedata = zip(srange, self.ch1_range[1:], self.ch2_range[1:])
		date = time.strftime('%Y_%m_%d__%H_%M_%S')
		# if not self.scope_display.checkSaveDirSet():
		# 	self.scope_display.setSaveDir()
		# # if not self.scope_display.saveDirSet:
		# # 	self.scope_display.setSaveDir
		# saveDir = self.scope_display.saveDir
		# # print(srange)
		# try:
		# 	with open(saveDir + 'SWEEP_' + str(int(min(srange)/1000.0)) + 'kHz_' + str(int(max(srange)/1000.0)) + 'kHz_' + date + '.csv', 'w') as f:
		# 		writer = csv.writer(f)
		# 		writer.writerows(savedata)
		# 		self.saveStatLabel.setText('Saved')
		# 		qtc.QTimer.singleShot(3000, lambda: self.saveStatLabel.setText(' '))
		# except:
		# 	self.saveStatLabel.setText('Save failed')
		# 	qtc.QTimer.singleShot(3000, lambda: self.saveStatLabel.setText(' '))
		# 	sys.excepthook(*sys.exc_info())
		saveFileName = qtw.QFileDialog.getSaveFileName(self, 'Save file:')
		try:
			with open(saveFileName[0]+'.csv', 'w') as f:
				writer = csv.writer(f)
				writer.writerows(savedata)
				self.saveStatLabel.setText('Saved')
				qtc.QTimer.singleShot(3000, lambda: self.saveStatLabel.setText(' '))
		except:
			self.saveStatLabel.setText('Save failed')
			qtc.QTimer.singleShot(3000, lambda: self.saveStatLabel.setText(' '))
			sys.excepthook(*sys.exc_info())


	def sweepChangeFreq(self, freq):
		self.newFreq = freq
		self.sweepindex += 1
		self.setFreq()

	def sweepMeasure(self, srange):
		res = self.scope_display.get_range()
		self.ch1_range.append("%2.3f" % res[0])
		self.ch2_range.append("%2.3f" % res[1])
		if self.sweepindex < len(srange):
			self.sweepChangeFreq(int(srange[self.sweepindex]*1000.0)) #then throw away the first entry
		else:
			self.sweeptimer.stop()
			self.sweepFinish(srange)

	def runButtonPress(self): 
		self.scope_display.pause()

	def updateRunBtn(self):
		if self.scope_display.running:
			self.runButton.setText('Pause')
		else:
			self.runButton.setText('Run')
		
	def about(self):
		qtw.QMessageBox.about(self, 'About', 
			'WinterLab board user interface.')

	def center(self):
		qr = self.frameGeometry()
		cp = qtw.QDesktopWidget().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def qtButton(self, layout, text, function=None, row=None, column=None, checkable=False, group=None):
		button = qtw.QPushButton(str(text))
		if group is not None:
			group.addButton(button)
		button.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
		if function is not None:
			button.clicked.connect(function, qtc.Qt.QueuedConnection)
		button.setCheckable(checkable)
		if row is None:
			layout.addWidget(button)
		else:
			layout.addWidget(button, row, column)
		return button

	def qtDial(self, layout, text, function=None, llim=0, ulim=100, interval=1, startpoint=None, row=None, column=None, label_pos=None, padding=None, notches_visible=True):
		dial = qtw.QDial()
		dial.setMinimum(llim)
		dial.setMaximum(ulim)
		dial.setValue(0.5 * (llim + ulim))
		dial.setNotchesVisible(notches_visible)
		dial.notchSize = interval
		dial.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
		if function is not None:
			dial.valueChanged.connect(function)		
		label = qtw.QLabel()
		label.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
		label.setAlignment(qtc.Qt.AlignCenter)
		label.setText(str(text))
		layout.addWidget(dial)
		layout.addWidget(label)
		return dial

	def qtLabel(self, layout, text, row=None, column=None):
		label = qtw.QLabel()
		# label.setUpdatesEnabled(True)
		label.setText(str(text))
		label.setAlignment(qtc.Qt.AlignCenter)
		label.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Expanding)
		if row is not None:
			layout.addWidget(label, row, column)
		else:
			layout.addWidget(label)
		return label

	def qtFrame(self, parentlayout, shape=None, style=None, row=None, column=None):
		frame = qtw.QFrame()
		frame.setFrameShape(shape)
		if row is not None:
			parentlayout.addWidget(frame, row, column)
		else:
			parentlayout.addWidget(frame)
		return frame

	def closeEvent(self, event):
		print('Exiting')
		sys.exit(0)
		# reply = qtw.QMessageBox.question(self, 'Message', 'Are you sure you want to quit?',
		# 	qtw.QMessageBox.Yes | qtw.QMessageBox.No, qtw.QMessageBox.No)
		# if reply == qtw.QMessageBox.Yes:
		# 	sys.exit(0)
		# else:
		# 	return

	def closeOnLostConnection(self):
		print('Exiting')
		sys.exit(1)

	def closeEventButton(self, event):
		print('Exiting')
		sys.exit(0)
		# reply = qtw.QMessageBox.question(self, 'Message', 'Are you sure you want to quit?',
		# 	qtw.QMessageBox.Yes | qtw.QMessageBox.No, qtw.QMessageBox.No)
		# if reply == qtw.QMessageBox.Yes:
		# 	event.accept()
		# else:
		# 	event.ignore()

	def handleSerialTimeout(self):
		print('Serial timed out. Please reconnect.')
		exit()

	def sigquit_handler(self, signal, frame):
		print('Sig quitting')
		sys.exit(0)
