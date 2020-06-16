from threading import Thread, Lock, Event
import time
import serial
import sys
import glob
import os
import struct   
from csv import writer
import numpy as np
from collections import deque 
import serial.tools.list_ports
import numpy as np
import matplotlib as mtp
mtp.use('QT5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.animation as manim
from datetime import datetime, timedelta
from PyQt5.QtCore import QDateTime, Qt, QTimer
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget,QMainWindow, QFontComboBox,QMessageBox)
from PyQt5.QtGui import QFont
from PyQt5.QtSerialPort import QSerialPortInfo

import signal
look= Lock()
# Global Parametes

stop_threads = False
stop_threads_1 = False
flag_data=False
flag_save= False
line =1
analog =0
dato1=0
event = Event()
data_serial = [b'', b'', b'',b'']

# Class for serial Comunication 
class Serial_com:
    def __init__(self, port, baud):
        self.running = 1
        self.analog =0
        self.dato1=0
        self.ser= serial.Serial(port,baud,\
        parity=serial.PARITY_NONE,\
        stopbits=serial.STOPBITS_ONE,\
        bytesize=serial.EIGHTBITS,\
        timeout=(0.5))
        self.SOH = b'H'
        self.STX = b'T'
        self.ETX = b'E'
        # Thread for reading serial Port
        self.t1 = Thread(target = self.loop)
        self.t1.start()
        self.t2 = Thread(target = self.update)
        self.t2.start()


    def loop (self):
        c=['','','','']
        global data_serial
        while True:
            global stop_threads, data_serial, event
            if stop_threads: 
                break
                # stop_threads_1= True
            
            # Waiting for serial buffer
            if self.ser.inWaiting() > 0:    
                # a=ser.read_until(ETX,8)
                a = self.ser.readline(1)
                # Define the start of protocol
                if a == self.SOH:
                    # Read the rest of the protocol
                    b = self.ser.readline(5)
                    # if its correct the number of bytes separate data received
                    if len(b) ==5:
                        c= struct.unpack('sshs',b)

                # use look for blocking changes from other threads
                look.acquire()
                data_serial =c
                if(data_serial[0]==b'R'):
                    data.save(data_serial[2],0)
                    # data.axis_data1 = data_serial[2]
                    # print (data.axis_data1)
                if(data_serial[0]==b'B'):
                    data.save(data_serial[2],1)                
                look.release()
                # flag_data = True
                # event.set()
        self.ser.close()    
    
    def update (self):
        i = 0
        while True:
            global  event
            if stop_threads:
                break
            if event.is_set():
                # print(data.tim)
                # print(data.axis_t[-1],data.axis_data1[-1], data.axis_data2[-1])
                frame.update()
                global flag_save, line
                if(flag_save):
                    # print('guardar')
                    data_save=[str(line),data.tim ,str(frame.baud_selec),str(data.data1),str(data.data2)]
                    # print(data_save)
                    append_list_as_row(frame.path_dir,frame.data_rec, data_save)
                    line = line+1

                event.clear()

# Lists serial port names
# A list of the serial ports available on the system

def serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


# Function for save data in CSV file
def append_list_as_row(path,file_name, list_of_elem):
    # Open file in append mode
    f='csv/'+file_name+'.csv'
    with open(f, 'a', newline='') as write_obj:    
        # Create a writer object from csv module
        csv_writer = writer(write_obj)
        # Add contents of list as last row in the csv file
        csv_writer.writerow(list_of_elem)



# Class of GUI
class Screen(QWidget):
    def __init__(self, parent = None):
        super(Screen, self).__init__(parent)
        self.port_selec=''
        self.baud_selec='115200'
        self.choices=[]
        self.y_max = 100
        self.y_min = 0
        self.path_dir = 'C:'
        self.data_rec=''
        self.time_upd= 0.5
        # panel = self

        grid = QGridLayout()
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 1)        
        
        # grid.setRowStretch(0,1)        
        grid.setRowStretch(2,5)
        # grid.setRowStretch(2,1)

        grid.setRowMinimumHeight(0,1)

        grid.addWidget(self.serial_settings(), 0, 0)
        grid.addWidget(self.plot_settings(), 1, 0,2,1)
        grid.addWidget(self.message(),3,0,1,2)

        grid.addWidget(self.record_settings(), 0, 1)
        grid.addWidget(self.current_settings(), 1, 1)
        grid.addWidget(self.graph_settings(), 2, 1)
        self.setLayout(grid)

        self.setFixedSize(1000,600)
        self.setWindowTitle('Datalogger')
        # panel.SetBackgroundColour('#364958')
        # panel.SetBackgroundColour('#5B5F97')
        self.show()


# --------------------------------BOX SERIAL SETTINGS-----------------------------------------------------------
    def serial_settings(self):
        self.box_serial = QGroupBox("Serial Settings")
        text_port = QLabel("Port")
        # text_port.SetBackgroundColour('#F1F7EE')
        
        self.port = QComboBox()
        self.port.addItem("Choose a Port")
        # self.ports =QSerialPortInfo.availablePorts()
        # for info in self.ports:             
        #     self.port.addItem(info.portName())
        # self.port.activated.connect(self.selec_port)
        self.ports = list(serial.tools.list_ports.comports())
        for i in self.ports:
            self.port.addItem(i.device)

        self.port.activated.connect(self.selec_port)
        # self.port.setStyleSheet('background-color: white')
    
        text_baud = QLabel("Baudrate")
        self.baud = QComboBox()
        self.baud_array=['2400','4800','9600','19200','38400','57600','74880'
        ,'115200','230400', '460800']
        for i in self.baud_array:
            self.baud.addItem(i)
        self.baud.setCurrentIndex(7 )
        self.baud.activated.connect(self.selec_baud)
        # self.baud.setStyleSheet('background-color: white')
        
        self.connect_button = QPushButton('Connect')
        self.connect_button.clicked.connect(self.onConnect)
        # self.connect_button.setStyleSheet('background-color: #F2F2F2')

        b1 = QHBoxLayout()
        b1.addWidget(text_port)
        b1.addWidget(self.port)
        b1.addStretch(1)
        b1.addWidget(text_baud)
        b1.addWidget(self.baud)
        b1.addStretch(2)
        b1.addWidget(self.connect_button) 
        
        # self.box_serial.setStyleSheet("background-color: #F1F7EE")
        self.box_serial.setLayout(b1)
        return self.box_serial

# ----------------------BOX RECORD SETTINGS---------------------------------------------------        
    def record_settings(self):
        self.box_rec = QGroupBox("Record/Export")
        self.rec_button = QPushButton('REC') 
        self.rec_button.clicked.connect(self.onRec)
        # self.rec_button.setStyleSheet('background-color: #F2F2F2')

        b1 = QHBoxLayout()
        b1.addWidget(self.rec_button)

        b1.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.box_rec.setLayout(b1)
        # self.box_rec.setStyleSheet("background-color: #F1F7EE")
        return self.box_rec

# ------------------ PLOT SETTINGS ------------------------------------------------------------
    def plot_settings(self):
        self.box_plot = QGroupBox("Real Time Graph")
        self.fig = Figure(figsize=([6.2,5]),tight_layout = {'pad': 2})
        self.a = self.fig.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.fig)
        b1 = QHBoxLayout()
        b1.addWidget(self.canvas)
        b1.addStretch(1)
        self.box_plot.setLayout(b1)
        self._plot = RealtimePlot(self.a, self.canvas, self.fig)

        self.box_plot.setStyleSheet("background-color: #87BBA2")    
        return self.box_plot

# -------------------- CURRENT SETTINGS -----------------------------------------------------
    def current_settings(self):
        self.box_data = QGroupBox("Current Values")
        text_data1= QLabel("Analogue 1")
        text_data1.setFont(QFont ("Times",18,weight=QFont.Bold))
        text_data1.setStyleSheet("color:#143642")

        self.value_data1 = QLabel("00")
        self.value_data1.setStyleSheet("background-color:#F1F7EE")
        self.value_data1.setAlignment(Qt.AlignHCenter)
        self.value_data1.setFont(QFont("Times",40,weight=QFont.Bold))
                

        text_data2 = QLabel("Analogue 2")
        text_data2.setFont(QFont ("Times",18,weight=QFont.Bold))
        text_data2.setStyleSheet("color:#143642")

        self.value_data2 = QLabel("00")
        self.value_data2.setStyleSheet("background-color:#F1F7EE")
        self.value_data2.setAlignment(Qt.AlignHCenter)
        self.value_data2.setFont(QFont("Times",40,weight=QFont.Bold))

        b1 = QVBoxLayout()
        b1.addWidget(text_data1)
        b1.addWidget(self.value_data1)
        b1.addWidget(text_data2)
        b1.addWidget(self.value_data2)
        b1.setAlignment(Qt.AlignHCenter)
        # b1.addStretch(1)
        self.box_data.setLayout(b1)
        self.box_data.setStyleSheet("background-color: #87BBA2")    
        return self.box_data
        
# -------------------- GRAPH SETTINGS -----------------------------------------------------
    def graph_settings(self):
        text_data1= QLabel("Y-Limit Max")

        self.Limit_max = QSpinBox()
        # self.value_data1.setMaximun
        self.Limit_max.setRange(-10000,10000)
        self.Limit_max.setSingleStep(10)
        self.Limit_max.setValue(100)
        # self.Limit_max.setStyleSheet('background-color: white')
        
        
        text_data2 = QLabel("Y-Limit Min")
        self.Limit_min = QSpinBox()
        self.Limit_min.setRange(-10000,10000)
        self.Limit_min.setSingleStep(10)
        self.Limit_min.setValue(0)
        # self.Limit_min.setStyleSheet('background-color: white')

        self.time = QSpinBox()
        self.time.setRange(-100000,10000000)
        self.time.setSingleStep(100)
        self.time.setValue(500)
        # self.time.setStyleSheet('background-color: white')
        text_data3 = QLabel("Time to update")
        text_data4 = QLabel("[ms]")

        self.set_button = QPushButton('SET') 
        # self.set_button.setStyleSheet('background-color: #F2F2F2')
        self.set_button.clicked.connect(self.Set_Limit)

        b1 = QHBoxLayout()
        b1.addWidget(text_data1)
        b1.addWidget(self.Limit_max)
        b1.setAlignment(Qt.AlignHCenter)

        b2 = QHBoxLayout()
        b2.addWidget(text_data2)
        b2.addWidget(self.Limit_min)
        b2.setAlignment(Qt.AlignHCenter)

        b4 = QHBoxLayout()
        b4.addWidget(text_data3)
        b4.addWidget(self.time)
        b4.addWidget(text_data4)
        b4.setAlignment(Qt.AlignHCenter)

        b3 = QVBoxLayout()
        b3.addLayout(b1)
        b3.addStretch(1)
        b3.addLayout(b2)
        b3.addStretch(1)
        b3.addLayout(b4)
        b3.addStretch(1)
        b3.addWidget(self.set_button)
        b3.addStretch(1)
        # self.box_data.setLayout(b1)
        self.box_limit = QGroupBox("Graph Settings")
        self.box_limit.setLayout(b3)
        # self.box_limit.setStyleSheet("background-color: #87BBA2")    
        return self.box_limit
    
# -------------------- MESSAGE SETTINGS -----------------------------------------------------
        
    def message(self):
        self.box_msg = QGroupBox("Message Bar")

        text_1 = QLabel("Serial Comunication: ")
        text_1.setFont(QFont("Times",12,weight=QFont.Bold))

        self.ser_msg= QLabel("Close")
        self.ser_msg.setFont(QFont("Times",12,weight=QFont.Bold))
        self.ser_msg.setStyleSheet('color: #364958')
        
        text_2 = QLabel("Recording Data: ")
        text_2.setFont(QFont("Times",12,weight=QFont.Bold))

        self.text_msg = QLabel('Stop') 
        self.text_msg.setFont(QFont("Times",12,weight=QFont.Bold))
        self.text_msg.setStyleSheet('color: #364958')

        b1 = QHBoxLayout()
        b1.addWidget(text_1)
        b1.addWidget(self.ser_msg)
        b1.addStretch(1)
        b1.addWidget(text_2)
        b1.addWidget(self.text_msg)
        b1.addStretch(1)

        self.box_msg.setLayout (b1)
        return self.box_msg

#------------------------------------------------------------------------------------------------
    def showDialog(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("Alert")
        msgBox.setWindowTitle("Choose a valid port")
        msgBox.setStandardButtons(QMessageBox.Ok )

        returnValue = msgBox.exec()
    
    def onRec(self,event):
        # ------------ Function for export data
        # print('rec')
        # print(self.rec_button.Label)
        if self.rec_button.text()=='REC':
            print('rec')
            # self.path_dir= os.path.abspath(os.getc wd())
            self.data_rec = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
            self.text_msg.setText('Exporting file ...'+ self.data_rec+'.csv')
            # f=self.path_dir+"\\"+self.data_rec+'.csv'
            f='csv/'+self.data_rec+'.csv'
            print(self.path_dir)

            # Create CSV file
            with open(f, 'w') as write_obj:
            # Create a writer object from csv module
                csv_writer = writer(write_obj)
            # Add header to the csv file
                csv_writer.writerow(['Date Time','Baudrate','Data analog1','Data analog2'])
            global flag_save
            flag_save = True
            self.rec_button.setText('STOP')
        else:
            global line
            self.text_msg.setText('Stop')
            self.rec_button.setText('REC')        
            flag_save = False
            line = 1

    # List COM availables 
    def List_port(self):
        # print(serial_ports)
        self.port.clear()
        ports = list(serial.tools.list_ports.comports())
        lst = []

        for p in ports:
            # print (type(p.device))
            self.port.addItem(p.device)

    # Get de Baudrate selected
    def selec_baud(self,text):
        self.baud_selec = self.baud.currentText() 
        print( type(self.baud_selec))
        # print(text)

    # Get Port Selected 
    def selec_port(self,text):
        self.port_selec = self.port.itemText(text)
        print(type(self.port_selec))
    
    # Start thread of Serial Communication
    def onConnect(self, event):
        global stop_threads,stop_threads_1, flag_data 
        print('port: '+ self.port_selec +'Baud: '+self.baud_selec)
        # print(self.connect_button.text())
        if self.connect_button.text()=='Connect':
            if(self.port_selec == '' or self.port_selec == 'Choose a port'):
                self.showDialog()
            else:
                self.connect_button.setText('Disconnect')
                stop_threads = False
                stop_threads_1 = False
                print('Start')
                self.Serial=Serial_com(self.port_selec,self.baud_selec)
                self.ser_msg.setText("Open")
                self.port.setDisabled(True)
                self.baud.setDisabled(True)
                flag_data = True
        else:
            self.connect_button.setText('Connect')
            stop_threads = True
            flag_data = False
            self.ser_msg.setText("Close")            
            # self.Serial.endApplication()
            self.port.setDisabled(False)
            self.baud.setDisabled(False)
    
    # Reset Plot Limits  
    def Set_Limit(self,event):
        self.y_max= self.Limit_max.value()
        self.y_min= self.Limit_min.value()
        self.time_upd = self.time.value()/1000
        self._plot.y_max = self.y_max
        self._plot.y_min = self.y_min
        self._plot._time = self.time_upd
        # print(self.y_max)
        # print(self.y_min)

    def update(self):
        self.value_data1.setText(str(data.data1))
        self.value_data2.setText(str(data.data2))

            
# Class for save data received and create arrays for plotting
class DataPlot:
    def __init__(self, max_entries = 60):
        self.axis_t = deque([0],maxlen=10)
        self.axis_data1 = deque([0],maxlen=max_entries)
        self.axis_data2 = deque([0],maxlen=max_entries)
        self.tim = 0
        self.data1= 0
        self.data2= 0
        self.data = [0, 0]
        self.data_save=[]
        self.max_entries = max_entries
        self.count=0

    # function for save data for plotting, save data in CSV 
    def save_all(self,data1,data2,tim):
        ######## DATA1 ##########################
        self.axis_t.append(datetime.now().strftime('%H:%M:%S'))
        self.axis_data1.append(data1)
        ######## DATA2 ##############
        self.axis_data2.append(data2)

    # function for save data incomming for serial port         
    def save_data(self, data1,data2):
        self.tim=datetime.now().strftime('%Y %m %d %H:%M:%S')
        ######## DATA1 ##########################
        # print(self.axis_t)
        self.data1= data1
        # print(self.axis_data1)
        ######## DATA2 ##############
        self.data2= data2
        # print(self.axis_data2)

    # Wait for get two data form serial before save
    def save (self,a,i):
        self.count=self.count+1
        self.data[i]=a        
        if(self.count==2):
            # print(self.data)
            self.save_data(self.data[0],self.data[1])
            self.count=0
            global event
            event.set()

class RealtimePlot:
    def __init__(self, a,canvas, fig):
        self.y_min = 0
        self.y_max = 100
        self._time = 0.5
        self.x_tim= deque([],15)
# -------------------- PLOT SETTINGS -----------------------------------------------------
        self.a = a
        self.canvas = canvas
        self.fig = fig
        self.lineplot, = self.a.plot([],[],'ro-', label="Data1",markersize=1, linewidth=1)
        self.lineplot1, = self.a.plot( [],[],'bo-', label="Data2",markersize=1,linewidth=1)
        self.a.legend(loc=1) 
        self.a.minorticks_on()
        self.a.grid(which='major', linestyle='-', linewidth='0.5', color='black') 
        self.a.grid(which='minor', linestyle=':', linewidth='0.5', color='black') 
        # self.fig.canvas.draw()
        # self.animator = manim.FuncAnimation(self.fig,self.anim, interval=500,)

        self.t3= Thread(target = self.loop)
        self.t3.start()    
    # Plotting Real timeF
    def loop (self):
        while True:
            global stop_threads_1, event, flag_data
            if stop_threads_1:
                break
            # print(data.axis_data1)
            # print(data.axis_data2)
            if flag_data:
                data.save_all(data.data1,data.data2,data.tim)
            # self.animator = manim.FuncAnimation(self.fig,self.anim, interval=500,blit=True)
            
            self.anim()
            # time.sleep(float(self._time))
    
    def anim (self):
        start = time.process_time()
        if flag_data:
            data.save_all(data.data1,data.data2,data.tim)
        self.a.clear()
        # Update Data to the plot
        self.a.set_ylim([self.y_min , self.y_max ])
        y=np.arange(self.y_min, self.y_max+5,10)
        self.a.set_yticks(y)

        # self.a.set_xticklabels(self.x_tim, fontsize=8)
        self.a.set_xticklabels(data.axis_t, fontsize=8)
        # print(data.axis_t)
        # self.a.autoscale_view(scalex=True, tight=True)   
        # self.a.autoscale_view(True)   
        # self.a.relim()
        # self.lineplot.set_data(np.arange(0,len(data.axis_data1),1),np.array(data.axis_data1))
        # self.lineplot1.set_data(np.arange(0,len(data.axis_data2),1),np.array(data.axis_data2))
        self.a.plot(list(range(len(data.axis_data1))),data.axis_data1,'ro-', label="Analogue 1",markersize=1, linewidth=1)
        self.a.plot(list(range(len(data.axis_data2))),data.axis_data2,'bo-', label="Analogue 2",markersize=1,linewidth=1)
        self.a.legend(loc=1) 
        self.a.grid()
        # self.a.minorticks_on()
        # self.a.grid(which='major', linestyle='-', linewidth='0.5', color='black') 
        # self.a.grid(which='minor', linestyle=':', linewidth='0.5', color='black') 
        self.fig.canvas.draw()
        # self.fig.canvas.flush_events()
        
        stop = time.process_time()
        print(stop-start)



 
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    # object for save data
    data = DataPlot()
    # GUI panel
    app = QApplication([])
    frame = Screen()
    app.exec_()
    # sys.exit(app.exec_())
    stop_threads_1 = True 
    stop_threads = True 
    print("exit")

    


