from glob import glob
from sys import path

import numpy as np
from matplotlib import use as mpluse
mpluse('Agg')
import matplotlib.pyplot as plt

path.append("./../bin/")

from plothelp import plot_fit
from plothelp import read_logf
from filter import filter
import resx

I_EMFs = list()
T_MSs  = list()

aliemfs = list()
altms = list()

ref_logs = glob("./../logs/mcal*11.10*.csv")

for i in range(0, len(ref_logs)):
    print "Calculating...",
    print "    {}".format(ref_logs[i])
              
    __, st, __, __, f_spd1, r_spd1, f_spd2, r_spd2, cra, crb, T, Vpz, Vms, gamma_dot, tau, tag = read_logf(ref_logs[i])
    
    # mcal_[name]_[viscosity]_[date+time].csv
    v_term = ref_logs[i].split('_')[2]
    print "\tVisc. Term:", v_term
    viscosity = 0.0
    try:
        viscosity = float(v_term) # if is any of the 'smart' options, this will not work
    except:
        try:
            viscosity = resx.get_mu_of_T(v_term, T) # will not work if is mixture
        except:
            parts = v_term.split("@")
            viscosity = resx.get_mu_of_T(parts[0], T, parts[1]) # will not work if is wrong
    
    print "\tViscosity:", np.average(viscosity)
    
    ## filtering!
    Vms = filter(st, Vms)
    cra = filter(st, cra)
    
    I_MS = resx.get_current(cra)
    I_CO = resx.get_current_coil(Vms)
    I_EMF = [0.0] * len(I_MS)
    for j in range(0, len(I_MS)):
        I_EMF[j] = I_MS[j] - I_CO[j]
    aliemfs.extend(I_EMF)
    I_EMFs.append(np.mean(I_EMF))
            
    stress = viscosity * gamma_dot
    torque = resx.get_torque(stress, 15)
    #print "\tStrain:   ", np.average(gamma_dot)
    #print "\tStress:   ", stress
    #print "\tTorque:   ", torque
    #print "\tI emf :   ", I_EMFs[-1]
    altms.extend(torque)
    T_MSs.append(np.mean(torque))

#print T_MSs
#print I_EMFs
fit, f_eqn, mot_cal = plot_fit(I_EMFs, T_MSs, 1, x_name="Iemf", y_name="T")
f = plt.figure()
ax = f.add_subplot(111)
ax.plot(aliemfs, altms, "x")
ax.plot(I_EMFs, T_MSs, "o")
ax.plot(I_EMFs, fit)
#plt.show()
plt.savefig("trd.png")
print "New fit:"
print "\tT = Iemf * {} + {}".format(mot_cal[0], mot_cal[1])
