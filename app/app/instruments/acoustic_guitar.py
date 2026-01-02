import numpy as np
from ..physics.core import Instrument, note_to_freq, InstrumentConfig
from ..physics.body import GuitarBody
from ..physics.dwg import DigitalWaveguideStrategy
from ..physics.karplus_strong import KarplusStrongAlgorithm

class AcousticGuitar(Instrument):
    def __init__(self):
        # We now import components from the physics package!
        self.body_left = GuitarBody(sample_rate = 44100, resonance_freq=95.0)
        self.body_right = GuitarBody(sample_rate = 44100, resonance_freq=105.0)
        
        tuning_notes = ["E2", "A2", "D3", "G3", "B3", "E4"]
        self.body = GuitarBody(sample_rate=44100)
        self.strings = []
        self.last_string = None
        self.open_frequencies = [] 
        self.resonance_enabled = True

        # ACOUSTIC PRESET (Default)
        acoustic_config = InstrumentConfig(
            pickup_positions=0.0, 
            use_bridge_output=True, 
            pluck_width=40,
            string_damping=0.997
        )

        for note in tuning_notes:
            freq = note_to_freq(note)
            self.open_frequencies.append(freq)
            # Pass the config to the strategy
            self.strings.append(DigitalWaveguideStrategy(sample_rate=44100, frequency=freq, config=acoustic_config))

        super().__init__("Acoustic Guitar", self.strings[0])

    def set_synthesis_strategy(self, strategy_name:str):
        """Swaps the physics engine for all strings."""
        new_strings = []
        for freq in self.open_frequencies:
            if strategy_name == "Digital Waveguide":
                s= DigitalWaveguideStrategy(sample_rate = 44100, frequency = freq, config=self.strings[0].config)
            elif strategy_name == "Karplus Strong":
                s= KarplusStrongAlgorithm(sample_rate = 44100, frequency = freq, config=self.strings[0].config)
            new_strings.append(s)
        self.strings = new_strings
        self.last_string = self.strings[0]

    def set_instrument_config(self, mode: str):
        if mode == "Acoustic":
            config = InstrumentConfig(
                pickup_positions=0.0, 
                use_bridge_output=True, 
                pluck_width=40,
                string_damping=0.999
            )
        else: # Electric
            config = InstrumentConfig(
                pickup_positions=0.2, 
                use_bridge_output=False, 
                pluck_width=10,
                string_damping=0.999
            )
            
        for s in self.strings:
            if hasattr(s, 'config'):
                s.config = config
    
    def play(self, target_freq:float, velocity:float, sustain_time:float=4.0):
        best_string_index = 0
        min_dist = 100000.0

        for i,open_freq in enumerate(self.open_frequencies):
            if open_freq <= target_freq +1.0:
                dist = target_freq - open_freq
                if dist<min_dist:
                    min_dist = dist
                    best_string_index = i
            
        selected_strategy = self.strings[best_string_index]
        selected_strategy.set_frequency(target_freq,sustain_time=sustain_time)
        selected_strategy.excite(velocity)
        self.last_string = selected_strategy
        # Direct Body Kick
        kick = np.random.uniform(-0.1,0.1,100) * velocity
        self.body_left.process(kick)
        self.body_right.process(kick)
        
    def process_block(self, num_samples:int):
        raw_string_sound=np.zeros(num_samples)
        for s in self.strings:
            raw_string_sound += s.process(num_samples)
        if self.resonance_enabled:
            left = self.body_left.process(raw_string_sound)
            right = self.body_right.process(raw_string_sound)
            final_sound = np.vstack((left,right)).T
        else:
            final_sound = np.vstack((raw_string_sound, raw_string_sound)).T

        return final_sound*0.3

    def get_effective_frequency(self) -> float:
        """Returns the actual frequency of the last string played."""
        if self.last_string:
            return self.last_string.get_effective_frequency()
        return 0.0