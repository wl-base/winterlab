'''
global settings file for WinterLab GUI: set values here to affect all moduules
'''

import sys

def custom_excepthook(type, value, tb):
	raw_report = traceback.format_exception(type, value, tb)
	report = '\n'.join(raw_report)
	print(report)
	print('Yikes!')
	sys.exit()


def init():
	global PYVERSION
	global VENDOR_ID
	global PRODUCT_ID
	global excepthook
	global BATCH_LEN
	global VIEW_LEN
	global DELTA_X
	global ADC_SAMPLERATE
	global WTABLELEN
	global F_CLK
	global INITIAL_XPAN
	global INITIAL_XWIDTH
	global INITIAL_XMIN
	global INITIAL_XMAX
	global INITIAL_YMIN
	global INITIAL_YMAX
	global MIN_AMP
	global MAX_AMP
	global MIN_OFFSET
	global MAX_OFFSET
	global MAX_FREQ
	global MAX_DC
	global MIN_DC

	PYVERSION = sys.version_info[0]

	VENDOR_ID = '16C0'
	PRODUCT_ID = '0483'

	BATCH_LEN = 1024 # number of samples read at a time from board
	VIEW_LEN = 512  # limit the display scale to avoid scrolling past edge of set
	DELTA_X = 4.2e-6 # seconds per x division
	ADC_SAMPLERATE = 238095 # Hz
	WTABLELEN = 4096.0
	F_CLK = 4096000 # sample rate of MCU DAC

	INITIAL_XPAN = VIEW_LEN/4
	INITIAL_XWIDTH = VIEW_LEN/2
	INITIAL_XMIN = INITIAL_XPAN * DELTA_X
	INITIAL_XMAX = INITIAL_XMIN + INITIAL_XWIDTH * DELTA_X
	INITIAL_YMIN = 0
	INITIAL_YMAX = 5

	MIN_AMP = 0
	MAX_AMP = 9

	MIN_OFFSET = -4.5
	MAX_OFFSET = 4.5

	MAX_FREQ = 100000

	MAX_DC = 4.5
	MIN_DC = -4.5 
