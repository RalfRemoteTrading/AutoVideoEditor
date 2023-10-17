import os
from os import path
import glob
import wave
import random



def get_song_length(path_):
    wav_full_path = path.join(path_, os.listdir(path_)[0])
    try:
        with wave.open(wav_full_path, 'rb') as wav:
            p = wav.getparams()
            length = p.nframes / p.framerate
            return length
    except Exception as ex:
        print(wav_full_path)
        raise ex


def get_songdirs_for_required_length(required_length, search_dir, randomOrder):    
    total_list_of_song_dirs = os.listdir(search_dir)
    if randomOrder:
        random.shuffle(total_list_of_song_dirs)
    collected_songdirs = list()
    collected_length = 0
    for song_dir in total_list_of_song_dirs:
        song_path = path.join(search_dir, song_dir)
        current_songs_length = get_song_length(song_path)
        collected_length += current_songs_length 
        collected_songdirs.append(song_dir)        
        
        if collected_length >= required_length:
            break

    if collected_length <= required_length:
        raise IOError("Not enough songs in the specified directory. Could only collect {:.2f}s of the {:.2f}s required with {} songs being available.".format(collected_length, required_length, len(collected_songdirs)))

    return collected_songdirs
        
def get_stem_names_for_song(song_path):
    def check_name_for(tag):
        found_name = None
        for name in os.listdir(song_path):
            if tag in name:
                found_name = name
                break
        if found_name == None:
            raise IOError("Could not find a stem '{}' in song '{}'".format(tag, song_path))
        return found_name
        
    instruments_name = check_name_for("INSTRUMENTS")
    drums_name = check_name_for("DRUMS")
    bass_name = check_name_for("BASS")
    melody_name = check_name_for("MELODY")

    return instruments_name, drums_name, bass_name, melody_name

def write_source_to_output_wav(source_wav, output_wav):
    p = source_wav.getparams()
    try:
        output_wav.setparams(p)
    except:
        assert source_wav.getparams().nchannels == output_wav.getparams().nchannels
        assert source_wav.getparams().sampwidth == output_wav.getparams().sampwidth
        assert source_wav.getparams().framerate == output_wav.getparams().framerate
    output_wav.writeframesraw(source_wav.readframes(source_wav.getparams().nframes))

def chain_songs_of_length(required_length, search_dir, tmp_output_dir, randomOrder):
    song_dirs_for_video = get_songdirs_for_required_length(required_length, search_dir, randomOrder)
    
    output_instruments_wav  = wave.open(path.join(tmp_output_dir, "output_instruments.wav"), 'wb')
    output_drums_wav  = wave.open(path.join(tmp_output_dir, "output_drums.wav"), 'wb')
    output_bass_wav = wave.open(path.join(tmp_output_dir, "output_bass.wav"), 'wb')
    output_melody_wav = wave.open(path.join(tmp_output_dir, "output_melody.wav"), 'wb')

    for song_dir in song_dirs_for_video:
        instruments_name, drums_name, bass_name, melody_name = get_stem_names_for_song(path.join(search_dir, song_dir))
        with wave.open(path.join(search_dir, song_dir, instruments_name), 'rb') as source_instruments_wav:
            write_source_to_output_wav(source_instruments_wav, output_instruments_wav)
        with wave.open(path.join(search_dir, song_dir, drums_name), 'rb') as source_drums_wav:
            write_source_to_output_wav(source_drums_wav, output_drums_wav)
        with wave.open(path.join(search_dir, song_dir, bass_name), 'rb') as source_bass_wav:
            write_source_to_output_wav(source_bass_wav, output_bass_wav)
        with wave.open(path.join(search_dir, song_dir, melody_name), 'rb') as source_melody_wav:
            write_source_to_output_wav(source_melody_wav, output_melody_wav)    

    output_instruments_wav.close()
    output_drums_wav.close()
    output_bass_wav.close()
    output_melody_wav.close()


def clear_tmp_output_dir(tmp_output_dir):
    files = glob.glob(path.join(tmp_output_dir, '*'))
    for f in files:
        os.remove(f)

def generate_new_chained_stems(required_duration, search_dir, tmp_output_dir, randomOrder):
    if not path.exists(tmp_output_dir):
        os.makedirs(tmp_output_dir)
    clear_tmp_output_dir(tmp_output_dir)
    chain_songs_of_length(required_duration, search_dir, tmp_output_dir, randomOrder)

if __name__ == "__main__":
    search_dir = "editing_assets/audio/stems/Sunset_House"
    tmp_output_dir = "tmp"
    required_duration = 410
    generate_new_chained_stems(required_duration, search_dir, tmp_output_dir, True)