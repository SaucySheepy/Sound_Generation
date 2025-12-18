import numpy as np 
import matplotlib.pyplot as plt
from scipy.signal import freqz
from app.app.engine import GuitarBody, AcousticGuitar

def analyze_body_resonance():
    print("Anaylyze: Guitar Body Impluse Response")
    fs = 44100
    duration = 1.0
    # Simulate white noise
    noise = np.random.uniform(-1,1, int(fs*duration))

    # Pass through body
    body = GuitarBody(fs)
    filtered_noise = body.process(noise)

    # FFT
    # We use Magnitude Spectrum to see which frequencies are boosted/cut
    plt.figure(figsize=(10,6))
    plt.psd(filtered_noise, NFFT=1024, Fs=fs, color='purple', label='Body Response')
    plt.axvline(100, color='r', linestyle='--', label='Helmholtz (100Hz)')
    plt.axvline(2000, color='g', linestyle='--', label = "Wood Cutoff (2khz)")
    plt.legend()
    plt.xlim(0, 5000)
    plt.show()

def analyze_string_harmonics():
    print("Analyze: String Spectrogram...")

    fs = 44100
    guitar = AcousticGuitar()
    guitar.play(110.0, 1.0)

    block = guitar.process_block(int(fs*2.0))

    plt.figure(figsize=(10,6))
    plt.specgram(block, NFFT=1024, Fs=fs, noverlap=512, cmap='inferno')
    plt.title("Spectrogram of A2 String (Harmonic Decay)")
    plt.ylabel("Frequency (Hz)")
    plt.xlabel("Time (s)")
    plt.ylim(0, 3000) 
    plt.colorbar(label='Intensity (dB)')
    plt.show()

if __name__ == "__main__":
    analyze_body_resonance()
    analyze_string_harmonics()
