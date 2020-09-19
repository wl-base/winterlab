import sys
import serial
import serial.tools.list_ports
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

import settings

sys._excepthook = sys.excepthook
sys.excepthook = settings.custom_excepthook

class SweepDialog(qtw.QDialog):
	gotValues = qtc.pyqtSignal(str)
	def __init__(self):
		qtw.QDialog.__init__(self)
		
		masterboxLayout = qtw.QVBoxLayout()
		hboxLayout = qtw.QHBoxLayout()
		labelLayout = qtw.QVBoxLayout()
		entryLayout = qtw.QVBoxLayout()
		unitsLayout = qtw.QVBoxLayout()
		typeLayout = qtw.QHBoxLayout()
		buttonLayout = qtw.QHBoxLayout()

		masterboxLayout.addLayout(hboxLayout)
		hboxLayout.addLayout(labelLayout)
		hboxLayout.addLayout(entryLayout)
		hboxLayout.addLayout(unitsLayout)
		masterboxLayout.addLayout(typeLayout)
		masterboxLayout.addLayout(buttonLayout)

		startFreqLabel = qtw.QLabel('Start frequency: ')
		startFreqLabelUnits = qtw.QLabel(' kHz')
		stopFreqLabel = qtw.QLabel('Stop frequency: ')
		stopFreqLabelUnits = qtw.QLabel(' kHz')
		numStepsLabel = qtw.QLabel('Steps: ')
		numStepsUnits = qtw.QLabel(' ')
		typeLabel = qtw.QLabel('type')
		self.startFreqEntry = qtw.QLineEdit()
		self.stopFreqEntry = qtw.QLineEdit()
		self.numStepsEntry = qtw.QLineEdit()
		self.rlin = qtw.QRadioButton('Lin.')
		self.rlog = qtw.QRadioButton('Log.')
		goButton = qtw.QPushButton('Go')
		cancelButton = qtw.QPushButton('Cancel')
		self.statusLabel = qtw.QLabel('Note: rounds DOWN to nearest 1kHz.')

		labelLayout.addWidget(startFreqLabel)
		labelLayout.addWidget(stopFreqLabel)
		#labelLayout.addWidget(numStepsLabel)
		entryLayout.addWidget(self.startFreqEntry)
		entryLayout.addWidget(self.stopFreqEntry)
		#entryLayout.addWidget(self.numStepsEntry)
		unitsLayout.addWidget(startFreqLabelUnits)
		unitsLayout.addWidget(stopFreqLabelUnits)
		#unitsLayout.addWidget(numStepsUnits)
		# typeLayout.addWidget(self.rlin)
		# typeLayout.addWidget(self.rlog)
		buttonLayout.addWidget(cancelButton)
		buttonLayout.addWidget(goButton)
		masterboxLayout.addWidget(self.statusLabel)

		self.rlin.setChecked(True)
		goButton.clicked.connect(self.collect_values)
		goButton.setDefault(True)
		cancelButton.clicked.connect(self.close)

		self.setLayout(masterboxLayout)
		self.resize(self.sizeHint())

	def collect_values(self):
		start = int(float(self.startFreqEntry.text()))
		stop = int(float(self.stopFreqEntry.text()))
		print(start)
		print(stop)
		# numSteps = self.numStepsEntry.text()
		numSteps = float(stop) - float(start) + 1
		if self.rlin.isChecked():
			stype = 'lin'
		else:
			stype = 'log'
		if start != '' and stop != '':
			if start < stop:
				if start < 1 or stop < 1:
					print('too low')
					self.statusLabel.setText('Error: frequency out of bounds.')
				elif start > settings.MAX_FREQ/1000.0 or stop > settings.MAX_FREQ/1000.0:
					print('too high')
					self.statusLabel.setText('Error: frequency out of bounds.')
				else:
				# if float(start) > MAX_FREQ/1000.0 or float(stop) > MAX_FREQ/1000.0 or float(start) < 1 or float(stop) < 1:
					self.statusLabel.setText(' ')
					value_string = str(start) + ' ' + str(stop) + ' ' +stype+' '+str(numSteps)
					self.send_values(value_string)
			else:
				self.statusLabel.setText('Error: start freq. must be \nless than stop freq.')
			
				
		else:
			self.statusLabel.setText('Error: value missing.')

	def send_values(self, value_string):
		self.gotValues.emit(value_string)
		self.close()