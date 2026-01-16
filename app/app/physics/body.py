import numpy as np
from scipy.signal import lfilter, butter, lfilter_zi

class GuitarBody():
    def __init__(self, sample_rate : int = 44100, resonance_freq:float =100.0):
        self.sample_rate = sample_rate
        cutoff_hz = 3000
        nyquist = 0.5 * sample_rate
        normal_cutoff = cutoff_hz/nyquist
        

        # Design the Butterworth Filter coefficients (b,a)
        # b = feedforward coeffs, a = feedback coeffs
        self.b, self.a = butter(N=2, Wn=normal_cutoff, btype= 'low', analog=False)

        # Initialize the State Vector (zi) to zeros
        # This memory vector keeps the filter continuous across blocks
        self.zi = lfilter_zi(self.b, self.a)
        
        #Helmholtz filter
        self.bp_b, self.bp_a = butter(N=2, Wn = [(resonance_freq-20)/nyquist, (resonance_freq+20)/nyquist],btype = 'bandpass', analog =False)
        self.bp_zi = lfilter_zi(self.bp_b, self.bp_a)

        #Simulating white noise
        self.noise_gain = 0.0002
        


    def process(self, signal: np.ndarray) -> np.ndarray:
        # Apply the filter with state preservaction
        # input: signal + current_state (self.zi)
        # output: filtered_signal + new_state (self.zf)

        #Apply Wood Damping (low Pass) 
        filtered_signal, self.zf = lfilter(self.b, self.a, signal, zi=self.zi)
        self.zi = self.zf
        #Apply Helmholtz Resonance (Bandpass)
        boom, self.bp_zf = lfilter(self.bp_b, self.bp_a, signal, zi=self.bp_zi)
        self.bp_zi = self.bp_zf

        raw_output = filtered_signal + (boom*1.5)

        noise = np.random.normal(0, self.noise_gain, size=signal.shape)
        raw_output += noise
        return np.tanh(raw_output)
