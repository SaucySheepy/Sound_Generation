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
    def __init__(self, sample_rate = 44100, frequency:float = 440.0, stiffness:float = -0.7, config :InstrumentConfig = InstrumentConfig()):
        self.sample_rate = sample_rate
        self.stiffness = stiffness
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
        self.damping_filter = LowPassFilter(alpha=0.4)
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
        pluck_pos = max(1, min(int(self.buffer_size * pluck_position), self.buffer_size - 1))
        for i in range(self.buffer_size):
            current_point = (self.ptr + i)%self.buffer_size
            if i<= pluck_pos :
                self.right_buffer[current_point] +=0.5 * velocity * i/pluck_pos 
                self.left_buffer[current_point] +=0.5 * velocity * i/pluck_pos 
            else:
                self.right_buffer[current_point] +=0.5* velocity * (self.buffer_size-i)/(self.buffer_size-pluck_pos)
                self.left_buffer[current_point] +=0.5* velocity * (self.buffer_size-i)/(self.buffer_size-pluck_pos)

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
        selector_key = "all"
        pickup_offsets=[]

        if not use_bridge:
            ratios=self.pickup_locations.get(selector_key,[0.2])
            for r in ratios :
                offset = int(buff_size *r)
                pickup_offsets.append(offset)
            num_pickups = len(pickup_offsets)

        output = [0.0]*num_samples

        for i in range(num_samples):
            val_bridge = wd_right[ptr]
            val_nut = wd_left[ptr]

            filtered_bridge = self.damping_filter.process_sample(val_bridge)
            stiff_bridge = self.stiffness.process_sample(filtered_bridge)
            #prev_output = filtered_bridge

            inv_nut = -1*val_nut
            nut_reflection = self.fractional_delay.process_sample(inv_nut, self.frac_c)
            #ap_x_prev =inv_nut
            #ap_y_prev = nut_reflection

            wd_left[ptr] = -stiff_bridge * self.current_damping
            wd_right[ptr] = nut_reflection

            if use_bridge:
                output[i] = filtered_bridge
            else:
                total_sig = 0.0
                for offset in pickup_offsets:
                    idx = (ptr+offset)%buff_size
                    total_sig += wd_right[idx] + wd_left[idx]
                output[i] = total_sig/num_pickups

            ptr = (ptr+1)%buff_size
        
        self.ptr = ptr
        
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