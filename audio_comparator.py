import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import welch

class AudioComparator:
    """
    Utility class to load and analyze reference audio for comparison 
    against synthetic models.
    """
    def __init__(self, sample_rate: int = 44100):
        self.fs = sample_rate
        self.ref_audio = None
        self.ref_sr = sample_rate # Track actual SR of the file
        self.ref_freqs = None
        self.ref_psd = None
        self.filename = None

    def load_reference(self, file_path: str):
        """Loads and normalizes a reference WAV file."""
        print(f"Loading reference: {file_path}")
        self.filename = file_path
        
        try:
            sr, data = wavfile.read(file_path)
            
            # Convert to float32 and normalize
            if data.dtype == np.int16:
                data = data.astype(np.float32) / 32768.0
            elif data.dtype == np.int32:
                data = data.astype(np.float32) / 2147483648.0
                
            # Convert to Mono if Stereo
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
                
            # Basic normalization
            data = data / (np.max(np.abs(data)) + 1e-9)
            
            # Store the actual sample rate!
            self.ref_sr = sr
            if sr != self.fs:
                print(f"Note: Reference SR {sr} differs from target {self.fs}. Aligning spectra...")
            
            self.ref_audio = data
            self._compute_psd()
            return True
        except Exception as e:
            print(f"Error loading reference: {e}")
            return False

    def _compute_psd(self):
        """Computes the Power Spectral Density using the file's native sample rate."""
        # Skip the initial transient for a cleaner spectrum
        start_idx = int(0.2 * self.ref_sr)
        # Use 1 second of audio or whatever is available
        end_idx = min(len(self.ref_audio), start_idx + self.ref_sr)
        
        if end_idx <= start_idx:
            print("Reference audio too short for spectral analysis.")
            return

        # Crucial: Use self.ref_sr here so the Hz axis is accurate!
        self.ref_freqs, self.ref_psd = welch(
            self.ref_audio[start_idx:end_idx], 
            self.ref_sr, 
            nperseg=16384
        )

    def plot_comparison(self, synth_freqs, synth_psd, target_label="Synthetic"):
        """Plots the synth PSD against the reference PSD."""
        if self.ref_psd is None:
            print("No reference audio loaded for comparison.")
            return
        plt.clf()
        plt.figure(figsize=(12, 6))
        plt.title(f"Spectral Match: {self.filename} vs {target_label}")
        
        # Plot Synthetic
        plt.semilogy(synth_freqs, synth_psd, label=target_label, color='cyan', alpha=0.8)
        
        # Plot Reference
        plt.semilogy(self.ref_freqs, self.ref_psd, label='Reference (Real)', color='orange', alpha=0.6, linestyle='--')
        
        plt.xlim(0, 4000)
        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Intensity (dB)")
        plt.legend()
        plt.grid(True, which='both', alpha=0.2)
        plt.tight_layout()
        plt.show()
