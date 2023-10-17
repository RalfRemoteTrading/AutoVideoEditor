import math 
import wave, audioop
from os import path

sound_effect_path = "C:/Users/ralfh/Programming/editing_assets/audio/effects/ES_Button Push 2 - SFX Producer.wav"

class EffectHelper:
    def __init__(self, use_sound_effect, is_scale_up, frames_available) -> None:
        self._use_sound_effect = use_sound_effect
        self._is_scale_up = is_scale_up
        self._frames_available = frames_available

        self._wav = wave.open(sound_effect_path, 'rb')
        self._nframes_sound_effect = self._wav.getparams().nframes

        assert self._frames_available > self._nframes_sound_effect

        if self._is_scale_up:
            self._start_idx = 0
            self._end_idx = self._nframes_sound_effect
        else:
            self._start_idx = self._frames_available - self._nframes_sound_effect
            self._end_idx = self._frames_available

    
    def __del__(self):
        self._wav.close()

    
    def maybe_add_sound_effect(self, wav_to_add_to, idx):

        # check if there should even be sound effects, if not just return the input
        if not self._use_sound_effect:
            return wav_to_add_to

        if idx >= self._start_idx and idx < self._end_idx:
            effect_frame = audioop.mul(self._wav.readframes(1), self._wav.getparams().sampwidth, 2)
            merged = audioop.add(wav_to_add_to, effect_frame, self._wav.getparams().sampwidth)
            return merged
        else:
            return wav_to_add_to


            
        
