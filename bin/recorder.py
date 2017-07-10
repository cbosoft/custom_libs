import pyaudio
import wave
import thread as td

class recorder(object):

    def __init__(self, channels=1, rate=44100, chunk=1024):
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.audio = pyaudio.PyAudio()
        self.recording = False
        self.outname = ""
        
    def start_recording(self, output_name):
        self.recording = True
        self.outname = output_name
        td.start_new_thread(self.rec_str, tuple())
        self.stream = self.audio.open(format=pyaudio.paInt16, channels=self.channels,
                rate=self.rate, input=True,
                frames_per_buffer=self.chunk)
        self.frames = []
    
    def stop_recording(self):
        self.recording = False
        
    def rec_str(self):
        while (self.recording):
            data = self.stream.read(self.chunk)
            self.frames.append(data)
            
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        
        waveFile = wave.open(self.outname, 'wb')
        waveFile.setnchannels(self.channels)
        waveFile.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        waveFile.setframerate(self.rate)
        waveFile.writeframes(b''.join(self.frames))
        waveFile.close()
