#
# tempsens.py
#
# class controlling the DS18B20 1-wire temperature sensor from a Raspberry Pi
# 
# Taken (almost verbatim) from:
# https://www.modmypi.com/blog/ds18b20-one-wire-digital-temperature-sensor-and-the-raspberry-pi
#
# Feels a bit silly, I'd rather directly control the sensor but w/e
#
# Requires root

import os
import sys
import platform


class ds18b20(object):

    def __init__(self, serno):
        # loads 1 wire drivers
        if platform.system() == "Windows":
            self.on_windows = True
        else:
            self.on_windows = False
            os.system('sudo -H modprobe w1-gpio')
            os.system('sudo -H modprobe w1-therm')
            self.sens_file = '/sys/bus/w1/devices/{}/w1_slave'.format(serno)

    def temp_raw(self):
        
        f = open(self.sens_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    def read_temp(self):
        if self.on_windows: return 20.0
        
        lines = self.temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.temp_raw()
    
        temp_output = lines[1].find('t=')

        if temp_output != -1:
            temp_string = lines[1].strip()[temp_output+2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c
    
    def set_sn(self, serno):
        self.sens_file = '/sys/bus/w1/devices/{}/w1_slave'.format(serno)
    
    def check_sn(self):
        return os.path.isfile(self.sens_file)
