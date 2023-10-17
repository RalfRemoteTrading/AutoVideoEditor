import math 
import wave, audioop
from os import path
from effect_helper import EffectHelper


class FadingProcessor:
    def __init__(self, tmp_stem_dir, fading_duration, use_melody_for_base_background, background_multiplicator=.7, use_sound_effects=True):
        self._fading_duration = fading_duration
        self._use_melody_for_base_background = use_melody_for_base_background
        self._background_multiplicator = background_multiplicator

        self._instruments_wav  = wave.open(path.join(tmp_stem_dir, "output_instruments.wav"), 'rb')
        self._wav_params = self._instruments_wav.getparams()
        self._drums_wav  = wave.open(path.join(tmp_stem_dir, "output_drums.wav"), 'rb')
        self._bass_wav = wave.open(path.join(tmp_stem_dir, "output_bass.wav"), 'rb')
        self._melody_wav = wave.open(path.join(tmp_stem_dir, "output_melody.wav"), 'rb')

        self._mixed_output_wav = wave.open(path.join(tmp_stem_dir, "output_faded_mixed.wav"), 'wb')
        self._mixed_output_wav.setparams(self._wav_params)

        self._use_sound_effects = use_sound_effects
        
        self._n_fading_frames =  int(round(self._fading_duration * self._wav_params.framerate, 0))
        self._scaling_base = 1 / self._n_fading_frames
    
    def add_instruments_section(self, duration):
        nframes_instruments = int(round(self._wav_params.framerate * duration, 0))
        
        frames_instruments = self._instruments_wav.readframes(nframes_instruments)
        frames_melody = self._melody_wav.readframes(nframes_instruments)
        if self._use_melody_for_base_background:
            ready_to_write_frames = audioop.add(frames_instruments, frames_melody, self._wav_params.sampwidth)
        else:
            ready_to_write_frames = frames_instruments
        
        # this will make the background music while speaking be more silent
        ready_to_write_frames = audioop.mul(ready_to_write_frames, self._wav_params.sampwidth, self._background_multiplicator)
        self._mixed_output_wav.writeframesraw(ready_to_write_frames)

        # throw away the frames from the other stems and move the cursor
        self._drums_wav.readframes(nframes_instruments)
        self._bass_wav.readframes(nframes_instruments)


    def add_faded_fullmix_section(self, duration):
        self.fade_up()

        full_mix_duration = duration - 2*self._fading_duration
        full_mix_frames = int(round(full_mix_duration * self._wav_params.framerate, 0))

        frames_instruments = self._instruments_wav.readframes(full_mix_frames)
        frames_drums = self._drums_wav.readframes(full_mix_frames)
        frames_bass = self._bass_wav.readframes(full_mix_frames)
        frames_melody = self._melody_wav.readframes(full_mix_frames)
        self._mixed_output_wav.writeframesraw(audioop.add(audioop.add(audioop.add(frames_instruments, frames_drums, self._wav_params.sampwidth),
                                                                       frames_bass, self._wav_params.sampwidth),
                                                                       frames_melody, self._wav_params.sampwidth))
        self.fade_down()

    def fade_down(self):
        def scale_stems_down_fn(i):
            return 1 - self._scaling_base*i
        self.apply_fade(scale_stems_down_fn, False)
    
    def fade_up(self):
        def scale_stems_up_fn(i):
            return self._scaling_base*i
        self.apply_fade(scale_stems_up_fn, True)

    def apply_fade(self, scaling_fn, is_scale_up):
        effect_helper = EffectHelper(self._use_sound_effects, is_scale_up, self._n_fading_frames)
        for i in range(self._n_fading_frames):
            frames_instruments = self._instruments_wav.readframes(1)
            scaled_instruments = audioop.mul(frames_instruments, self._wav_params.sampwidth,  self._background_multiplicator + (1-self._background_multiplicator) * scaling_fn(i))

            frames_drums = self._drums_wav.readframes(1)
            frames_bass = self._bass_wav.readframes(1)
            frames_melody = self._melody_wav.readframes(1)

            scaled_drums = audioop.mul(frames_drums, self._wav_params.sampwidth,  scaling_fn(i))
            scaled_bass = audioop.mul(frames_bass, self._wav_params.sampwidth,  scaling_fn(i))
            if self._use_melody_for_base_background:
                scaled_melody = audioop.mul(frames_melody, self._wav_params.sampwidth,  self._background_multiplicator + (1-self._background_multiplicator) * scaling_fn(i))
            else:
                scaled_melody = audioop.mul(frames_melody, self._wav_params.sampwidth,  scaling_fn(i))
            
            merged = audioop.add(scaled_instruments, scaled_drums, self._wav_params.sampwidth)
            merged = audioop.add(merged, scaled_bass, self._wav_params.sampwidth)
            merged = audioop.add(merged, scaled_melody, self._wav_params.sampwidth)

            merged = effect_helper.maybe_add_sound_effect(merged, i)

            self._mixed_output_wav.writeframesraw(merged)



    def __del__(self):
        self._instruments_wav.close()
        self._drums_wav.close()
        self._bass_wav.close()
        self._melody_wav.close()
        self._mixed_output_wav.close()
