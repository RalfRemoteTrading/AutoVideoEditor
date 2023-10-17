#!/usr/bin/env python
#
# Based on a script by Donald Feury
# https://gitlab.com/dak425/scripts/-/blob/master/trim_silenceV2
# https://youtu.be/ak52RXKfDw8

import math
import sys
import subprocess
import os
import shutil
from tqdm import tqdm
from moviepy.editor import AudioFileClip, VideoFileClip, ImageClip, CompositeVideoClip, CompositeAudioClip, concatenate_videoclips, concatenate_audioclips, vfx
import moviepy.audio.fx.all as afx
from chain_stems_to_required_length import generate_new_chained_stems

from fading_processor import FadingProcessor
from speedup_mapper import SpeedupMapper


use_melody_for_base_background = True
silence_padding_s = 1

def find_silence(audio_clip, speedup_mapper, window_size=0.2, volume_threshold=0.02):
    # First, iterate over audio to find all silent windows.
    num_windows = math.floor(audio_clip.end/window_size)
    window_is_silent = []
    for i in tqdm(range(num_windows), total=num_windows, desc="Scanning for silent windows"):
        s = audio_clip.subclip(i * window_size, (i + 1) * window_size)
        v = s.max_volume()
        window_is_silent.append(v < volume_threshold)

    # Find speaking intervals.
    def add_intevall_if_long_engough():
        intervall_duration = silence_end-silence_start
        if intervall_duration > speedup_mapper.min_input_duration + 2*silence_padding_s:
            new_silence_interval = [silence_start+silence_padding_s, silence_end-silence_padding_s]
            silence_intervals.append(new_silence_interval)

    silence_start = 0
    silence_end = 0
    silence_intervals = []
    for i in range(1, len(window_is_silent)):
        e1 = window_is_silent[i - 1]
        e2 = window_is_silent[i]

        # speaking -> silence
        if not e1 and e2:
            silence_start = i * window_size
        # silvence -> speaking
        if e1 and not e2:
            silence_end = i * window_size
            add_intevall_if_long_engough()

    if silence_start != silence_intervals[-1][0] and silence_end != silence_intervals[-1][1]:
        silence_end = i * window_size
        add_intevall_if_long_engough()
        
    return silence_intervals

def get_speaking_intervalls(silent_intervals, video_len):
    speaking_intervals = []

    if silent_intervals[0][0] != 0:
        speaking_intervals.append([0, silent_intervals[0][0]])

    for i in range(len(silent_intervals)-1):
        speaking_start = silent_intervals[i][1]
        speaking_end =  silent_intervals[i+1][0]
        speaking_intervals.append([speaking_start, speaking_end])
    
    if silent_intervals[-1][1] != video_len:
        speaking_intervals.append([silent_intervals[-1][1], video_len])
    
    return speaking_intervals

def sync_music(speedup_mapper, speedup_leading, leading_list, trailing_list):
    fading_processor = FadingProcessor("tmp", speedup_mapper.fading_duration, use_melody_for_base_background, .5)

    #for i in tqdm(range(len(leading_list)), total=len(leading_list), desc="Adding music"):
    for i in range(len(leading_list)):
        start_leading, end_leading = leading_list[i]
        if i < len(trailing_list):
            start_trailing, end_trailing = trailing_list[i]
        

        if speedup_leading:
            fading_processor.add_faded_fullmix_section((end_leading - start_leading)/speedup_mapper.get_speedup_factor_for_input_duration(end_leading - start_leading))
            if i < len(trailing_list):
                fading_processor.add_instruments_section(end_trailing - start_trailing)
            
        else:
            fading_processor.add_instruments_section(end_leading - start_leading)
            if i < len(trailing_list):
                fading_processor.add_faded_fullmix_section((end_trailing - start_trailing)/speedup_mapper.get_speedup_factor_for_input_duration(end_trailing - start_trailing))

    if len(trailing_list) > len(leading_list):
        start_trailing, end_trailing = trailing_list[-1]
        if speedup_leading:
            fading_processor.add_instruments_section(end_trailing - start_trailing)
        else:
            fading_processor.add_faded_fullmix_section((end_trailing - start_trailing)/speedup_mapper.get_speedup_factor_for_input_duration(end_trailing - start_trailing))
        


def speedup_and_merge_intervals(video_source, leading_list, trailing_list,  speedup_leading, speedup_mapper, target_volume):
    def add_fast_forward_overlay(clip):
        ff = ImageClip("editing_assets/images/ff new clean.png").set_start(0).set_duration(clip.duration).set_pos((0.75, 0.70), relative=True)
        final = CompositeVideoClip([clip, ff])
        return final

    def add_from_trailing_list():
        trailing_clip = video_source.subclip(start_trailing, end_trailing)
        #print("Trailing ", trailing_clip.audio.max_volume())
        if not speedup_leading:
            trailing_clip = trailing_clip.fx(vfx.speedx, speedup_mapper.get_speedup_factor_for_input_duration(end_trailing-start_trailing))
            trailing_clip = trailing_clip.without_audio()
            trailing_clip = add_fast_forward_overlay(trailing_clip)  
        else:
            trailing_clip = trailing_clip.fx(afx.audio_normalize)
        clips_list.append(trailing_clip)


    clips_list = []
    for i in tqdm(range(len(leading_list)), total=len(leading_list), desc="Chaining video clips"):
        start_leading, end_leading = leading_list[i]
        if i < len(trailing_list):
            start_trailing, end_trailing = trailing_list[i]

        leading_clip = video_source.subclip(start_leading, end_leading)
        if speedup_leading:
            leading_clip = leading_clip.fx(vfx.speedx, speedup_mapper.get_speedup_factor_for_input_duration(end_trailing-end_trailing))            
            leading_clip = leading_clip.without_audio()
            leading_clip = add_fast_forward_overlay(leading_clip)
        else:
            if leading_clip.audio.max_volume() > 0:
                leading_clip = leading_clip.fx(afx.audio_normalize)
            
        clips_list.append(leading_clip)
        if i < len(trailing_list):
            add_from_trailing_list()

    # if the trailing list has and additional entry we can not forget using it
    if len(trailing_list) > len(leading_list):
        start_trailing, end_trailing = trailing_list[i]
        add_from_trailing_list()

    edited_video = concatenate_videoclips(clips_list, method="chain")
    return edited_video

def print_silent_speaking_stats(silent_intervals, speaking_intervals):
    sum_silent = 0
    for silent_interval in silent_intervals:
        sum_silent += silent_interval[1] - silent_interval[0]
    
    sum_speaking = 0
    for speaking_interval in speaking_intervals:
        sum_speaking += speaking_interval[1] - speaking_interval[0]
    
    print("Silent sections in recording: {} -- {:.2f} min".format(len(silent_intervals), sum_silent/60))
    print("Speaking sections in recording: {} -- {:.2f} min".format(len(speaking_intervals), sum_speaking/60))

def main(speedup_mapper, recording_file_name):
    target_voice_volume = 0.6
    recordings_dir = "C:\\Users\\ralfh\\Videos\\OBS_recordings"
    output_dir = "C:\\Users\\ralfh\\Videos\\rendered_videos"
    
    outout_file_name = recording_file_name[:recording_file_name.rfind(" ")+1] + "rendered.mp4"

    video_source = VideoFileClip(os.path.join(recordings_dir, recording_file_name))
    #video_source = video_source.subclip(0, video_source.duration/6)

    silent_intervals = find_silence(video_source.audio, speedup_mapper)
    speaking_intervals = get_speaking_intervalls(silent_intervals, video_source.duration)
    print_silent_speaking_stats(silent_intervals, speaking_intervals)
    #print("Silent intervals: " + str(silent_intervals))
    #print("Speaking intervals: " + str(speaking_intervals))

    if silent_intervals[0][0] == 0:
        speedup_leading = True
        leading_list = silent_intervals
        trailing_list = speaking_intervals
    else:
        speedup_leading = False
        leading_list = speaking_intervals
        trailing_list = silent_intervals

    mergered_intervals = speedup_and_merge_intervals(video_source, leading_list, trailing_list, speedup_leading, speedup_mapper, target_voice_volume)

    
    generate_new_chained_stems(mergered_intervals.duration+5, "editing_assets/audio/stems/lofi_laid_back", "tmp", randomOrder=True)
    sync_music(speedup_mapper, speedup_leading, leading_list, trailing_list)    
    music_track = AudioFileClip("tmp/output_faded_mixed.wav").fx(afx.audio_normalize).volumex(0.16) # 45 for lofi
    music_track.subclip(0, mergered_intervals.duration)

    overlayed = CompositeAudioClip([mergered_intervals.audio, music_track])
    mergered_intervals.audio = overlayed

    #intro_audio = AudioFileClip("editing_assets/audio/intro.wav").fx(afx.audio_normalize)
    #logo_clip = ImageClip("editing_assets/images/logo_full_page.png").resize((1920, 1080)).set_duration(intro_audio.duration).fx(vfx.fadeout, .25)
    #logo_clip.audio = intro_audio
    discalimer_spoken = AudioFileClip("editing_assets/audio/disclaimer_spoken.wav").fx(afx.audio_normalize)
    disclaimer_image = ImageClip("editing_assets/images/disclaimer.png").resize((1920, 1080)).set_duration(discalimer_spoken.duration+.5).fx(vfx.fadeout, .25)
    disclaimer_image.audio = discalimer_spoken
    mergered_intervals = concatenate_videoclips([#logo_clip,
                                                  disclaimer_image,
                                                    mergered_intervals.fx(vfx.fadein, .25)])

    print("Old duration {0:.2f} min".format(video_source.duration/60))
    print("New duration {0:.2f} min".format(mergered_intervals.duration/60))
    video_time_reduced_sec = video_source.duration - mergered_intervals.duration
    print("Shortened by {:.2f} min and reduced video length by {}%".format(video_time_reduced_sec/60, int(video_time_reduced_sec/video_source.duration*100)))

    mergered_intervals.write_videofile(os.path.join(output_dir, outout_file_name),
        fps=24,
        #preset='ultrafast',
        preset='slow',
        codec='libx264',
        bitrate='8000k',
        temp_audiofile='tmp/temp-audio-{}.m4a'.format(outout_file_name),
        remove_temp=True,
        audio_codec="aac",
        threads=20,
    ) 

    video_source.close()
    music_track.close()
    discalimer_spoken.close()
    

if __name__ == '__main__':
    speedup_mapper = SpeedupMapper(scaling_gradient=.15, max_speedup_factor=12)
    main(speedup_mapper, "2023.10.17 14_59 backtest 09.03 2022 recording.mp4")
