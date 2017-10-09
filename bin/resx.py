'''
Provides methods for easily reading and using calibration and geometry data from file.

Provides run-time access to the information stored in the /etc/data.xml file, including access 
to calibrations and the geometry of the cylinders.

Also has a few functions that allow the easy use of the calibrations ("get_supply_voltage(pv)" 
for example)

Author: Chris Boyle (christopher.boyle.101@strath.ac.uk)
'''

# 3rd Party
import xml.etree.ElementTree as ET
import numpy as np
from numpy import pi

# read the xml file
root = ET.parse('./../etc/data.xml').getroot()

def parse_root(name, type):
    global root
    for child in root:
        # can be geometry or calibration...
        if child.tag == type and type == "geometry":
            if child.attrib["name"] == name:
                return float(child[0].text)
        elif child.tag == type and type == "calibration":
            if child.attrib["name"] == name:
                return [float(child[0].text), float(child[1].text)]
        elif child.tag == type and type == "misc":
            if child.attrib["name"] == name:
                return child[0].text

## DIMENSIONS
# in mm
icor = parse_root("icor", "geometry")
ich = parse_root("ich", "geometry")
ocor = parse_root("ocor", "geometry")
ocir = parse_root("ocir", "geometry")
och = parse_root("och", "geometry")

cal_dynamo = parse_root("dynamo", "calibration")
cal_5AHES = parse_root("5AHES", "calibration")

cal_IcoVms = parse_root("IcoVms", "calibration")
cal_TsVms = parse_root("TsVms", "calibration")
cal_TauIemf = parse_root("TauIemf", "calibration")

calc_supply_voltage = [0.066, 2.422]

cal_Vnl = [5.130, 15.275]

vmsmult = 2.0

version = parse_root("version", "misc")

def writeout(path="./../etc/data.xml"):
    '''
    resx.writeout(**kwargs)
    
    Writes the contents of a data file.
    
    **kwargs:
        path        (string)        Path to data.xml. Default is './../etc/data.xml'
    '''
    global root
    # update xml tree
    
    # geometries
    root[0][0].text = str(icor)
    root[1][0].text = str(ich)
    root[2][0].text = str(ocor)
    root[3][0].text = str(ocir)
    root[4][0].text = str(och)
    root[5][0].text = version
    # calibrations
    root[6][0].text = str(cal_dynamo[0])
    root[6][1].text = str(cal_dynamo[1])
    root[8][0].text = str(cal_5AHES[0])
    root[8][1].text = str(cal_5AHES[1])
    root[9][0].text = str(cal_IcoVms[0])
    root[9][1].text = str(cal_IcoVms[1])
    root[10][0].text = str(cal_TauIemf[0])
    root[10][1].text = str(cal_TauIemf[1])
    
    tree = ET.ElementTree(root)
    tree.write(path)

def get_current(cv):
    '''
    resx.get_current(cr2a, cr2b)
    
    Given the outputs from two current sensors, calculates the current.
    
    Parameters:
        cra    (list, float)       List of 5A HECS voltage readings
        crb    (list, float)       List of 5A HECS voltage readings
    
    Returns:
        cu      (list, float)       List of current values, averaged out from two sensors.
    '''
    #cu = (cv - 2.5) * (5.0 / 2.5) # current = (signal - (2.5v offset)) * (5A / 2.5v)
    cu = ((cv - 2.5) / 0.185) 
    return cu

def get_speed_rads(dr):
    '''
    resx.get_speed_rads(dr)
    
    Given readings from a dynamo, uses calibration data stored in data.xml to calculate the rotational speed in
    radians per second of the motor.
    
    Parameters:
        dr      (list, float)       List of dynamo voltage readings.
    
    Returns:
        v_rads  (list, float)       List of speeds in rad/s.
    '''
    v_rpm = get_speed_rpm(dr)
    v_rads = v_rpm * np.pi / 30 # rpm is 2pi per 60s =~ 1/10 rad/s
    return v_rads

def get_strain(spd_omega):
    '''
    resx.get_strain(omega)

    Parameters:
        dr      (list, float)       [List of] dynamo voltage readings.
    
    Returns:
        gd      (list, float)       [List of] strains in inverse seconds.
    '''
    gd = spd_omega * (icor / (ocir - icor)) 
    return gd

def get_current_coil(voltage):
    '''
    resx.get_current_coil(voltage)
    
    Given the motor's supply voltage, use calibration data stored in data.xml to 
    calculate the current loss due to inefficiency (Icoil).
    
    Parameters:
        pv      (list, float)       List of values sent to potentiometer.
    
    Returns:
        ico     (list, float)       List of coil currents.
    '''
    ico = cal_IcoVms[0] * voltage + cal_IcoVms[1]  # Ico = (1/Rco) * Vms + (~0.0)
    #ico = list()
    #try:
    #    x = len(voltage)
    #except:
    #    voltage = [voltage]
    #for v in voltage:
    #    ico.append((-0.003784 * (v ** 2)) + (0.06433 * v) + 0.4964)
    #ico = np.array(ico, np.float64)
    #if len(ico) == 1: ico = float(ico)
    return ico

def get_torque(stress, fill_volume_ml):
    '''
    resx.get_torque(stress, fill_volume_ml)
    
    Calculates the torque from stress and fill data.
    
    Parameters:
        stress          (list, float)   List of stresses
        fill_volume_ml  (number)        Volume of test fluid in ml.
    
    Returns:
        T       (list, float)       List of torques.
    '''
    A_small = (pi * (icor ** 2)) # in m^2
    A_big   = (pi * (ocir ** 2)) # in m^2
    A_middle_m2 = A_big - A_small
    fill_volume_m3 = fill_volume_ml * (10.0 ** (-9.0)) # 1000 ml in a l, 1 000 000 l in a m3: 10^9ml in a m3
    H = fill_volume_m3 / A_middle_m2
    T = stress * (2 * A_small * H)
    #T = (stress) / (pi * 2 * H)
    return T

def get_stress(T, fill_volume_ml):
    A_small = (pi * (icor ** 2)) # in m^2
    A_big   = (pi * (ocir ** 2)) # in m^2
    A_middle_m2 = A_big - A_small
    fill_volume_m3 = fill_volume_ml * (10.0 ** (-9.0)) # 1000 ml in a l, 1 000 000 l in a m3: 10^9ml in a m3
    H = fill_volume_m3 / A_middle_m2
    stress = T / (2 * A_small * H)
    return stress
    
if __name__ == "__main__": print __doc__
