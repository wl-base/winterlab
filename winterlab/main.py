import sys
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg

from gui import GUI
import settings




if __name__ == '__main__':
	settings.init()
	app = qtw.QApplication(sys.argv)
	root = GUI()
	root.show()
	sys._excepthook = sys.excepthook
	sys.excepthook = settings.custom_excepthook
	try:
		sys.exit(app.exec_())
	except:
		sys.excepthook(*sys.exc_info())