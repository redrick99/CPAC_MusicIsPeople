print('Importing magenta modules...')
from magenta.models.music_vae import configs
from magenta.models.music_vae import TrainedModel
from note_seq.sequences_lib import concatenate_sequences
import os
import logging
import note_seq as mm
import numpy as np
import tensorflow._api.v2.compat.v1 as tf
import pretty_midi
from neural_network import chords_progression as cp

tf.disable_v2_behavior()
# Removes Tensorflow logs and warnings
tf.keras.utils.disable_interactive_logging()
tf.get_logger().setLevel(logging.ERROR)
print('Done!')

BATCH_SIZE = 4
Z_SIZE = 512
TOTAL_STEPS = 512
BAR_SECONDS = 2.0
CHORD_DEPTH = 49

SAMPLE_RATE = 44100
SF2_PATH = 'neural_network/models/SGM-v2.01-Sal-Guit-Bass-V1.3.sf2'
CONFIG = None
MODEL =None
MODEL_PATH = 'neural_network/models/MusicVAE/model_chords_fb64.ckpt'
CONFIG_INTERP = None
MODEL_INTERP = None
MODEL_INTERP_PATH = 'neural_network/models/MusicVAE/model_fb256.ckpt'
PREC_SONG = None
KEY = None


# Play sequence using SoundFont.
def play(note_sequences):
    if not isinstance(note_sequences, list):
        note_sequences = [note_sequences]
    for ns in note_sequences:
        mm.play_sequence(ns, synth=mm.fluidsynth,
                         sf2_path=SF2_PATH, sample_rate=44100.0)


# Spherical linear interpolation.
def slerp(p0, p1, t):
    """Spherical linear interpolation."""
    omega = np.arccos(np.dot(np.squeeze(p0 / np.linalg.norm(p0)),
                      np.squeeze(p1 / np.linalg.norm(p1))))
    so = np.sin(omega)
    return np.sin((1.0 - t) * omega) / so * p0 + np.sin(t * omega) / so * p1


# Chord encoding tensor.
def chord_encoding(chord):
    index = mm.TriadChordOneHotEncoding().encode_event(chord)
    c = np.zeros([TOTAL_STEPS, CHORD_DEPTH])
    c[0, 0] = 1.0
    c[1:, index] = 1.0
    return c


# Trim sequences to exactly one bar.
def trim_sequences(seqs, num_seconds=BAR_SECONDS):
    for i in range(len(seqs)):
        seqs[i] = mm.extract_subsequence(seqs[i], 0.0, num_seconds)
        seqs[i].total_time = num_seconds


# Consolidate instrument numbers by MIDI program.
def fix_instruments_for_concatenation(note_sequences):
    instruments = {}
    for i in range(len(note_sequences)):
        for note in note_sequences[i].notes:
            if not note.is_drum:
                if note.program not in instruments:
                    if len(instruments) >= 8:
                        instruments[note.program] = len(instruments) + 2
                    else:
                        instruments[note.program] = len(instruments) + 1
                note.instrument = instruments[note.program]
            else:
                note.instrument = 9


def to_midi(note_sequence):
    return mm.sequence_proto_to_pretty_midi(note_sequence)


def generate_sequence(va_value: str):
    global KEY
    global MODEL
    
    chords, KEY = cp.choose_chords(va_value, KEY)
    print(chords)

    num_bars = 24  # @param {type:"slider", min:4, max:64, step:4}
    temperature = 0.1  # @param {type:"slider", min:0.01, max:1.5, step:0.01}

    z1 = np.random.normal(size=[Z_SIZE])
    z2 = np.random.normal(size=[Z_SIZE])
    z = np.array([slerp(z1, z2, t)
                  for t in np.linspace(0, 1, num_bars)])

    seqs = [
        MODEL.decode(length=TOTAL_STEPS, z=z[i:i+1, :], temperature=temperature,
                     c_input=chord_encoding(chords[i % 4]))[0]
        for i in range(num_bars)
    ]
    # print(time.time()-start_time)
    trim_sequences(seqs)
    fix_instruments_for_concatenation(seqs)
    prog_interp_ns = concatenate_sequences(seqs)

    return prog_interp_ns, KEY


def initialize_model(main_path: str):
    global CONFIG
    global MODEL
    global MODEL_PATH
    global CONFIG_INTERP
    global MODEL_INTERP
    global MODEL_INTERP_PATH
    global SF2_PATH

    SF2_PATH = os.path.join(main_path, SF2_PATH)
    MODEL_PATH = os.path.join(main_path, MODEL_PATH)
    MODEL_INTERP_PATH = os.path.join(main_path, MODEL_INTERP_PATH)

    # INITIALIZE MODEL FOR CREATE SONG
    CONFIG = configs.CONFIG_MAP['hier-multiperf_vel_1bar_med_chords']
    MODEL = TrainedModel(
        CONFIG, batch_size=BATCH_SIZE,
        checkpoint_dir_or_path=MODEL_PATH)

    #INITIALIZE MODEL FOR INTERPOLATE SONGS
    CONFIG_INTERP = configs.CONFIG_MAP['hier-multiperf_vel_1bar_med']
    MODEL_INTERP = TrainedModel(
        CONFIG_INTERP, batch_size=BATCH_SIZE,
        checkpoint_dir_or_path=MODEL_INTERP_PATH)
    MODEL_INTERP._config.data_converter._max_tensors_per_input = None


def interpolate_songs(va_value:str):
    global MODEL_INTERP
    global MODEL
    global PREC_SONG
    global KEY

    seqs = []
    new_song,_ = generate_sequence(va_value)
    new_song = to_midi(new_song)
    new_song = mm.midi_to_sequence_proto(PREC_SONG)
    seqs.append(mm.midi_to_sequence_proto(PREC_SONG))
    seqs.append(new_song)
    
    for seq in seqs:
        uploaded_seqs = []
        _, tensors, _, _ = MODEL_INTERP._config.data_converter.to_tensors(seq)
        uploaded_seqs.extend(MODEL_INTERP._config.data_converter.from_tensors(tensors))

    trim_sequences(uploaded_seqs)
    
    index_1 = 0 
    index_2 = 1 

    num_bars = 32 
    temperature = 0.2 

    z1, _, _ = MODEL_INTERP.encode([uploaded_seqs[index_1]])
    z2, _, _ = MODEL_INTERP.encode([uploaded_seqs[index_2]])
    z = np.array([slerp(np.squeeze(z1), np.squeeze(z2), t)
                for t in np.linspace(0, 1, num_bars)])

    seqs = MODEL_INTERP.decode(length=TOTAL_STEPS, z=z, temperature=temperature)

    trim_sequences(seqs)
    fix_instruments_for_concatenation(seqs)
    recon_interp_ns = concatenate_sequences(seqs)
    PREC_SONG = to_midi(recon_interp_ns)
    

def create_song(va_value: str, liked: bool):
    global MODEL
    global PREC_SONG
    global KEY

    if not liked or PREC_SONG is None:
    # CHOOSE CHORDS AND RUN
        [prog_interp_ns, KEY] = generate_sequence(va_value)
        PREC_SONG = to_midi(prog_interp_ns)
        return PREC_SONG
    
    interpolate_songs(va_value)
    return PREC_SONG


def create_wav(midi:pretty_midi.PrettyMIDI):
    global SF2_PATH
    wav = midi.fluidsynth(fs=44100.0, sf2_path=SF2_PATH)
    return wav.astype(dtype=np.float32)