'''
    Facilitates the control of a motor using dig_pot.py and adc.py.
    
    Controls the supply voltage sent to the motor in to control the speed.
    Data is logged using methods from adc.py. Noise is removed from the data
    using methods from filter.py. Temperature sensing data is obtained using
    tempsens.py.
    
    Author: Chris Boyle (christopher.boyle.101@strath.ac.uk)
'''

# System
import sys
import time
import os
import thread as td
from warnings import warn

# 3rd Party
try:
    import RPi.GPIO as gpio
except ImportError:
    import dummygpio as gpio

# RPi-R
#from filter import filter as ft
from dig_pot import MCP4131 as dp
from adc import MCP3008 as ac
from control import tf_pi_controller as pitf
from tempsens import ds18b20 as ts


class motor(object):
    '''
    Usage:
    
    object = motor.motor(**kwargs)
    
    Creates a new instance of a motor interface object.
    
    **kwargs:
        startnow        (bool)          Start polling as soon as the instance is created
        adc_vref        (float)         Voltage reference value. Default is 3.3
        poll_logging    (bool)          Indicates whether to log to file or not. Default is True.
        log_dir         (string)        Path to log directory. Default is './../logs/'
        therm_sn        (string)        Serial number of the thermocouple. Used in 1-wire communication.
                                        Default is '28-0316875e09ff'
        log_name        (string)        Name of log file to be written. If 'DATETIME', will replace with
                                        current date and time.
        i_poll_rate     (float)         Inverse poll rate: time to wait in between logging data. Default is 0.1
        pic_tuning      (float, float)  Tuning of PI controller. Kp and Ki respectively. Default is (0.2, 0.15)
        relay_pin       (integer)       Pin number which can be used to control the relay.
    '''
    
    # Internal Switches
    poll_running = False  # is the speed currently being polled?
    
    # Logging
    poll_logging = True  # Will log every (i_poll_rate)s if this is True
    log_paused = False
    log_add_note = False
    log_dir = "./../logs"  # where the logged data should be saved
    i_poll_rate = 0.1
    this_log_name = ""
    
    # Control thread
    control_stopped = True
    
    # Classes
    therm = ts("blank")
    pot = dp()  # potentiometer to control voltage
    pic = pitf((0.2, 0.15))
    aconv = ac()  # adc to read current/voltage
    
    # GPIO Pins
    relay_pin = 0

    def __init__(self, startnow=False, adc_vref=3.3, poll_logging=True, log_dir="./../logs", therm_sn="28-0316875e09ff",
                 log_name="DATETIME", i_poll_rate=0.1, pic_tuning=(0.2, 0.15), relay_pin=18):
        '''
        object = motor.motor(**kwargs)
        
        Creates a new instance of a motor interface object.
        
        **kwargs:
            startnow        (bool)          Start polling as soon as the instance is created. Default is False
            adc_vref        (float)         Voltage reference value. Default is 3.3
            poll_logging    (bool)          Indicates whether to log to file or not. Default is True.
            log_dir         (string)        Path to log directory. Default is './../logs/'
            therm_sn        (string)        Serial number of the thermocouple. Used in 1-wire communication.
                                            Default is '28-0316875e09ff'
            log_name        (string)        Name of log file to be written. If 'DATETIME', will replace with
                                            current date and time. Default is 'DATETIME'
            i_poll_rate     (float)         Inverse poll rate: time to wait in between logging data. Default is 0.1
            pic_tuning      (float, float)  Tuning of PI controller. Kp and Ki respectively. Default is (0.2, 0.15)
            relay_pin       (integer)       Pin number which can be used to control the relay. Default is 18
        '''
        
        # Setup relay pin
        self.relay_pin = relay_pin
        gpio.setmode(gpio.BCM)
        gpio.setup(self.relay_pin, gpio.OUT)
        gpio.output(self.relay_pin, gpio.LOW)
        
        # controller
        self.pic = pitf(pic_tuning)

        # Set sensor variables
        self.pot = dp()
        self.aconv = ac(cs_pin=1, vref=adc_vref)
        self.therm = ts(therm_sn)
        self.i_poll_rate=i_poll_rate
        
        # Set up logs
        self.log_dir = log_dir
        self.poll_logging = poll_logging
        
        # Start speed polling (if necessary)
        if (startnow): self.start_poll(log_name)

    def actuate(self):
        '''
        motor.actuate()
        
        Activates the relay such that the motor is now recieving power.
        '''
        gpio.output(self.relay_pin, gpio.HIGH)
        
    def deactuate(self):
        '''
        motor.deactuate()
        
        Deactivates the relay such that the motor is now off.
        '''
        gpio.output(self.relay_pin, gpio.LOW)
        
    def new_logs(self, log_name="DATETIME"):
        '''
        motor.new_logs(**kwargs)
        
        Creates a new set of logs. Useful for running tests one after another.
        
        **kwargs:
            log_name        (string)            Indicates name of new log file. 'DATETIME' will be replaced by date
                                                and time of run. Default is 'DATETIME'
        '''
        # Try closing old log file
        try:
            logf.close()
        except:
            pass
        
        # Check if log directory exists. If not, create it.
        if not os.path.isdir(self.log_dir):
            os.mkdir(self.log_dir)

        # Create log
        if (self.poll_logging):
            if log_name == "DATETIME":
                # Get unique number for the log file
                un = time.strftime("%H %M %S", time.gmtime())
                self.this_log_name = self.log_dir + "/log_" + un + ".csv"
            else:
                #self.this_log_name = self.log_dir + "/" + log_name
                self.this_log_name = str(log_name)
            
            self.logf = open(self.this_log_name, "w")
            
            self.logf.write("t,dr,cr,cr2a,cr2b,pv,T,Vpz\n")

    def start_poll(self, name="DATETIME"):
        '''
        motor.start_poll(**kwargs)
        
        Starts the data logging process. Launches a new thread which will continuously monitor the sensors and record
        the desired data. Saves file to <motor.log_dir>/<name>
        
        **kwargs:
            name            (string)            Indicates name of new log file. 'DATETIME' will be replaced by date
                                                and time of run. Default is 'DATETIME'
        '''
        if self.poll_logging:
            self.new_logs(log_name=name)
        if (not self.poll_running):  # if not already running
            td.start_new_thread(self.poll, tuple())
    
    def start_control(self):
        '''
        motor.start_control()
        
        Starts the PI control of the speed. Launches a new thread which will use the control library to decide how to 
        alter the motor's supply voltage in order to maintain the setpoint.
        '''
        if self.control_stopped:
            self.control_stopped = False
            td.start_new_thread(self.control, tuple())
            
    def update_setpoint(self, value):
        '''
        motor.update_setpoint(value)
        
        Sets the new setpoint on the controller.
        
        Parameters:
            value       (float)         The speed for the control system to target.
        '''
        self.pic.set_point = value
    
    def control(self):
        '''
        motor.control()
        
        When motor.start_control() is called, a thread is created running this method. Continuously gets the speed 
        (filtered) from the sensor detection thread and calculates the control action (new motor supply voltage) to
        best maintain the setpoint.
        
        This will repeat until motor.stop_control() is called, or motor.control_stopped becomes True.
        '''
        while not self.control_stopped:
            control_action = self.pic.get_control_action(self.speed)
            if control_action > 128: control_action = 128
            if control_action < 0: control_action = 0
            self.set_pot(control_action)
            time.sleep(0.1)
            
    def stop_control(self):
        '''
        motor.stop_control()
        
        Halts the motor speed control thread.
        '''
        self.control_stopped = True

    def read_sensors(self):
        '''
        motor.read_sensors()
        
        Reads from every channel of the ADC (CH0 to CH7).
        
        Returns:
            out     ([float] * 8)       List of values read from ADC.
        '''
        out = list()
        for a in range(0, 7):
            out.append(self.aconv.read_volts(a))
        return out
        
    def poll(self):
        '''
        motor.poll()
        
        When motor.start_poll() is called, a thread is created running this method. Continuously reads the sensors and 
        writes the values out to the log file.
        
        This will repeat until motor.stop_poll() is called, or motor.poll_running becomes False.
        '''
        self.poll_running = True
	
        while (self.poll_running):
            # At the third tone, the time will be...
            t = time.time()
            
            # Read sensors
            self.volts = self.read_sensors()
            
            temperature_c = 0.0
            
            # if thermosensor was set up properly...
            if self.therm.check_sn(): 
                temperature_c = self.therm.read_temp()
            else:
                warn("Temperature sensor cannot access its data! (Was the serial number entered correctly?)")
            
            if (self.poll_logging):
                #                   t         dr      cr      cr2a      cr2b   pv      T     Vpz
                self.logf.write(("{0:.6f}, {1:.3f}, {2:.3f}, {3:.3f}, {4:.3f}, {5}, {6:.3f}, {7} \n").format(
                    t, self.volts[0], self.volts[1], self.volts[2], self.volts[3], self.pot.lav, temperature_c, self.volts[4]))
            
            # delay for x seconds
            time.sleep(self.i_poll_rate)
        self.clean_exit()

    def set_pot(self, value):
        '''
        motor.set_pot(value)
        
        Sets the value of the digital potentiometer.
        
        Parameters:
            value       (int)       Value to set on digital potentiometer (representing motor supply voltage). Must be
                                    between 0 and 128 inclusive.
        '''
        if value < 0: value = 0
        if value > 128: value = 128
        self.pot.set_resistance(int(value))
                   
    def clean_exit(self):
        '''
        motor.clean_exit()
        
        Cleanly shuts down sensor poll, and control threads, as well as tidying up the GPIO settings and closing log 
        files.
        
        Should always be called when finished using the motor.
        '''
        self.poll_running = False
        self.control_stopped = True
        time.sleep(0.5)
        
        gpio.cleanup()

        if (self.poll_logging):
            self.logf.close()

if __name__ == "__main__":
    print __doc__
    print motor.__doc__
