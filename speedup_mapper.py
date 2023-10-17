class SpeedupMapper:
    def __init__(self, scaling_gradient=.20, min_input_duration=10, fading_duration=1.5, min_time_between_fading=2, min_speedup_factor=2, max_speedup_factor=20):
        assert (min_time_between_fading + fading_duration*2) <= (min_input_duration / min_speedup_factor)

        self._min_input_duration = min_input_duration
        self._fading_duration = fading_duration
        self._min_time_between_fading = min_time_between_fading
        self._min_speedup_factor = min_speedup_factor
        self._max_speedup_factor = max_speedup_factor

        self._check_min_gradient(scaling_gradient)
        self._scaling_gradient = scaling_gradient
        self._scaling_y_intercept = min_speedup_factor - scaling_gradient*min_input_duration
    
    def _check_min_gradient(self, scaling_gradient):
        duration_reference = self.min_input_duration + 5
        speedup_factor_reference = duration_reference / (self._min_time_between_fading + self._fading_duration*2)

        min_gradient = (speedup_factor_reference - self._min_speedup_factor) / (duration_reference - self._min_input_duration)
        assert min_gradient >= scaling_gradient

    @property
    def min_input_duration(self):
        return self._min_input_duration

    @property
    def fading_duration(self):
        return self._fading_duration

    @property
    def min_time_between_fading(self):
        return self._min_time_between_fading
    
    def get_speedup_factor_for_input_duration(self, input_duration):
        assert self._min_input_duration <= input_duration

        calculated_speedup_factor = (self._scaling_gradient * input_duration) + self._scaling_y_intercept

        if calculated_speedup_factor > self._max_speedup_factor:
            #print("\n\n\n",self._max_speedup_factor)
            return self._max_speedup_factor
        else:
            #print("\n\n\n", calculated_speedup_factor)
            return calculated_speedup_factor
            
    

if __name__ == "__main__":
    print(SpeedupMapper().get_speedup_factor_for_input_duration(30))
    print(SpeedupMapper().get_speedup_factor_for_input_duration(60))
    print(SpeedupMapper().get_speedup_factor_for_input_duration(12))
    print(SpeedupMapper().get_speedup_factor_for_input_duration(120))
