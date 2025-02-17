#!/usr/bin/env python
# coding: utf-8

# In[1]:


#CHECK data strucutre of buffer_data, implement 
#CHECK average meaning

from pymeasure.instruments.keithley import Keithley2400
import numpy as np
import pandas as pd
from time import sleep
import datetime
import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
import math
import sys
import tempfile
import random
from time import sleep
from pymeasure.log import console_log
from pymeasure.display.Qt import QtWidgets
from pymeasure.display.windows import ManagedWindow
from pymeasure.experiment import Procedure, Results
from pymeasure.experiment import IntegerParameter, FloatParameter, Parameter


# In[2]:


"""
# Set the input parameters
data_points = 10

max_voltage = 1
min_voltage = -max_voltage
#INITAL HOLD
inital_voltage = 4 # in V
holding_time_inital = 30 # seconds

# SWEEP Set source_current and measure_voltage parameters
  # in V

measure_nplc = 0.1  # Number of power line cycles SLOW (10PLC), MEDIUM (1PLC) and FAST (0.1PLCC)
  # in A
hold_time = 10 #in seconds, between voltage steps
"""

inital_currents = []
voltage_range = None
current_range = None
compliance_current = 1  # in A
#measurement_time = 0.2 # in seconds for SWEEP and INITAL

date_of_measurment = (str(datetime.datetime.now())[:16])
date_of_measurment=date_of_measurment.replace('-','')
date_of_measurment=date_of_measurment.replace(':','')
date_of_measurment=date_of_measurment.replace(' ','')
save_name = "Voltage_sweep" + str(date_of_measurment)
#setting_names = ["holding_time_inital", "hold:time", "measurement_time"]
#settings = [str(holding_time_inital),str(hold_time),str(measurement_time)]
hold_data = []
sweep_data = []
sourcemeter = Keithley2400("ASRL4", timeout=1000, baud_rate=19200)


# In[ ]:





# In[ ]:





# In[3]:


class RandomProcedure(Procedure):
    global sourcemeter
    data_points = IntegerParameter('Number of data points for sweep (defines step size)', default=10, minimum=2)
    max_voltage = FloatParameter('Sweep final voltage', units='V', default=1, minimum=-21, maximum=21)
    min_voltage = FloatParameter('Sweep starting voltage', units='V', default=-1, minimum=-21, maximum=21)
    inital_voltage = FloatParameter('Inital hold voltage', units='V', default=4)
    holding_time_inital = FloatParameter('Inital holding time', units='s', default=10)
    measure_nplc = FloatParameter('nplc (0.01-10)', units='Hz/Hz', default=1, minimum=0.01, maximum=10)
    measurement_time = FloatParameter('Time between measurements (Set to zero for no delay)', units='s', default=0, minimum=0)
    hold_time = FloatParameter('Sweep holding time', units='s', default=3) #in seconds, between voltage steps
    averages = FloatParameter('Sample number (number of samples to take the average of for each measurement)', units='', default=10) 
    
    DATA_COLUMNS = ['Timestep','Voltage', 'Current','Time']

    def startup(self):
        global sourcemeter
        log.info("Connecting to device")
        self.voltages = np.linspace(self.min_voltage, self.max_voltage, num=self.data_points)
        #self.no_of_measurments = np.arange(0, self.hold_time/self.measurement_time,1)
        try:
            sourcemeter.reset()
            sourcemeter.use_front_terminals()
            sourcemeter.apply_voltage(voltage_range, compliance_current)
            sourcemeter.measure_current(self.measure_nplc, current_range)
            sleep(0.1)  # wait here to give the instrument time to react
            self.mestime = 1/50*self.measure_nplc*self.averages
            sourcemeter.stop_buffer()
            sourcemeter.disable_buffer()
            #sourcemeter.display_enabled = False
            log.info(str(sourcemeter.id))
        except Exception as e:
            log.warning("Failed to connect" + str(e))    



    def execute(self):
        global sourcemeter
        time_step = 0
        applied_voltage = self.inital_voltage
        sourcemeter.enable_source()
        sourcemeter.config_buffer(self.averages)
        sourcemeter.source_voltage = applied_voltage
        sourcemeter.start_buffer()
        sourcemeter.wait_for_buffer()
        log.info("Starting Inital hold")
        date_of_measurment_2 = datetime.datetime.now()
        #INITAL HOLD
        for i in range(0,int(self.holding_time_inital/(self.measurement_time+self.mestime)),1):
            sourcemeter.config_buffer(self.averages)
            sourcemeter.start_buffer()
            sourcemeter.wait_for_buffer()
            time_step += 1
            
            data = {
                'Timestep': time_step,
                'Voltage': applied_voltage,
                'Current': sourcemeter.means[1],
                'Time': (datetime.datetime.now()-date_of_measurment_2).total_seconds()
            }
            self.emit('results', data)
            log.debug("Emitting results: %s" % data)
            #self.emit('progress', 100 * time_step / ((int(self.holding_time_inital/(self.measurement_time+self.mestime))*len(self.voltages))+int(self.holding_time_inital/(self.measurement_time+self.mestime))))
            self.emit('progress', 100 * (datetime.datetime.now()-date_of_measurment_2).total_seconds()/(self.holding_time_inital+self.hold_time*len(self.voltages)))
            try:
                sleep(self.measurement_time-self.mestime)
            except:
                pass
            hold_data.append(sourcemeter.buffer_data)
            if (datetime.datetime.now()-date_of_measurment_2).total_seconds() > math.ceil(int(self.holding_time_inital)):
                log.info("overstepped time" + str((datetime.datetime.now()-date_of_measurment_2).total_seconds()))
                break
            #if (datetime.datetime.now()-date_of_measurment_2).total_seconds() > (self.holding_time_inital+2 ):
            #    break
            if self.should_stop():
                log.warning("Caught the stop flag in the procedure")
                break
        
        #SWEEP
        sourcemeter.config_buffer(self.averages)
        sourcemeter.start_buffer()
        sourcemeter.wait_for_buffer()
        log.info("Starting SWEEP")
        for applied_voltage in self.voltages:
            sourcemeter.source_voltage = applied_voltage
            date_of_measurment_3 = datetime.datetime.now()
            for i in range(0,int(self.hold_time/(self.measurement_time+self.mestime)),1):
                sourcemeter.config_buffer(self.averages)
                sourcemeter.start_buffer()
                sourcemeter.wait_for_buffer()
                time_step += 1
                data = {
                    'Timestep': time_step,
                    'Voltage': applied_voltage,
                    'Current': sourcemeter.means[1],
                    'Time': (datetime.datetime.now()-date_of_measurment_2).total_seconds()    
                }
                self.emit('results', data)
                log.debug("Emitting results: %s" % data)
                #self.emit('progress', 100 * time_step / ((int(self.holding_time_inital/(self.measurement_time+self.mestime))*len(self.voltages))+int(self.holding_time_inital/(self.measurement_time+self.mestime))))
                self.emit('progress', 100 * (datetime.datetime.now()-date_of_measurment_2).total_seconds()/(self.holding_time_inital+self.hold_time*len(self.voltages)))
                try:
                    sleep(self.measurement_time-self.mestime)
                except:
                    pass
                sweep_data.append(sourcemeter.buffer_data)
                #a = int(self.hold_time/(self.measurement_time+self.mestime))*(self.measurement_time-self.mestime)
                #if 0 > a:
                #    a = 1
                if (datetime.datetime.now()-date_of_measurment_3).total_seconds() > math.ceil(int(self.hold_time)):
                    log.info("overstepped time" + str((datetime.datetime.now()-date_of_measurment_3).total_seconds()))
                    break
                #if (datetime.datetime.now()-date_of_measurment_3).total_seconds() > (self.hold_time+2 + (self.measurement_time-self.mestime)*int(self.hold_time/(self.measurement_time+self.mestime))):
                 #   break
                if self.should_stop():
                    log.warning("Caught the stop flag in the procedure")
                    break
        
        sourcemeter.triad(1024,0.2)
        #sourcemeter.display_enabled = True
        sourcemeter.shutdown()
        date_of_measurment = (str(datetime.datetime.now())[:16])
        date_of_measurment=date_of_measurment.replace('-','')
        date_of_measurment=date_of_measurment.replace(':','')
        date_of_measurment=date_of_measurment.replace(' ','')
        save_name = "Voltage_sweep" + str(date_of_measurment)
        #dataframe_to_save = sweep_data + hold_data
        dataframe_to_save_hold = pd.DataFrame({
        'Hold Current': np.concatenate(hold_data).flat})
        dataframe_to_save_sweep = pd.DataFrame({
        'Sweep current': np.concatenate(sweep_data).flat})
        dataframe_to_save_hold .to_csv("C:/Users/ARC-User/Voltage sweep Keithle2401/measurments/" + save_name +"_hold.csv")
        dataframe_to_save_sweep.to_csv("C:/Users/ARC-User/Voltage sweep Keithle2401/measurments/" + save_name +"_sweep.csv")
        log.info("measurement complete, data saved succesfully")
class MainWindow(ManagedWindow):

    def __init__(self):
        super().__init__(
            procedure_class=RandomProcedure,
            inputs=['inital_voltage', 'min_voltage', 'max_voltage', 'data_points','holding_time_inital','measurement_time'
                 ,'hold_time','measure_nplc','averages'],
            displays=['inital_voltage', 'min_voltage', 'max_voltage', 'data_points','holding_time_inital','measurement_time'
                   ,'hold_time','measure_nplc','averages'],
            x_axis='Timestep',
            y_axis='Current'
        )
        self.setWindowTitle('Voltage sweep')
        self.filename = save_name   # Sets default filename
        self.directory = r'C:/Users/ARC-User/Voltage sweep Keithle2401/measurments/'  


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




