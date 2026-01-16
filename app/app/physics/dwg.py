from alembic.command import current
from typing import override
from .core import IPhysicsStrategy, InstrumentConfig
from .utils import FractionalDelay, LowPassFilter, StiffnessDispersion
import collections
import numpy as np


#Configurables
# Alpha for low pass filter
# Listening at pickup versus listening at bridge (electric versus acoustic apparently)
# location of pickups in pct
# Comb filter ?
# Pluck position
# velocity
# Stiffness
# Decay factor

class DigitalWaveguideStrategy(IPhysicsStrategy):
    def __init__(self, sample_rate = 44100, frequency:float = 440.0, config :InstrumentConfig = InstrumentConfig()):
        self.sample_rate = sample_rate
        self.config = config
        self.decay_factor = config.string_damping

        self.frequency = 0.0
        self.buffer_size = int(self.sample_rate/(frequency*2))
        self.max_size = 4096
        self.right_buffer = [0.0] * self.max_size
        self.left_buffer = [0.0]  * self.max_size

        self.ptr = 0
        self.prev_output = 0.0
        self.ap_x_prev = 0.0
        self.ap_y_prev = 0.0

        #Initialize our utility objects
        self.fractional_delay = FractionalDelay()
        self.damping_filter = LowPassFilter(alpha=0.2)
        self.stiffness = StiffnessDispersion(stiffness = config.stiffness)

        self.pickup_locations = {
            "bridge":[0.08],
            "neck":[0.35],
            "middle":[0.2],
            "bridge+middle":[0.08, 0.2],
            "middle+neck":[0.2,0.35],
            "all":[0.08,0.2,0.35]
        }

        self.set_frequency(frequency)
    @override
    def set_frequency(self, frequency:float=440.0,sustain_time:float=4.0):
        self.frequency = frequency
        self.current_damping = 10**(-3/(frequency*sustain_time))

        if frequency > 600.0:
            new_alpha = 0.08
        elif frequency < 300.0:
            new_alpha = 0.2
        else:
            ratio = (frequency - 300.0) / 300.0
            new_alpha = 0.2 - (0.12*ratio)
        self.damping_filter.set_alpha(new_alpha)
         
        ideal_N = (self.sample_rate/frequency)/2.0
        stiffness_delay = self.stiffness.update_stiffness(self.config.stiffness, ideal_N*0.7-1.0)
        fixed_delays = 1.0+stiffness_delay
        total_N = ideal_N-(0.5*fixed_delays) # The -1.0 is for damping filter
        if total_N<1.1:
            total_N=1.1
        self.buffer_size = int(total_N)
        residue = total_N - self.buffer_size
        self.frac_c = (1.0-(2.0*residue))/(1.0 + (2.0*residue))

        if self.buffer_size >= self.max_size:
            extension = [0.0] * (self.buffer_size - self.max_size +100)
            self.right_buffer.extend(extension)
            self.left_buffer.extend(extension)
            self.max_size = len(self.right_buffer)

        return
    
    def get_displacement_at(self, ratio:float):
        idx = (self.ptr + int(self.buffer_size * ratio)) % self.buffer_size
        return self.right_buffer[idx]+self.left_buffer[idx]

    def excite(self, velocity:float, pluck_position:float = 0.2):
        self.right_buffer = [0.0] * self.max_size
        self.left_buffer = [0.0] * self.max_size
        
        # Reset Utility States
        self.fractional_delay.reset()
        self.damping_filter.reset()
        self.stiffness.reset()

        pluck_pos = max(1, min(int(self.buffer_size * pluck_position), self.buffer_size - 1))
        
        # [NEW] Smoothed Pluck Top (Simulates finger width)
        width = max(2, self.config.pluck_width)
        
        for i in range(self.buffer_size):
            current_point = (self.ptr + i)%self.buffer_size
            
            # 1. Calculate Ideal Sharp Triangle
            if i <= pluck_pos:
                val = 0.5 * velocity * (i / pluck_pos)
            else:
                val = 0.5 * velocity * ((self.buffer_size - i) / (self.buffer_size - pluck_pos))
            
            # 2. Smooth the tip using a simple polynomial window
            # If we are within 'width' of the pluck position, round it off
            dist = abs(i - pluck_pos)
            if dist < width:
                # Quadratic smoothing: val * (1 - (dist/width)^2 * scaling)
                # This makes the sharp point a parabola
                correction = (dist / width) ** 2
                val = val * (1.0 - 0.2 * (1.0 - correction)) 

            self.right_buffer[current_point] = val
            self.left_buffer[current_point] = val

    # Alpha is used for filtering. We'll take alpha*prev sample and average it with (1-a)*current sample
    # Alpha 0.05-0.1 is good for metal strings
    # Alpha 0.2-0.3 is good for Nylon strings
    # Alpha 0.5 is good for old/dead strings
    # Alpha 0.8 is good for palm muted strumming
    def process(self, num_samples :int,selector:str = 'acoustic'):

        ptr = self.ptr
        wd_right = self.right_buffer
        wd_left = self.left_buffer
        buff_size = self.buffer_size

        use_bridge = self.config.use_bridge_output

        chunk_size = 64
        output = np.zeros(num_samples)
        pickup_offsets=[]

        if not use_bridge:
            ratios=self.pickup_locations.get("all",[0.2])
            for r in ratios :
                offset = int(buff_size *r)
                pickup_offsets.append(offset)
        num_pickups = max(1,len(pickup_offsets))

        processed = 0
        while processed < num_samples:
            current_chunk = min(chunk_size, num_samples - processed)
            indices = (np.arange(current_chunk) + self.ptr) % buff_size
            val_bridge = np.array([wd_right[i] for i in indices])
            val_nut = np.array([wd_left[i] for i in indices])

            filtered_bridge = self.damping_filter.process_vector(val_bridge)
            stiff_bridge = self.stiffness.process_vector(filtered_bridge)

            inv_nut = -1 * val_nut
            nut_reflection = self.fractional_delay.process_vector(inv_nut, self.frac_c)

            left_write = -stiff_bridge * self.current_damping
            right_write = nut_reflection

            for k in range(current_chunk):
                idx = indices[k]
                wd_left[idx] = left_write[k]
                wd_right[idx] = right_write[k]

                if use_bridge:
                    output[processed + k] = filtered_bridge[k]
                else:
                    s = 0.0
                    for off in pickup_offsets:
                        pidx = (idx+off)%buff_size
                        s += wd_right[pidx] + wd_left[pidx]
                    output[processed + k] = s/num_pickups
            self.ptr = (self.ptr + current_chunk) % buff_size
            processed += current_chunk
            
        return output

    def get_effective_frequency(self) -> float: 
        """
        calculates the actual frequency being generated based on waveguide delays.
        """
        # We reverse the fractional delay formula: alpha = (1-c)/(1+c)
        frac_delay = (1.0 - self.frac_c) / (1.0+self.frac_c)
        stiffness_delay = self.stiffness.get_group_delay()

        total_period = (2.0 * self.buffer_size) + frac_delay + stiffness_delay +1.0

        return self.sample_rate / total_period