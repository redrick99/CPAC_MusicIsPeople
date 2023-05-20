import random
import numpy as np

grades = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']
notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
moods = ['happy', 'exciting', 'relaxing', 'serene', 'bored', 'sad', 'anxious', 'angry']


class ChordsMarkovChain:

    def __init__(self):
        self.__key = random.choice(notes)
        self.__scale = self._build_scale(self.__key)
        self.__prev_chords = []

        # TODO fill with possible chord symbols for every mood, ordered from left to right
        self._mood_chords_dict = {
            'happy': 'Imaj7 IImin7 IIImin7 IVmaj7 V7 VImin7 II7 III7'.split(' '),
            'exciting': [],
            'relaxing': 'I6 IImin7 IIImin7 IV6 V6 VImin7 VIb IVmaj7 IIIb'.split(' '),
            'serene': [],
            'bored': [],
            'sad': 'Imaj7 IImin7 IIImin7 IVmaj7 V7 VImin7 VIImin7 IVmin7 III7'.split(' '),
            'anxious': [],
            'angry': 'Imaj7 IImin7 IIImin7 IVmaj7 V7 VImin7 VIImin7 VIIo7 V6 III7 I7'.split(' '),
        }

        # TODO fill with the transition matrix for every mood
        self._mood_matrix_dict = {
            'happy': np.array([[0.00, 0.13, 0.00, 0.13, 0.42, 0.13, 0.13, 0.06],
                               [0.00, 0.00, 0.00, 0.25, 0.75, 0.00, 0.00, 0.00],
                               [0.00, 0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00],
                               [0.27, 0.09, 0.09, 0.00, 0.55, 0.00, 0.00, 0.00],
                               [0.16, 0.00, 0.00, 0.34, 0.16, 0.34, 0.00, 0.00],
                               [0.16, 0.16, 0.00, 0.52, 0.00, 0.00, 0.16, 0.00],
                               [0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00],
                               [0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00]]),
            'exciting': np.array([[]]),
            'relaxing': np.array([[0.00, 0.08, 0.16, 0.37, 0.08, 0.16, 0.08, 0.00, 0.08],
                                  [0.00, 0.00, 0.00, 0.25, 0.75, 0.00, 0.00, 0.00, 0.00],
                                  [0.00, 0.00, 0.00, 0.33, 0.33, 0.34, 0.00, 0.00, 0.00],
                                  [0.30, 0.10, 0.10, 0.10, 0.40, 0.00, 0.00, 0.00, 0.00],
                                  [0.25, 0.00, 0.00, 0.00, 0.50, 0.25, 0.00, 0.00, 0.00],
                                  [0.00, 0.20, 0.00, 0.60, 0.20, 0.00, 0.00, 0.00, 0.00],
                                  [0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00],
                                  [0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00],
                                  [0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00]]),
            'serene': np.array([[]]),
            'bored': np.array([[]]),
            'sad': np.array([[0.00, 0.00, 0.00, 0.00, 0.67, 0.33, 0.00, 0.00, 0.00],
                             [0.25, 0.25, 0.00, 0.00, 0.25, 0.00, 0.00, 0.25, 0.00],
                             [0.25, 0.00, 0.25, 0.25, 0.00, 0.00, 0.25, 0.00, 0.00],
                             [0.17, 0.00, 0.00, 0.00, 0.00, 0.50, 0.00, 0.00, 0.33],
                             [0.11, 0.11, 0.22, 0.34, 0.00, 0.22, 0.00, 0.00, 0.00],
                             [0.10, 0.20, 0.10, 0.20, 0.30, 0.10, 0.00, 0.00, 0.00],
                             [0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00],
                             [1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
                             [0.00, 0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00]]),
            'anxious': np.array([[]]),
            'angry': np.array([[0.00, 0.00, 0.33, 0.33, 0.00, 0.00, 0.00, 0.00, 0.34, 0.00, 0.00],
                               [0.50, 0.00, 0.00, 0.00, 0.50, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
                               [0.00, 0.00, 0.20, 0.20, 0.20, 0.40, 0.00, 0.00, 0.00, 0.00, 0.00],
                               [0.00, 0.00, 0.78, 0.11, 0.11, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
                               [0.00, 0.00, 0.50, 0.50, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
                               [0.11, 0.00, 0.11, 0.22, 0.00, 0.00, 0.00, 0.11, 0.23, 0.11, 0.11],
                               [0.50, 0.00, 0.00, 0.00, 0.50, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
                               [0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
                               [0.00, 0.17, 0.17, 0.50, 0.00, 0.17, 0.00, 0.00, 0.00, 0.00, 0.00],
                               [0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
                               [0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]]),
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
