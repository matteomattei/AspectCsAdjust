#!/usr/bin/python

# -*- coding: utf-8 -*-

from PySide.QtGui import *
from PySide.QtCore import *
from aspectcsadjust_ui import *
import sys, os, time, csv

VERSION='0.2'
UPDATE_DELAY=5

PERSIST_FILE=".persist"
DEFAULT_RESULT='C:\Result.csv'
DEFAULT_SAMPLE='C:\Defstd.alv'
DEFAULT_REPORT='C:\Report.csv'

RES_ROWLEN=43
RES_NUM_COL=0
RES_NAME_COL=1
RES_LINE_COL=2
RES_NAME2_COL=36
RES_POS_COL=32
RES_ABS_COL=18
RES_DATE_COL=21
RES_TIME_COL=22

SAM_NAME_COL=0
SAM_LINE_COL=1
SAM_CONC_COL=2
SAM_ABS_COL=3
SAM_NAME2_COL=4

REP_ABS_COL=7

class MyTableModel(QAbstractTableModel): 
	def __init__(self, data, header, parent=None, *args):
		QAbstractTableModel.__init__(self, parent, *args)
		self.full_data = data
		self.headerdata = header
    
	def rowCount(self, parent):
		return len(self.full_data) 
    
	def columnCount(self, parent):
		return len(self.full_data[0])
    
	def color(self, index):
		if not index.isValid():
			return None
		color = self.full_data[index.row()][index.column()][1]	
		if color==None:
			return Qt.black
		return color

	def data(self, index, role):
		if not index.isValid():
			return None
		if role == Qt.DisplayRole:
			return self.full_data[index.row()][index.column()]
		if role == Qt.BackgroundColorRole and index.column()==REP_ABS_COL:
			return QBrush(Qt.green)
		return None
	def headerData(self, col, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			return self.headerdata[col]
		return None

class TimerSignal(QObject):
	sigtimer = Signal(int)

class ParseDataSignal(QObject):
	sigdata = Signal(list)

class WorkingThread(QThread):
	def __init__(self, parent = None):
		QThread.__init__(self, parent)
		self.exiting = False
		self.sig_timer = TimerSignal()
		self.sig_data = ParseDataSignal()
		self.resultfile = ''
		self.samplefile = ''
		self.reportfile = ''
		self.sampledata = []

	def run(self):
		"""Thread callback"""
		self.checkfiles()
		counter=0
		global UPDATE_DELAY
		if self.exiting==False:
			self.parsesample()
			self.parseresult()
			self.processresult()
		while self.exiting==False:
			if counter>=UPDATE_DELAY:
				counter=0
				self.parseresult()
				self.processresult()
			else:
				counter=counter+1
			self.sig_timer.sigtimer.emit(counter)
			time.sleep(1)

	def checkfiles(self):
		"""Check if result, sample and report files are OK."""
		if not os.path.isfile(self.resultfile) or not os.path.isfile(self.samplefile):
			self.exiting=True
		try:
			f = open(self.reportfile,'w')
			with open(PERSIST_FILE,'w') as persist:
				persist.write(self.samplefile+'\n')
				persist.write(self.reportfile+'\n')
				persist.write(self.resultfile+'\n')
		except:
			self.exiting=True
		f.close()

	def parseresult(self):
		"""Parse result csv file"""
		self.data = []
		with open(self.resultfile,'r') as result:
			reader = csv.reader(result, delimiter=';')
			try:
				for row in reader:
					# only bring in a row if it's the expected length. This will cut out freetext file headers.
					if(len(row)==RES_ROWLEN) and row[RES_NUM_COL].strip().isdigit():
						self.data.append(row)
			except csv.Error as e:
 				sys.exit('file %s, line %d: %s' % (self.resultfile, reader.line_num, e))
	
	def processresult(self):
		"""Generate output reports based on latest result data"""
		self.output_data = []
		try:
			# output_data format: ("Numero,Nome,Elemento,Concentrazione,KAL,Diluizione,Posizione,Assorbanza,Data,Ora")
			# Init the reference sample to be used. It is done outside the loop because it is global to the "parser pass", i.e. it is entirely possible
			# that, when we parse the nth result row, we have to use the sample row from one of the previous result rows. This is due to the fact that
			# the sample to be used in the formula is defined as "the latest sample row whose NAME and LINE matched the NAME and LINE in a result row"
			latest_conc_match = 0
			# ABS value from the latest result row that matched with a sample
			latest_abs_match = 1 
			latest_name2_match = 1
			for row in self.data:
				self.output_data.append([row[RES_NUM_COL],row[RES_NAME_COL],row[RES_LINE_COL].strip("1234567890 "),0,' ',row[RES_NAME2_COL],row[RES_POS_COL],row[RES_ABS_COL],row[RES_DATE_COL],row[RES_TIME_COL]])
				for samplerow in self.sampledata:
					#print row
					#print samplerow
					# Check whether we have to update the latest matching sample
					if row[RES_NAME_COL].strip()==samplerow[SAM_NAME_COL].strip() and row[RES_LINE_COL].strip("1234567890 ")==samplerow[SAM_LINE_COL].strip():
						latest_abs_match = float(row[RES_ABS_COL])
						latest_conc_match = float(samplerow[SAM_CONC_COL])
						# use 1 if the NAME2 column is empty
						if row[RES_NAME2_COL].strip()=='':
							latest_name2_match = 1
						else:
							latest_name2_match = float(row[RES_NAME2_COL])
				
				a = ( latest_conc_match * float(row[RES_ABS_COL]) ) / latest_abs_match
				try:
					b = float(row[RES_NAME2_COL]) / latest_name2_match
				except:
					b = 0	# handles the case were input result file has rows with empty NAME2
				#print("computing ("+str(latest_conc_match) +" * "+row[RES_ABS_COL]+") / "+str(latest_abs_match)+" * ("+ row[RES_NAME2_COL]+" / "+str(latest_name2_match)+")")
				self.output_data[-1][3]= a * b
				#print self.output_data[-1][0]
		except:
			print("Parsing error. Wrong input file format?")
			self.exiting=True
			print("result row: "+str(row))
			print("sample row: "+str(samplerow))
			print("attempting: ("+str(latest_conc_match) +" * "+row[RES_ABS_COL]+") / "+str(latest_abs_match)+" * ("+ row[RES_NAME2_COL]+" / "+str(latest_name2_match)+")")
			raise
					
		print("records in/out: "+str(len(self.data))+"/"+str(len(self.output_data)))
		self.sig_data.sigdata.emit(self.output_data)
		self.generatereport(self.output_data)

	def parsesample(self):
		"""Parse sample csv file"""
		self.sampledata = []
		with open(self.samplefile,'r') as samples:
			reader = csv.reader(samples)
			for row in reader:
				self.sampledata.append(row)
	
	def generatereport(self, data):
		with open(self.reportfile,'w') as report:
			writer = csv.writer(report, delimiter=',')
			try:
				for row in data:
					writer.writerow(row)
			except csv.Error as e:
				sys.exit('file %s, line %d: %s' % (self.resultfile, reader.line_num, e))
		print("generated report!")

class AspectCSAdjust(QtGui.QMainWindow, Ui_MainWindow):
	def __init__(self, parent=None):
		super(AspectCSAdjust, self).__init__(parent)
		self.ui = Ui_MainWindow()
		self.setupUi(self)
		self.centerwindow()
		self.filebrowser = QFileDialog(self)
		self.setWindowTitle('AspectCSAdjust v.'+VERSION)
		self.thread = WorkingThread()
		self.thread.started.connect(self.thread_started)
		self.thread.finished.connect(self.thread_finished)
		self.thread.terminated.connect(self.thread_terminated)
		self.thread.sig_timer.sigtimer.connect(self.updatetimer)
		self.thread.sig_data.sigdata.connect(self.filltable)
	
		try:
			with open(PERSIST_FILE,'r') as persist:
				print("Opened "+PERSIST_FILE)	
				self.thread.samplefile = persist.readline().strip('\n')
				self.editSample.setText(self.thread.samplefile)
				self.thread.reportfile = persist.readline().strip('\n')
				self.editReport.setText(self.thread.reportfile)
				self.thread.resultfile = persist.readline().strip('\n')
				self.editResult.setText(self.thread.resultfile)
		except:
			print("Can not read persistant config, using defaults")	
			self.thread.samplefile = DEFAULT_SAMPLE
			self.editSample.setText(DEFAULT_SAMPLE)
			self.thread.reportfile = DEFAULT_REPORT
			self.editReport.setText(DEFAULT_REPORT)
			self.thread.resultfile = DEFAULT_RESULT
			self.editResult.setText(DEFAULT_RESULT)

	def centerwindow(self):
		"""Function to center the mainwindow in the display screen."""
		screen = QtGui.QDesktopWidget().screenGeometry()
		size =  self.geometry()
		self.move((screen.width() - size.width()) / 2,
				(screen.height() - size.height()) / 2)

	def selectResult(self):
		"""Slot for select result file."""
		archive = self.filebrowser.getOpenFileName(self,'Select Result CSV file','.','CSV file (*.csv)')
		if archive[0] != '' and os.path.isfile(archive[0]):
			self.thread.resultfile = archive[0]
			self.editResult.setText(archive[0]) 

	def selectSample(self):
		"""Slot for select sample file."""
		archive = self.filebrowser.getOpenFileName(self,'Select Sample CSV file','.','CSV file (*.csv)')
		if archive[0] != '' and os.path.isfile(archive[0]):
			self.thread.samplefile = archive[0]
			self.editSample.setText(archive[0]) 

	def selectReport(self):
		"""Slot for select report file."""
		archive = self.filebrowser.getSaveFileName(self,'Select Report CSV file','aaa.csv','CSV file (*.csv)')
		if archive[0] != '':
			self.thread.reportfile = archive[0]
			self.editReport.setText(archive[0])

	def closeEvent(self, event):
		"""Overlod of the actual closeEvent method.
		Just to make sure to close the working thread on closure."""
		self.thread.exiting=True
		if self.thread.isRunning():
			self.waitstatus('finished')
		event.accept()

	def runcheck(self):
		"""Slot for Start/Stop button."""
		if not self.thread.isRunning():
			self.start()
		else:
			self.stop()

	def thread_started(self):
		print('started')
	def thread_finished(self):
		print('finished')
	def thread_terminated(self):
		print('terminated')

	def checkfiles(self):
		"""Check if the files are correct."""
		if self.editReport.text() == '': return False
		if self.editSample.text() == '': return False
		if self.editResult.text() == '': return False
		return True
	
	def start(self):
		"""Callback for start application.
		Start thread and disable all fields."""
		if not self.checkfiles():
			QMessageBox.warning(self, "Specify files.", "Please specify all files.")
			return False
		self.thread.exiting=False
		self.thread.start()
		self.waitstatus('running')
		self.buttonStart.setText('Stop')
		self.buttonReport.setEnabled(False)
		self.buttonSample.setEnabled(False)
		self.buttonResult.setEnabled(False)
		self.editReport.setEnabled(False)
		self.editSample.setEnabled(False)
		self.editResult.setEnabled(False)
		
	def stop(self):
		"""Callback for stop application.
		Stop thread and re-enable all fields."""
		self.thread.exiting=True
		self.waitstatus('finished')
		self.buttonStart.setText('Start')
		self.buttonReport.setEnabled(True)
		self.buttonSample.setEnabled(True)
		self.buttonResult.setEnabled(True)
		self.editReport.setEnabled(True)
		self.editSample.setEnabled(True)
		self.editResult.setEnabled(True)
		self.lcdNumber.display(0)

	def waitstatus(self, status):
		"""Blocking wait until the thread is started/finished."""
		if status=='running':
			while not self.thread.isRunning():
				continue
		elif status=='finished':
			while not self.thread.isFinished():
				continue

	def updatetimer(self, value):
		"""Update LCD display number [5, 4, 3, 2, 1, 0]."""
		self.lcdNumber.display(value)
	
	def filltable(self, data):
		header = ['No.', 'Nome', 'Elemento', 'Concentrazione', 'KAL', 'Diluizione', 'Posizione', 'Assorbanza', 'Data', 'Ora']
		nrows = len(data)
		tm = MyTableModel(data, header, self)
		self.tableView.setModel(tm)
		self.tableView.resizeColumnsToContents()
		self.tableView.resizeRowsToContents()
		#self.tableView.horizontalHeader().setStretchLastSection(True)
		#print(data)

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	window = AspectCSAdjust()
	window.show()
	sys.exit(app.exec_())
