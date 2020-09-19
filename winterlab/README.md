WinterLab board graphical user interface

Run main.py to use or build into executable with pyinstaller

Requires packages: sys, numpy, math, matplotlib, random, csv, time, signal, traceback, pyserial, PyQt5

Contents:
- settings.py
	- establishes global variables (change them here to affect all modules)
- gui.py
	- general interface setup and functioning
	- built on pyqt5
- wlboard.py
	- WLBoard object
	- establishes and handles asynchronous serial communication with WinterLab board
- animatedmplcanvas.py
	- sets up and controls an animated matplotlib canvas for the oscilloscope display
- multithreading objects: passed GUI threads to run mutliple processes without disrupting interactivity
	- plotter.py
		- pyqt qObject; triggers oscilloscope updates
	- sender.py
		- pyqt qObject; sends values to WinterLab board
	- sendrecv.py
		- pyqt qObject; handles two-way communication with WinterLab board
- sweepdialog.py
	- pyqt qDialog; interface for recording a frequency sweep
