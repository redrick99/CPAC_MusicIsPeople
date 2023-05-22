import os
import random
import numpy as np
import pandas as pd

grades = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']
notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
moods = ['happy', 'exciting', 'relaxing', 'serene', 'bored', 'sad', 'anxious', 'angry']


class ChordsMarkovChain:

    def __init__(self, main_path: str):
        self.__key = random.choice(notes)
        self.__scale = self._build_scale(self.__key)
        self.__prev_chords = []

        path_to_csv_chords = os.path.join(main_path, "resources", "mood_chords_symbols")
        path_to_csv_arrays = os.path.join(main_path, "resources", "mood_transition_arrays")
        # TODO fill with possible chord symbols for every mood, ordered from left to right
        self._mood_chords_dict = {
            'happy': pd.read_csv(os.path.join(path_to_csv_chords, "happy_cs.csv"), index_col=False).to_numpy().transpose()[0].tolist(),
            'exciting': pd.read_csv(os.path.join(path_to_csv_chords, "happy_cs.csv"), index_col=False).to_numpy().transpose()[0].tolist(),
            'relaxing': pd.read_csv(os.path.join(path_to_csv_chords, "relaxing_cs.csv"), index_col=False).to_numpy().transpose()[0].tolist(),
            'serene': pd.read_csv(os.path.join(path_to_csv_chords, "relaxing_cs.csv"), index_col=False).to_numpy().transpose()[0].tolist(),
            'bored': pd.read_csv(os.path.join(path_to_csv_chords, "sad_cs.csv"), index_col=False).to_numpy().transpose()[0].tolist(),
            'sad': pd.read_csv(os.path.join(path_to_csv_chords, "sad_cs.csv"), index_col=False).to_numpy().transpose()[0].tolist(),
            'anxious': pd.read_csv(os.path.join(path_to_csv_chords, "angry_cs.csv"), index_col=False).to_numpy().transpose()[0].tolist(),
            'angry': pd.read_csv(os.path.join(path_to_csv_chords, "angry_cs.csv"), index_col=False).to_numpy().transpose()[0].tolist(),
        }

        # TODO fill with the transition matrix for every mood
        self._mood_matrix_dict = {
            'happy': pd.read_csv(os.path.join(path_to_csv_arrays, "happy_tm.csv"), index_col=False).to_numpy(),
            'exciting': pd.read_csv(os.path.join(path_to_csv_arrays, "happy_tm.csv"), index_col=False).to_numpy(),
            'relaxing': pd.read_csv(os.path.join(path_to_csv_arrays, "relaxing_tm.csv"), index_col=False).to_numpy(),
            'serene': pd.read_csv(os.path.join(path_to_csv_arrays, "relaxing_tm.csv"), index_col=False).to_numpy(),
            'bored': pd.read_csv(os.path.join(path_to_csv_arrays, "sad_tm.csv"), index_col=False).to_numpy(),
            'sad': pd.read_csv(os.path.join(path_to_csv_arrays, "sad_tm.csv"), index_col=False).to_numpy(),
            'anxious': pd.read_csv(os.path.join(path_to_csv_arrays, "angry_tm.csv"), index_col=False).to_numpy(),
            'angry': pd.read_csv(os.path.join(path_to_csv_arrays, "angry_tm.csv"), index_col=False).to_numpy(),
        }

    def set_random_key(self):
        self.set_key(random.choice(notes))

    def set_key(self, key: str):
        self.__key = key
        self.__scale = self._build_scale(key)

    def get_next_chord_progression(self, mood: str, chords_in_bar: int, new_song: bool):
        new_chord_progression = []

        if new_song or len(self.__prev_chords) == 0:
            self.set_random_key()
            self.__prev_chords = []
            self.__prev_chords.append(np.random.choice(self._mood_chords_dict[mood]))

        new_chord_progression.append(self._get_next_chord(mood, self.__prev_chords[-1]))

        for i in range(1, chords_in_bar):
            next_chord = self._get_next_chord(mood, new_chord_progression[i-1])
            new_chord_progression.append(next_chord)

        self.__prev_chords = new_chord_progression.copy()
        print(new_chord_progression)
        for i in range(len(new_chord_progression)):
            new_chord_progression[i] = self._get_chord_from_symbol(new_chord_progression[i])

        return new_chord_progression

    def _get_next_chord(self, mood: str, prev_chord: str):
        m_matrix = self._mood_matrix_dict[mood]
        next_possible_chords = self._mood_chords_dict[mood]
        try:
            next_possible_chords_index = next_possible_chords.index(prev_chord)
            next_chord = np.random.choice(next_possible_chords, p=m_matrix[next_possible_chords_index])
        except ValueError as e:
            print(e)
            next_chord = np.random.choice(next_possible_chords)

        return next_chord

    def _get_chord_from_symbol(self, symbol: str):
        separators = ['I', 'V']
        down_sharp_alt = '#b'
        split_symbol = ''
        for c in reversed(range(len(symbol))):
            if symbol[c] in separators:
                split_symbol = symbol.rsplit(symbol[c], 1)
                split_symbol[0] += symbol[c]
                break

        if split_symbol == '':
            raise ValueError("Incorrect symbol found, was "+symbol)

        chord = str(self.__scale[grades.index(split_symbol[0])] + split_symbol[1])
        if down_sharp_alt in chord:
            chord = chord.replace(down_sharp_alt, '')

        return chord

    def _build_scale(self, key: str):
        ind = notes.index(key)
        major_scale = [notes[ind], notes[(ind + 2) % 12], notes[(ind + 4) % 12], notes[(ind + 5) % 12],
                       notes[(ind + 7) % 12], notes[(ind + 9) % 12], notes[(ind + 11) % 12], notes[ind]]
        return major_scale
