import numpy as np
from scipy.signal import lfilter

class FractionalDelay:
    #Adding logic for all-pass filter
    #Caters to fractional differences in frequency conversion to integers
    def __init__(self):
        self.x_prev =0.0
        self.y_prev =0.0

    def process_sample(self, input_val:float, c:float) -> float:
        """
        y[n] = C*x[n] + x[n-1] - C*y[n-1]
        """
        output = (c*input_val) + self.x_prev - (c*self.y_prev)
        self.x_prev = input_val
        self.y_prev = output
        return output

    def process_vector(self, signal:np.ndarray, c:float)->np.ndarray:
        b = [c,1.0]
        a = [1.0,c]
        zi = np.array([self.x_prev - c*self.y_prev])

        output, zf = lfilter(b,a,signal,zi=zi)

        self.x_prev = signal[-1]
        self.y_prev = output[-1]
        return output

    def reset(self):
        self.x_prev = 0.0
        self.y_prev = 0.0

class LowPassFilter:
    """
    A simple one-pole low pass filter
    """
    def __init__(self, alpha:float=0.5):
        self.alpha = alpha
        self.prev_output= 0.0

    def set_alpha(self, alpha:float = 0.5):
        self.alpha = alpha 

    def process_sample(self, input_val:float) -> float:
        """
        y[n] = (1-alpha)*x[n] + alpha*y[n-1]
        """
        output = ((1.0-self.alpha) * input_val) + (self.alpha * self.prev_output)
        self.prev_output = output
        return output

    def process_vector(self, signal:np.ndarray) -> np.ndarray:
        b = [1.0 - self.alpha]
        a = [1.0 - self.alpha]

        zi = np.array(self.prev_output *self.alpha)

        output, zf = lfilter(b,a, signal, zi=zi)

        self.prev_output = output[-1]
        return output

    def reset(self):
        self.prev_output = 0.0
        
class StiffnessDispersion:
    def __init__(self, stiffness:float = -0.7, stages:int = 12):
        self.a = stiffness
        self.stages = stages
        self.x_prev = [0.0]*stages
        self.y_prev = [0.0]*stages
        self.zi_vec = [np.zeros(1) for _ in range(stages)]
    
    def process_vector(self, signal: np.ndarray) -> np.ndarray:
        current = signal
        b = np.array([self.a, 1.0])
        a_poly = np.array([1.0, self.a])

        for i in range(self.stages):
            output, self.zi_vec[i] = lfilter(b,a_poly,current, zi =self.zi_vec[i])
            current = output

        return current

    def reset(self):
        self.x_prev = [0.0]*self.stages
        self.y_prev = [0.0]*self.stages
        self.zi_vec = [np.zeros(1) for _ in range(self.stages)]
        
    def get_group_delay(self) -> float:
        """Calculates the total sample delay introduced by all stages."""
        denom = (1.0+self.a)
        if abs(denom) <1e-6:denom = 1e-6
        return self.stages*(1.0-self.a)/denom
    
    def update_stiffness(self, target_stiffness:float, max_delay_budget:float):
        s = max(-0.99, min(0.99, target_stiffness))
        delay = self.stages * (1.0-s) / (1.0+s)
        if delay> max_delay_budget:
            D = max(0.1,max_delay_budget)
            s = (self.stages-D) / (self.stages+D)
            delay = D
        self.a=s
        return delay

    def process_sample(self, input_val:float) -> float:
        current_input = input_val
        for i in range(self.stages):
            output = (self.a * current_input) + self.x_prev[i] - (self.a * self.y_prev[i])
            self.x_prev[i] = current_input
            self.y_prev[i] = output
            current_input = output
        return current_input

    def reset(self):
        self.x_prev = [0.0]*self.stages
        self.y_prev = [0.0]*self.stages
