# plots a most lovely figure showing how well the final filter choice works

import sys

sys.path.append('./../../bin')

from filter import filter
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

def filterff(path_file):
    datf = pd.read_csv(path_file)
    
    st = np.array(datf['t'])
    st = st - float(st[0])
    
    dr = np.array(datf['dr'])
    
    drf = filter(st, dr, method="butter", A=2, B=0.0001)
    return st, dr, drf

def get_ft(x, y, f):
    # get spectra
    dt = x[-1] / len(x)
    # get frequency range (x)
    w = np.fft.fftfreq(len(x), d=dt)
    w = np.abs(w[:((len(x) / 2) + 1)])
    # get fourier transform of noisy signal (y1)
    ft = np.fft.rfft(y)
    ps_n = np.real(ft*np.conj(ft))*np.square(dt)
    # get fourier transform of filtered signal (y2)
    ft = np.fft.rfft(f)
    ps_f = np.real(ft*np.conj(ft))*np.square(dt)  
    return w, ps_n, ps_f
    
def fftnoise(f):
    f = np.array(f, dtype='complex')
    Np = (len(f) - 1) // 2
    phases = np.random.rand(Np) * 2 * np.pi
    phases = np.cos(phases) + 1j * np.sin(phases)
    f[1:Np+1] *= phases
    f[-1:-1-Np:-1] = np.conj(f[1:Np+1])
    return np.fft.ifft(f).real

def band_limited_noise(min_freq, max_freq, samples=1024, samplerate=1):
    freqs = np.abs(np.fft.fftfreq(samples, 1/samplerate))
    f = np.zeros(samples)
    idx = np.where(np.logical_and(freqs>=min_freq, freqs<=max_freq))[0]
    f[idx] = 1
    return fftnoise(f)

if __name__ == "__main__":
    # test script for testing
    # wiener averages too much and loses data
    # don't use spline - graphical method has little correlation to actual data
    # (tuned) butterworth seems to work well (A=2, nyf=0.05  

    # load up some noisy data
    # normal run (1)
    x1, y1, f1 = filterff("./../../logs/std_sweep.csv")
    # intermittent load
    x2, y2, f2 = filterff("./../../logs/intermittent_load_short.csv")
    
    # Set up figure
    f = plt.figure(figsize=(16, 16))
    ax_tl = f.add_subplot(221)
    plt.title("$a)\ Steady\ Speed\ Increase$\n", fontsize=24)
    ax_tr = f.add_subplot(222)
    plt.title("$c)\ Frequency\ Spectra\ (Fourier\ Transform)$\n", fontsize=24)
    ax_b = f.add_subplot(212)
    plt.title("$b)\ Intermittent\ Loading$", fontsize=24)
    
    # get spectra
    noise = band_limited_noise(10, 10, samples=len(y1))
    y_noisy = y1 + noise
    w, ps_n, ps_f = get_ft(x1, y_noisy, f1)

    # Plot data and trendline
    ax_tl.plot(x1, y1, 'b', color=(0,0,1,0.2))
    ax_tl.plot(x1, f1, 'b')
    ax_tl.set_xlabel("\n $Time,\ s$", ha='center', va='center', fontsize=24)
    ax_tl.set_ylabel("$Speed,\ RPM$\n", ha='center', va='center', fontsize=24)
    
    ps_offs = 0
    #ax_tr.set_ylim([0, 500000])
    ax_tr.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.1e'))
    
    ax_tr.plot(w[ps_offs:], ps_n[ps_offs:len(w)], 'b', color=(0,0,1,0.2))
    ax_tr.plot(w[ps_offs:], ps_f[ps_offs:len(w)], 'b')
    ax_tr.set_xlabel("\n $Frequency,\ Hz$", ha='center', va='center', fontsize=24)
    ax_tr.set_ylabel("", ha='center', va='center', fontsize=24)

    ax_b.plot(x2, y2, 'b', color=(0,0,1,0.2))
    ax_b.plot(x2, f2, 'b')
    ax_b.set_xlabel("\n $Time,\ s$", ha='center', va='center', fontsize=24)
    ax_b.set_ylabel("$Speed,\ RPM$\n", ha='center', va='center', fontsize=24)

    #plt.title("$Filter\ Type:\ {0}$".format(method), fontsize=20)

    # Save plot
    plt.grid(which='both', axis='both')
    plt.savefig("./fig_filt_demonstra.png")
    plt.close(f)
