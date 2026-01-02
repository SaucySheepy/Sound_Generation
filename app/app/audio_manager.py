import sounddevice as sd
import numpy as np 
from .instruments.acoustic_guitar import AcousticGuitar
import threading

class AudioManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(AudioManager, cls).__new__(cls)
                    cls._instance.initialized = False
        return cls._instance

    def initialize(self):
        if self.initialized:
            return
        print("Initializing Audio Manager")
        self.fs = 44100
        self.model = AcousticGuitar()

        self.current_freq = 440.0
        self.current_decay = 0.99
        self.current_sustain= 4.0
        self.stream = sd.OutputStream(
            channels =2,
            samplerate = self.fs,
            callback = self._audio_callback
        )
        self.stream.start()
        self.initialized = True

    def _audio_callback(self, outdata, frames, time, status):
        if status:
            print(status)
        block = self.model.process_block(frames)
        outdata[:] = block

    def pluck(self):
        if self.initialized:
            self.model.play(self.current_freq, velocity=1.0, sustain_time = self.current_sustain)

    def _perform_strum(self, note_freqs:list[float], duration:float, direction:str):
        sorted_freqs=sorted(note_freqs)
        if direction == 'up':
            sorted_freqs.reverse()

        num_strings = len(sorted_freqs)
        if num_strings ==0: return

        delay_per_string = duration/ max(1, num_strings -1)

        import time
        for i, freq in enumerate(sorted_freqs):
            # Humanize velocity: 0.8 to 1.0
            vel = np.random.uniform(0.8, 1.0)
            if i == 0 : vel = 1.0

            self.model.play(freq,vel, sustain_time=self.current_sustain)
            if i<num_strings -1:
                time.sleep(delay_per_string)

    def strum(self, note_freqs: list[float], duration :float=0.05, direction: str = 'down'):
        """Plays a chord (list of frequencies) simultaneously."""
        if self.initialized:
            threading.Thread(target=self._perform_strum, args=(note_freqs,duration, direction), daemon=True).start()           

    def set_synthesis_mode(self, mode:str):
        if self.initialized:
            self.model.set_synthesis_strategy(mode)

    def set_frequency(self, freq):
        if self.initialized:
            self.current_freq = freq

    def set_sustain(self, sustain_seconds):
        if self.initialized:
            ss = 10*(sustain_seconds -0.5)/(0.5) +0.1

            self.current_sustain = ss

            for string in self.model.strings:
                string.set_frequency(string.frequency, sustain_time=ss)

    def set_resonance(self, enabled:bool):
        if self.initialized:
            self.model.resonance_enabled = enabled

    def set_stiffness(self, stiffness_val:float):
        if self.initialized:
            print(f"Setting stiffness to {stiffness_val}")
            for string in self.model.strings:
                if hasattr(string, 'stiffness'):
                    string.stiffness.a = stiffness_val
                string.set_frequency(string.frequency, sustain_time = self.current_sustain)

    def get_effective_frequency(self) -> float:
        if self.initialized:
            return self.model.get_effective_frequency()
        return 0.0

audio_manager = AudioManager()
        