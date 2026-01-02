from .core import IPhysicsStrategy, InstrumentConfig
from .utils import FractionalDelay, StiffnessDispersion
import numpy as np
from scipy.signal import lfilter


class KarplusStrongAlgorithm(IPhysicsStrategy):
    def __init__(self, sample_rate :int = 44100, frequency:float=440.0, config: InstrumentConfig=InstrumentConfig()) -> None:
        self.sample_rate = sample_rate
        self.config = config
        self.frequency = frequency
        #self.decay_factor = decay_factor
        self.fractional_delay=FractionalDelay()
        self.stiffness = StiffnessDispersion(stiffness=config.stiffness)

        self.N = int(sample_rate / frequency)
        self.delay_line = np.zeros(2)
        self.ptr = 0


        self.set_frequency(frequency)

    def set_frequency(self, freq:float, sustain_time: float=4.0):
        self.frequency = freq

        ideal_T = self.sample_rate/freq
        stiffness_delay = self.stiffness.update_stiffness(self.config.stiffness, ideal_T*0.7-0.52)

        total_T = ideal_T-0.52-stiffness_delay
        if total_T<2.1:
            total_T =2.1
        self.N = int(total_T)

        residue = total_T - self.N
        self.frac_c = (1.0-residue)/(1.0+residue)
        target_gain = 10**(-3/(freq*sustain_time))
        w=2*np.pi*freq/self.sample_rate
        filter_gain = np.sqrt(0.48**2+0.52**2+2*0.48*0.52*np.cos(w))
        self.decay_factor= min(0.999,target_gain/filter_gain)
        if len(self.delay_line)!=self.N:
            self.delay_line = np.zeros(self.N)
            self.ptr =0
    
    def excite(self, velocity :float, cutoff_frequency:float=4000, pluck_position:float=0.2):
        white = np.random.uniform(-1.0, 1.0, self.N)

        # Filter into pink noise (1/f approx)
        # We use a simple integrator to boost the 'thump'  
        burst = np.zeros(self.N)
        last_val = 0
        for i in range(self.N):
            white[i] = (white[i] + (0.5 * last_val)) / 1.5 # Leaky itegrator
            last_val = white[i]
        burst = white

        pluck_samples = int(self.N * pluck_position)
        pluck_samples = max(1, min(pluck_samples, self.N -2))

        #combfilter: y[n] = x[n] - x[n-p]
        combed_burst = np.zeros(self.N)
        combed_burst[pluck_samples:] = burst[pluck_samples:]- burst[:-pluck_samples]
        combed_burst[:pluck_samples] = burst [:pluck_samples]


        alpha:float = (2.0* np.pi * cutoff_frequency) / (self.sample_rate+2.0*np.pi*cutoff_frequency)
        filtered_burst = lfilter([alpha], [1, -(1-alpha)],combed_burst)
        self.delay_line = filtered_burst * velocity
        self.ptr = 0


    def process(self, num_samples: int) -> np.ndarray:
        output = np.zeros(num_samples)

        local_delay = self.delay_line
        local_N = len(local_delay)
        local_ptr = self.ptr

        for i in range(num_samples):
            current_val = local_delay[local_ptr]
            output[i] = current_val

            next_ptr = (local_ptr +1) % local_N
            next_val = local_delay[next_ptr]
            lowpassed_val = (0.48* current_val +0.52*next_val) * self.decay_factor
            # ---Dispersion stiffness 
            stiff_val = self.stiffness.process_sample(lowpassed_val)

            y_n = self.fractional_delay.process_sample(stiff_val, self.frac_c)

            local_delay[local_ptr] = y_n
            local_ptr = next_ptr
            
        self.ptr = local_ptr
        return output

    def get_effective_frequency(self) -> float:
        frac_delay = (1.00 - self.frac_c) / (1.0+self.frac_c)
        stiffness_delay = self.stiffness.get_group_delay()

        total_period = self.N + frac_delay + stiffness_delay + 0.52
        return self.sample_rate / total_period
