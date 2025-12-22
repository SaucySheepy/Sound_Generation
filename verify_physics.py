import numpy as np 
import matplotlib.pyplot as plt
from scipy.signal import welch
from app.app.engine import KarplusStrongAlgorithm, AcousticGuitar

class PhysicsLab:
    def __init__(self, target_freq=82.41, target_sustain=4.0):
        self.fs = 44100
        self.target_freq = target_freq
        self.target_sustain = target_sustain
        
        # 1. Generate the instrument and data
        print (f"--- Physical Modeling Lab: {target_freq}Hz ---")
        self.guitar = AcousticGuitar()
        self.guitar.play(target_freq, velocity = 1.0, sustain_time = target_sustain)

        # Capture 5 sec of audio
        self.audio = np.array(self.guitar.process_block(int(5.0*self.fs)))
        self.left = self.audio[:,0]
        self.right = self.audio[:,1]

        # Prepare spectral data once
        start_idx = int(0.2*self.fs)
        self.freqs, self.psd = welch(self.left[start_idx:start_idx+self.fs], self.fs, nperseg=16384)

    def _interpolate_peak(self, psd, peak_idx, freqs):
        """Uses parabolic interpolation to find the true peak between bins"""
        if peak_idx <=0 or peak_idx >= len(psd)-1:
            return freqs[peak_idx]

        # Get amplitude of peak and neighbours
        alpha = psd[peak_idx-1]
        beta = psd[peak_idx]
        gamma = psd[peak_idx+1]

        # Calculate offset(-0.5 to +0.5 bins)
        p= 0.5*(alpha-gamma) /(alpha -2* beta + gamma)

        # Return frequency adjusted by offset
        bin_width = freqs[1] - freqs[0]
        return freqs[peak_idx] + (p*bin_width)


    def test_tuning(self):
        ''' Measures frequency accuracy(Fundamental vs Target)'''
        search_range = (self.freqs> self.target_freq -100) & (self.freqs<self.target_freq+100)
        peak_idx = np.argmax(self.psd[search_range])
        measured_freq = self.freqs[search_range][peak_idx]

        error = 1200*np.log2(measured_freq / self.target_freq)
        print(f"[TUNING] Error : {error:.2f} cents ({measured_freq:.1f}Hz)")
        return error

    def test_sustain(self):
        '''Measures T60 decay time (ignoring the initial click)'''
        start_idx = int(0.1 * self.fs)
        sustain_part = np.abs(self.left[start_idx:])

        # Smooth and convert to dB
        window = int(0.01 * self.fs)
        smoothed = np.convolve(sustain_part, np.ones(window)/window, mode='same')
        env_db = 20* np.log10(smoothed +1e-9)
        threshold = np.max(env_db) - 60.0

        crossings = np.where(env_db < threshold)[0]
        t60 = ((crossings[0] + start_idx) / self.fs) if len(crossings) >0 else 5.0
        print(f"[SUSTAIN] T60:  {t60:.1f}s (Target: {self.target_sustain}s)")
        return t60

    def test_stereo_width(self):
        '''Measures L/R correlation (Width of the body)'''
        correlation = np.corrcoef(self.left, self.right)[0,1]
        print(f"[STEREO] Width: {correlation:.4f} (Correlation)")
        return correlation

    def test_timbre(self):
        '''Measures the damping effect of the wooden body'''
        f1_power = np.max(self.psd)
        f2_target = self.target_freq *2
        f2_range = (self.freqs > f2_target -10) & (self.freqs< f2_target +10)
        f2_power = np.max(self.psd[f2_range])

        ratio = 10*np.log10(f1_power/f2_power)
        print(f"[TIMBRE] Wood: {ratio:.1f} dB (Harmonic Drop)")
        return ratio

    def plot_results(self):
        '''Visualizes the spectral and temporal profile'''
        plt.figure(figsize=(10,8))

        plt.subplot(2,1,1)
        plt.title("Spectral Profile")
        plt.semilogy(self.freqs, self.psd)
        plt.xlim(0,2500) 
        plt.grid(True)

        plt.subplot(2,1,2)
        env = 20 * np.log10(np.abs(self.left) + 1e-9)
        plt.plot(np.arange(len(env))/self.fs, env)
        plt.title("Temporal Profile (Decay)")
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()

    def plot_spectrogram(self):
        """Visualizes how harmonics die out over time (The Waterfall)"""
        plt.figure(figsize=(10,6))
        # We use a logarithmic scale for the frequencies to see the 'Notes'
        power_spectrum, frequencies, times, image = plt.specgram(self.left, Fs=self.fs, NFFT=4096, noverlap=2048, cmap='magma')

        plt.ylim(0,3000)
        plt.ylabel('Frequency [Hz]')
        plt.xlabel('Time [sec]')
        plt.title('Harmonic Delay Waterfall (Wood Character)')
        plt.colorbar(label = 'Intensity [dB]')
        plt.show()

    def test_inharmonicity(self):
        """Measures the stretching of harmonics (stiffness check)"""
        # Find Fundamental
        search_range_f1 = (self.freqs>self.target_freq-50) & (self.freqs < self.target_freq +50)
        
        local_idx = np.argmax(self.psd[search_range_f1])
        global_idx = np.where(search_range_f1)[0][local_idx]
        f1 = self._interpolate_peak(self.psd, global_idx, self.freqs)

        # Find 4th harmonic (f4) - It should be theoretically at f1*4
        target_f4 = f1*4

        search_range_f4 = (self.freqs > target_f4 - 50) & (self.freqs<target_f4 + 50)
        if np.any(search_range_f4):
            local_idx4 = np.argmax(self.psd[search_range_f4])
            global_idx4 = np.where(search_range_f4)[0][local_idx4]
            f4 = self._interpolate_peak(self.psd, global_idx4, self.freqs)
            # Ideal Ratio = 4.0 Real Stiff Ratio >4.0
            ratio = f4/f1
            print(f"[STIFFNESS] Harmonic Stretch (f4/f1): {ratio:.5f} (Ideal:4.0000)")
            diff_cents = 1200*np.log2(ratio/4.0)
            print(f"Deviation: {diff_cents:.2f} cents")
            return ratio
        else:
            print("Could not find 4th harmonic.")
            return 0.0
    
if __name__ == "__main__":
    lab = PhysicsLab(target_freq=82.41, target_sustain=4.0)
    lab.test_tuning()
    lab.test_sustain()
    lab.test_stereo_width()
    lab.test_timbre()
    lab.plot_results()
    lab.plot_spectrogram()
    lab.test_inharmonicity()

    