import sys
sys.path.append("./../../bin")

from filter import filter
import matplotlib.pyplot as plt
import numpy as np
from glob import glob

# Read csv
#datf = open("./../../logs/pulley_test/smallx4.csv", "r")
datf = open("./../../logs/long_cal.csv", "r")
datl = datf.readlines()
datf.close()

# Create lists for sorting

rv = [0] * 0
t = [0] * 0
st = [0] * 0
pv = [0] * 0

splt = datl[1].split(",", 5)
tz = float(splt[0])

for i in range(1, len(datl)):
    splt = datl[i].split(",", 5)
    t.append(float(splt[0]))
    st.append(float(splt[0]) - tz)

    rv.append(float(splt[1]))
    pv.append(int(splt[3]))

rv = filter(st, rv, method="butter", A=2, B=0.0001)

# Read csv
datf = open("./../../logs/voltvval.csv", "r")
datl = datf.readlines()
datf.close()

# Create lists for sorting
av_volt = [0] * 0
av_spd = [0] * 0
p2v = [0] * 0
std = [0] * 0

for i in range(2, len(datl)):
    splt = datl[i].split(",", 13)
    av_volt.append(float(splt[6]))
    av_spd.append(float(splt[12]))
    p2v.append(float(splt[0]))
    std.append(np.std(np.array([float(splt[7]), float(splt[8]), float(splt[9]), float(splt[10]), float(splt[11])])))

av_speed_long = [0] * 0


#print pv

cur_pv = pv[0]
pv_indx = 0
for i in range(0, len(pv)):
    for j in range(0, len(p2v)):
        if (pv[i] - p2v[j]) < 8 and (pv[i] - p2v[j]) >= 0:
            #print pv[i] - p2v[j]
            pv_indx = j
    av_speed_long.append(av_spd[pv_indx])

tot_rvs = [[0] * 0] * len(p2v)
print tot_rvs
av_rvs = np.array([0] * len(p2v))
for i in range(0, len(pv)):
    for j in range(0, len(p2v)):
        if pv[i] == p2v[j]:
            print tot_rvs[j], j
            tot_rvs[j].append(rv[i])
            #print tot_rvs, j, rv[i]
            r = raw_input()
print min(tot_rvs[4]), max(tot_rvs[4])

stdv = [0] * 0
for i in range(0, len(tot_rvs)):
    stdv.append(np.std(tot_rvs[i]))
    av_rvs[i] = np.average(tot_rvs[i])

    
# 1st Trend: speed as a function of potval
zavspdpv = np.polyfit(p2v[4:], av_spd[4:], 1)
tlo = np.poly1d(zavspdpv)

# Speed v Val  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #
# Set up figure
f = plt.figure(figsize=(8, 8))
ax = f.add_subplot(111)

# 2nd Trend: read voltage as a function of potval
z = np.polyfit(pv, rv, 1)
tl = np.poly1d(z)

# 3rd Trend: speed as a function of read voltage
z3z = np.polyfit(tl(pv), tlo(pv), 1)
t3l = np.poly1d(z3z)

# Plot data and trendline
#ax.plot(rv, av_speed_long, 'o', label="$Recorded\ Speed$")
#ax.plot(tl(pv), t3l(tl(pv)), 'r--', label="$v_{2} = {0:.3f} V_D {1:.3f}$".format(z3z[0], z3z[1], "{NL}"))

ax.errorbar(av_rvs, av_spd, yerr=std, xerr=stdv, linestyle='None', marker='o')

ax.set_xlabel("\n $Read\ Voltage,\ V$", ha='center', va='center', fontsize=24)
ax.set_ylabel("$Speed,\ RPM$\n", ha='center', va='center', fontsize=24)

# Show Legend
#plt.legend()

# Show plot
plt.grid(which='both', axis='both')
plt.savefig("./fig_speed_v_rvolt.png")
plt.close(f)
