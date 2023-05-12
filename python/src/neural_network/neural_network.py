import numpy as np
import os
import time
import tensorflow._api.v2.compat.v1 as tf
import chords_progression as cp

print('Importing magenta modules...')
#import magenta.music as mm
import note_seq as mm
from magenta.music.sequences_lib import concatenate_sequences
from magenta.models.music_vae.trained_model import TrainedModel
from magenta.models.music_vae import configs

tf.disable_v2_behavior()
print('Done!')

BATCH_SIZE = 4
Z_SIZE = 512
TOTAL_STEPS = 512
BAR_SECONDS = 2.0
CHORD_DEPTH = 49

SAMPLE_RATE = 44100
SF2_PATH = './models/SGM-v2.01-Sal-Guit-Bass-V1.3.sf2'


# Play sequence using SoundFont.
def play(note_sequences):
    if not isinstance(note_sequences, list):
        note_sequences = [note_sequences]
    for ns in note_sequences:
        mm.play_sequence(ns, synth=mm.fluidsynth, sf2_path=SF2_PATH)


# Spherical linear interpolation.
def slerp(p0, p1, t):
    """Spherical linear interpolation."""
    omega = np.arccos(np.dot(np.squeeze(p0 / np.linalg.norm(p0)), np.squeeze(p1 / np.linalg.norm(p1))))
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


def generate_sequence(model):
    chords = cp.choose_chords()
    print(chords)

    num_bars = 48  # @param {type:"slider", min:4, max:64, step:4}
    temperature = 0.1  # @param {type:"slider", min:0.01, max:1.5, step:0.01}

    z1 = np.random.normal(size=[Z_SIZE])
    z2 = np.random.normal(size=[Z_SIZE])
    z = np.array([slerp(z1, z2, t)
                  for t in np.linspace(0, 1, num_bars)])

    seqs = [
        model.decode(length=TOTAL_STEPS, z=z[i:i+1, :], temperature=temperature,
                     c_input=chord_encoding(chords[i % 4]))[0]
        for i in range(num_bars)
    ]
    # print(time.time()-start_time)
    trim_sequences(seqs)
    fix_instruments_for_concatenation(seqs)
    prog_interp_ns = concatenate_sequences(seqs)

    return prog_interp_ns, chords


config = configs.CONFIG_MAP['hier-multiperf_vel_1bar_med_chords']
model = TrainedModel(
    config, batch_size=BATCH_SIZE,
    checkpoint_dir_or_path='./models/MusicVAE/model_chords_fb64.ckpt')

# %% CHOOSE CHORDS AND RUN
start_time = time.time()
[prog_interp_ns, chords] = generate_sequence(model)
print(time.time()-start_time)
play(prog_interp_ns)
mm.plot_sequence(prog_interp_ns)
