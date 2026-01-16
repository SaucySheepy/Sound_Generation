from abc import ABC, abstractmethod
import numpy as np
from dataclasses import dataclass, field

@dataclass
class InstrumentConfig:
    pickup_positions: list[float] = field(default_factory=lambda: [0.2])  # 0.0 = Bridge (Acoustic), 0.2 = Neck (Electric)
    use_bridge_output: bool = False # True = Listen to force (Acoustic), False = Listen to displ (Electric)
    string_damping: float = 0.999 # Metal vs Nylon
    pluck_width: int = 10         # 10 = Sharp, 40 = Soft Finger
    stiffness:float = -0.2  
      
class IPhysicsStrategy(ABC):
    @abstractmethod
    def set_frequency(self, freq:float, sustain_time: float=4.0) : 
        pass

    @abstractmethod
    def excite(self, velocity:float, cutoff_frequency:float=4000, pluck_position:float=0.2):
        pass

    @abstractmethod
    def process(self, num_samples:int) -> np.ndarray:
        pass

def note_to_freq(note:str)-> float:
    notes: dict[str, int] = {"A":9, "A#":10, "B":11, "C":0,"C#":1, "D":2, "D#":3,"E":4, "F":5, "F#":6, "G":7, "G#":8}
    octave = int(note[-1])
    octave_multiplier: int = 12 * (octave+1)
    n: int = notes[note[:-1]]+octave_multiplier
    frequency = 440.0 * (2.0 ** ((n - 69) / 12.0))
    return frequency

class Instrument:
    def __init__(self, name:str, strategy: IPhysicsStrategy):
        self.name = name
        self.strategy = strategy
    
    def play(self, frequency:float, velocity:float):
        self.strategy.set_frequency(frequency)
        self.strategy.excite(velocity)

    def process_block (self, num_samples):
        #Delegate the math to the strategy
        return self.strategy.process(num_samples)
