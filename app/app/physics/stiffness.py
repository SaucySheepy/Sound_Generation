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
