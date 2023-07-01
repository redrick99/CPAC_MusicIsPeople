import warnings
import logging
import os
import copy
from utilities import *

with warnings.catch_warnings():
    print_info('Importing magenta modules...')
    warnings.simplefilter("ignore")
    from magenta.models.music_vae import configs
    from magenta.models.music_vae import TrainedModel
    from note_seq.sequences_lib import concatenate_sequences
    import note_seq as mm
    import tensorflow._api.v2.compat.v1 as tf
    # Removes Tensorflow logs and warnings
    tf.keras.utils.disable_interactive_logging()
    tf.get_logger().setLevel(logging.ERROR)
    tf.disable_v2_behavior()
    print_success('Imported magenta!')

import numpy as np
import pretty_midi
from note_seq.protobuf import music_pb2
from neural_network.chords_progression import ChordsMarkovChain

# DEFINITION PARAMETERS AND GLOBAL VARIABLES

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

chords_markov_chain = None

##--------------------------------------------------------------------

def initialize_model(main_path: str):
    """Initialize the models used for generation and interpolation importing the configuration of Google Magenta API.

    **Args:**
    
    `main_path`: Path of the src folder passed down from the main script.
    """
    global chords_markov_chain
    global CONFIG
    global MODEL
    global MODEL_PATH
    global CONFIG_INTERP
    global MODEL_INTERP
    global MODEL_INTERP_PATH
    global SF2_PATH

    chords_markov_chain = ChordsMarkovChain(main_path)
    SF2_PATH = os.path.join(main_path, SF2_PATH)
    MODEL_PATH = os.path.join(main_path, MODEL_PATH)
    MODEL_INTERP_PATH = os.path.join(main_path, MODEL_INTERP_PATH)

    with warnings.catch_warnings():
        print_info('Initializing NN models...')
        warnings.simplefilter("ignore")
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
        print_success('Models initialized!')


def slerp(p0, p1, t):
    """Spherical linear interpolation.

    **Args:**

    `p0`: The starting point of the interpolation.

    `p1`: The ending point of the interpolation.

    `t`: Evenly spaced samples, calculated over the interval [0, 1].

    **Returns:**

    The interpolated value between p0 and p1 at the given parameter value t.
    """
    omega = np.arccos(np.dot(np.squeeze(p0 / np.linalg.norm(p0)),
                      np.squeeze(p1 / np.linalg.norm(p1))))
    so = np.sin(omega)
    return np.sin((1.0 - t) * omega) / so * p0 + np.sin(t * omega) / so * p1


def chord_encoding(chord):
    """Encode a chord as a one-hot vector.

    **Args:**

    `chord`: The chord to be encoded

    **Returns:**

    The one-hot encoding of the chord.
    """
    index = mm.TriadChordOneHotEncoding().encode_event(chord)
    c = np.zeros([TOTAL_STEPS, CHORD_DEPTH])
    c[0, 0] = 1.0
    c[1:, index] = 1.0
    return c


def trim_sequences(seqs, num_seconds=BAR_SECONDS):
    """Trim the sequences to a specified duration.

    **Args:**

    `seqs`: List of music sequences to be trimmed.

    `num_seconds`: Duration in seconds to trim the sequences to. Default is BAR_SECONDS.
    """
    for i in range(len(seqs)):
        seqs[i] = mm.extract_subsequence(seqs[i], 0.0, num_seconds)
        seqs[i].total_time = num_seconds


def fix_instruments_for_concatenation(note_sequences):
    """Fixes instrument assignments for concatenation of note sequences.

    **Args:**

    `note_sequences`: List of note sequences to fix instrument assignments.
    """
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
    """Converts a NoteSequence to a MIDI file.

    **Args:**

    `note_sequence`: The NoteSequence to convert to MIDI.

    `bpm`: The tempo in beats per minute (BPM) for the resulting MIDI file.

    **Returns:**
    
    The MIDI file representation of the NoteSequence.
    """
    note_sequence = change_tempo(note_sequence, bpm)
    return mm.sequence_proto_to_pretty_midi(note_sequence)


def change_tempo(note_sequence, new_tempo):
    """Change the tempo of a NoteSequence to a new tempo.

    **Args:**

    `note_sequence`: The NoteSequence to change the tempo of.

    `new_tempo`: The new tempo in beats per minute (BPM).

    **Returns:**

     The NoteSequence with the tempo changed.
    """
    new_sequence = copy.deepcopy(note_sequence)
    ratio = note_sequence.tempos[0].qpm / float(new_tempo)
    for note in new_sequence.notes:
        note.start_time = note.start_time * ratio
        note.end_time = note.end_time * ratio
    new_sequence.tempos[0].qpm = new_tempo
    return new_sequence


def get_bpm_and_num_bars(mood: str, max_duration: float):
    """Get the BPM (beats per minute) and the number of bars based on the mood. 

    **Args:**

    `mood`: The mood category.

    `max_duration`: The maximum duration in seconds.

    **Returns:**

    A tuple containing the BPM and the number of bars.
    """
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
    """ Generate a music sequence based on the specified mood, user preference, and number of bars

    **Args:**

    `va_mood`: The mood category.

    `liked`: Indicates whether the user liked the previous generated sequence.

    `num_bars`: The number of bars to generate.

    **Returns:**
    
    The generated music sequence.
    """

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
    """Interpolate between songs based on the specified mood, user preference, number of bars, and BPM. 

    **Args:**

    `va_value`: The mood used for the generation of new song.

    `liked`: Indicates whether the user liked the previous generated sequence.

    `num_bars`: The number of bars to generate.

    `bpm`: The tempo in beats per minute (BPM) for the resulting interpolation.

    **Returns:**

    The interpolated music sequence.
    """
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

    z1 = []
    z2 = []
    seq_length = len(uploaded_seqs)
    for i in range(seq_length // 2):
        r1, _, _ = MODEL_INTERP.encode([uploaded_seqs[i]])
        z1.append(r1)
        r2, _, _ = MODEL_INTERP.encode([uploaded_seqs[i + seq_length // 2]])
        z2.append(r2)

    #num_bars = 32
    temperature = 0.2 
    z = []
    for r_z1,r_z2 in zip(z1,z2):
        z.append(np.array([slerp(np.squeeze(r_z1), np.squeeze(r_z2), t)
            for t in np.linspace(0, 1, 4)]))

    seqs_dec = [MODEL_INTERP.decode(length=TOTAL_STEPS, z=zi, temperature=temperature) for zi in z]

    recon_interp_ns = []
    for s in seqs_dec:
        trim_sequences(s)
        fix_instruments_for_concatenation(s)
        recon_interp_ns.append(concatenate_sequences(s))    
    
    trim_sequences(recon_interp_ns)
    fix_instruments_for_concatenation(recon_interp_ns)
    recon_interp_ns = concatenate_sequences(recon_interp_ns)
    return recon_interp_ns


def create_song(va_mood: str, liked: bool):
    """ Create a complete song based on the specified mood and user preference.

    **Args:**

    `va_mood`: The mood category choosen by the user

    `liked`: Indicates whether the user liked the previous generated sequence.

    **Returns:**

    The generated MIDI file representing the complete song.
    """
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
    """ Create a WAV audio file from a MIDI file using the specified SoundFont.

    **Args:**

    `midi`: The MIDI file to convert

    **Returns:**

    The audio waveform as a floating-point numpy array.
    """
    global SF2_PATH
    wav = midi.fluidsynth(fs=44100.0, sf2_path=SF2_PATH)
    return wav.astype(dtype=np.float32)
