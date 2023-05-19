print('Importing magenta modules...')
from magenta.models.music_vae import configs
from magenta.models.music_vae import TrainedModel
from note_seq.sequences_lib import concatenate_sequences
import os
import copy
import logging
import note_seq as mm
import numpy as np
import tensorflow._api.v2.compat.v1 as tf
import pretty_midi
from note_seq.protobuf import music_pb2
# from neural_network import chords_progression as cp
from neural_network.chords_progression import ChordsMarkovChain

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
CHORDS_PER_BAR = 4

SAMPLE_RATE = 44100
SF2_PATH = 'neural_network/models/SGM-v2.01-Sal-Guit-Bass-V1.3.sf2'
CONFIG = None
MODEL = None
MODEL_PATH = 'neural_network/models/MusicVAE/model_chords_fb64.ckpt'
CONFIG_INTERP = None
MODEL_INTERP = None
MODEL_INTERP_PATH = 'neural_network/models/MusicVAE/model_fb256.ckpt'

PREV_SONG = None

chords_markov_chain = ChordsMarkovChain()


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


def to_midi(note_sequence, bpm):
    note_sequence = change_tempo(note_sequence, bpm)
    print(note_sequence.tempos, flush=True)
    return mm.sequence_proto_to_pretty_midi(note_sequence)


def change_tempo(note_sequence, new_tempo):
    new_sequence = copy.deepcopy(note_sequence)
    ratio = note_sequence.tempos[0].qpm / float(new_tempo)
    for note in new_sequence.notes:
        note.start_time = note.start_time * ratio
        note.end_time = note.end_time * ratio
    new_sequence.tempos[0].qpm = new_tempo
    return new_sequence


def get_bpm_and_num_bars(mood: str, max_duration: float):
    bpm = 120
    if mood == 'exciting' or mood == 'anxious':
        bpm = 120
    if mood == 'happy' or mood == 'angry':
        bpm = 90
    if mood == 'serene' or mood == 'sad':
        bpm = 60
    if mood == 'relaxing' or mood == 'bored':
        bpm = 30
    num_bars = int(max_duration * bpm / CHORDS_PER_BAR)
    return bpm, num_bars


def generate_sequence(va_mood: str, liked: bool, num_bars: int):
    global MODEL
    
    chords = chords_markov_chain.get_next_chord_progression(va_mood, CHORDS_PER_BAR, not liked)
    print(chords)

    # num_bars = 24
    temperature = 0.1

    z1 = np.random.normal(size=[Z_SIZE])
    z2 = np.random.normal(size=[Z_SIZE])
    z = np.array([slerp(z1, z2, t)
                  for t in np.linspace(0, 1, num_bars)])

    seqs = [
        MODEL.decode(length=TOTAL_STEPS, z=z[i:i+1, :], temperature=temperature,
                     c_input=chord_encoding(chords[i % 4]))[0]
        for i in range(num_bars)
    ]
    trim_sequences(seqs)
    fix_instruments_for_concatenation(seqs)
    prog_interp_ns = concatenate_sequences(seqs)

    return prog_interp_ns


def interpolate_songs(va_value: str, liked: bool, num_bars: int, bpm):
    global MODEL_INTERP
    global MODEL
    global PREV_SONG

    seqs = []
    new_song = generate_sequence(va_value, not liked, num_bars)
    new_song = to_midi(new_song, bpm)
    new_song = mm.midi_to_sequence_proto(new_song)
    seqs.append(mm.midi_to_sequence_proto(PREV_SONG))
    seqs.append(new_song)

    uploaded_seqs = []
    for seq in seqs:
        _, tensors, _, _ = MODEL_INTERP._config.data_converter.to_tensors(seq)
        uploaded_seqs.extend(MODEL_INTERP._config.data_converter.from_tensors(tensors))

    trim_sequences(uploaded_seqs)
    
    index_1 = 0 
    index_2 = 1 

    #num_bars = 32
    temperature = 0.2 

    z1, _, _ = MODEL_INTERP.encode([uploaded_seqs[index_1]])
    z2, _, _ = MODEL_INTERP.encode([uploaded_seqs[index_2]])
    z = np.array([slerp(np.squeeze(z1), np.squeeze(z2), t)
                for t in np.linspace(0, 1, num_bars)])

    seqs = MODEL_INTERP.decode(length=TOTAL_STEPS, z=z, temperature=temperature)

    trim_sequences(seqs)
    fix_instruments_for_concatenation(seqs)
    recon_interp_ns = concatenate_sequences(seqs)
    return recon_interp_ns


def create_song(va_mood: str, liked: bool):
    global MODEL
    global PREV_SONG

    bpm, num_bars = get_bpm_and_num_bars(va_mood, 1.0)

    # CHOOSE CHORDS AND RUN
    if not liked or PREV_SONG is None:
        prog_interp_ns = generate_sequence(va_mood, liked, num_bars)
    else:
        prog_interp_ns = interpolate_songs(va_mood, liked, num_bars, bpm)

    PREV_SONG = to_midi(prog_interp_ns, bpm)
    return PREV_SONG


def create_wav(midi: pretty_midi.PrettyMIDI):
    global SF2_PATH
    wav = midi.fluidsynth(fs=44100.0, sf2_path=SF2_PATH)
    return wav.astype(dtype=np.float32)


