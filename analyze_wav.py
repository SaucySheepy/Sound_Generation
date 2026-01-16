import numpy as np
from scipy.io import wavfile
from scipy.signal import welch

def analyze_freq(file_path):
    print(f"Analyzing: {file_path}")
    sr, data = wavfile.read(file_path)
    
    # Convert to Mono
    if len(data.shape) > 1:
        data = np.mean(data, axis=1)
        
    # Convert to float
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
        
    fs = sr
    # Use Welch for stable PSD
    freqs, psd = welch(data, fs, nperseg=16384)
    
    # Find the peak (Fundamental)
    # Filter out very low freq noise below 40Hz
    valid_range = freqs > 40
    peak_idx = np.argmax(psd[valid_range])
    fundamental = freqs[valid_range][peak_idx]
    
    # Refined peak search using parabolic interpolation
    # Find global idx
    global_idx = np.where(freqs == fundamental)[0][0]
    if 0 < global_idx < len(psd) - 1:
        alpha = psd[global_idx-1]
        beta = psd[global_idx]
        gamma = psd[global_idx+1]
        p = 0.5 * (alpha - gamma) / (alpha - 2*beta + gamma)
        fundamental += p * (freqs[1] - freqs[0])

    print(f"Fundamental Frequency: {fundamental:.2f} Hz")
    
    # Map to nearest note
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    semitones = 12 * np.log2(fundamental / 440.0) + 69
    note_idx = int(round(semitones)) % 12
    octave = int(round(semitones)) // 12 - 1
    
    print(f"Estimated Note: {notes[note_idx]}{octave}")

if __name__ == "__main__":
    analyze_freq("test_files\\d.wav")
