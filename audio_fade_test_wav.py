import wave, audioop
from tqdm import tqdm 


fadein_duration = 5
pre_run_seconds = 11

with wave.open('output.wav', 'wb') as audio:

    with wave.open('ES_empress - shamgang\\ES_empress STEMS INSTRUMENTS.wav', 'rb') as wav_instruments:
        with wave.open('ES_empress - shamgang\\ES_empress STEMS DRUMS.wav', 'rb') as wav_drums:
            with wave.open('ES_empress - shamgang\\ES_empress STEMS BASS.wav', 'rb') as wav_bass:
                with wave.open('ES_empress - shamgang\\ES_empress STEMS MELODY.wav', 'rb') as wav_melody:
                    p = wav_instruments.getparams()
                    audio.setparams(p)

                    n_fading_frames = fadein_duration * p.framerate
                    
                    pre_run_frames = pre_run_seconds * p.framerate
                    audio.writeframesraw(wav_instruments.readframes(pre_run_frames))
                    wav_drums.readframes(pre_run_frames)
                    wav_bass.readframes(pre_run_frames)
                    wav_melody.readframes(pre_run_frames)

                
                    scaling_base = 1/n_fading_frames

                    
                    for i in tqdm(range(n_fading_frames), total=n_fading_frames):
                        frames_instrumental = wav_instruments.readframes(1)
                        frames_drums = wav_drums.readframes(1)
                        frames_bass = wav_bass.readframes(1)
                        frames_melody = wav_melody.readframes(1)

                        scaled_drums = audioop.mul(frames_drums, p.sampwidth, scaling_base*i)
                        scaled_bass = audioop.mul(frames_bass, p.sampwidth, scaling_base*i)
                        scaled_melody = audioop.mul(frames_melody, p.sampwidth, scaling_base*i)
                        
                        merged = audioop.add(frames_instrumental, scaled_drums, p.sampwidth)
                        merged = audioop.add(merged, scaled_bass, p.sampwidth)
                        merged = audioop.add(merged, scaled_melody, p.sampwidth)

                        audio.writeframesraw(merged)


                    frames_instrumental = wav_instruments.readframes(p.nframes-n_fading_frames-pre_run_frames)
                    frames_drums = wav_drums.readframes(p.nframes-n_fading_frames-pre_run_frames)
                    frames_bass = wav_bass.readframes(p.nframes-n_fading_frames-pre_run_frames)
                    frames_melody = wav_melody.readframes(p.nframes-n_fading_frames-pre_run_frames)
                    audio.writeframesraw(audioop.add(audioop.add(audioop.add(frames_instrumental, frames_drums, p.sampwidth), frames_bass, p.sampwidth), frames_melody, p.sampwidth))