from abc import ABC, abstractmethod
from scipy.signal import lfilter, butter, lfilter_zi
import numpy as np

class IPhysicsStrategy(ABC):
    @abstractmethod
    def set_frequency(self, freq:float) : 
        pass

    @abstractmethod
    def excite(self, velocity:float):
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

class StiffnessDispersion:
    def __init__(self, stiffness:float=-0.7):
        self.a = stiffness
        # Cascade of 4 All-Pass Filters
        # We need independent memory for each stage
        self.x_prev = [0.0] * 4
        self.y_prev = [0.0] * 4 

    def process_sample(self, input_val:float) ->float:
        current_input = input_val
        for i in range(4):
            output = (self.a * current_input) + self.x_prev[i] - (self.a * self.y_prev[i])
            # Update history for this stage
            self.x_prev[i] = current_input
            self.y_prev[i] = output

            # The output of this stage becomes the input for the next 
            current_input = output
        return current_input


class KarplusStrongAlgorithm(IPhysicsStrategy):
    def __init__(self, sample_rate :int = 44100, frequency:float=440.0, decay_factor:float=0.99) -> None:
        self.sample_rate = sample_rate
        self.frequency = frequency
        self.decay_factor = decay_factor

        self.N = int(sample_rate / frequency)
        self.delay_line = np.zeros(self.N)
        self.ptr = 0
        self.ap_x_prev = 0.0
        self.ap_y_prev = 0.0
        self.C = 0.0
        self.stiffness = StiffnessDispersion(stiffness=-0.7)
        self.set_frequency(frequency)

    def set_frequency(self, freq:float, sustain_time: float=4.0):
        self.frequency = freq

        if freq < 600.0:
            ratio = 1.0 - (freq/600.0)
            current_stiffness = -0.7*ratio
        else:
            current_stiffness = 0.0

        self.stiffness.a = current_stiffness

        # --Delay Compensation--
        # We must subtract the filter's group delay from the string length
        # Formula: Delay = 4 Stages * (1-a)/(1+a)
        s = current_stiffness
        if s!=0.0:
            stiffness_delay = 4.0 * (1.0-s)/(1.0+s)
        else:
            stiffness_delay = 0.0
        
        N_total = (self.sample_rate /freq) +0.52 - stiffness_delay
        if N_total<2:
            N_total =2
        self.N = int(N_total)

        alpha = N_total - self.N
        self.C = (1.0 - alpha) / (1.0 + alpha)

        target_gain = 10**(-3/(freq*sustain_time))
        # Filter Gain Compensation (The Magic Step)
        # We calculate the gain of : 0.48*x + 0.52*x_prev (This is used in the lowpass filter)
        w = 2*np.pi*freq/self.sample_rate
        filter_gain = np.sqrt(0.48**2+0.52**2+2*0.48*0.52*np.cos(w))
        self.decay_factor = min(0.999, target_gain/filter_gain)

        if len(self.delay_line) != self.N:
            self.delay_line = np.zeros(self.N)
            self.ptr = 0
            self.ap_x_prev = 0.0
            self.ap_y_prev = 0.0
    
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
        # has issues with tuning. We can add Fractional Delay later to improve this 
        output = np.zeros(num_samples)

        local_delay = self.delay_line
        local_N = len(local_delay)
        local_ptr = self.ptr%local_N

        for i in range(num_samples):
            current_val = local_delay[local_ptr]
            output[i] = current_val

            next_ptr = (local_ptr +1) % local_N
            next_val = local_delay[next_ptr]
            lowpassed_val = (0.48* current_val +0.52*next_val) * self.decay_factor
            # ---Dispersion stiffness 
            stiff_val = self.stiffness.process_sample(lowpassed_val)

            x_n = stiff_val
            y_n = (self.C * x_n) + self.ap_x_prev - (self.C * self.ap_y_prev)

            # Update Filter History
            self.ap_x_prev = x_n
            self.ap_y_prev = y_n

            local_delay[local_ptr] = y_n
            local_ptr = next_ptr
        
        self.ptr = local_ptr
        return output


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

        return filtered_signal + (boom *20.0)

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


class AcousticGuitar(Instrument):
    def __init__(self):

        self.body_left = GuitarBody(sample_rate = 44100, resonance_freq=95.0)
        self.body_right = GuitarBody(sample_rate = 44100, resonance_freq=105.0)
        tuning_notes = ["E2", "A2", "D3", "G3", "B3", "E4"]
        self.body = GuitarBody(sample_rate=44100)
        self.strings = []
        self.open_frequencies = [] # Remember the "Open" pitch of each string
        self.resonance_enabled = True
        for note in tuning_notes:
            freq = note_to_freq(note)
            self.open_frequencies.append(freq)
            self.strings.append(KarplusStrongAlgorithm(sample_rate=44100, frequency=freq))

        super().__init__("Acoustic Guitar", self.strings[0])

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

        # Direct Body Kick
        # We 'Kick' the body resonance with a tiny burst of energy when the note starts. Adds a thump to high notes
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
            # Combine into (N,2) array
            final_sound = np.vstack((left,right)).T
        else:
            final_sound = np.vstack((raw_string_sound, raw_string_sound)).T

        return final_sound*0.3


