import random
import numpy as np

grades = {
    'I': 0,
    'II': 1,
    'III': 2,
    'IV': 3,
    'V': 4,
    'VI': 5,
    'VII': 6
}

grades = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']

notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

happy_chords = [["Imaj7", "IVmaj7", "V7", "IVmaj7"], ["Imaj7", "IVmaj7", "V7", "VIm"], ["Imaj7", "V7", "VIm", "IVmaj7"], ["Imaj7", "V7", "VIm", "IVmaj7"], [
    "Imaj7", "VIm", "IVmaj7", "V7"], ["IV", "Imaj7", "V7", "VIm7"], ["IV", "V7", "Imaj7", "VIm6"], ["IV", "VIm", "Imaj7", "V7"]]
sad_chords = [["VIm", "IVmaj7", "Imaj7", "V7"], ["VIm", "IVmaj7", "Imaj7", "V9"], ["Imaj7", "VII", "VIm", "V7"], [
    "Imaj7", "VIm", "IIIm", "VII"], ["Imaj7", "VII", "VIm", "IVmaj7"], ["Imaj7", "VIm", "IIIm", "IVmaj7"]]
dance_chords = [["Imaj7", "IVmaj7", "V7", "IVmaj7"], ["Imaj7", "IV6", "V7", "VIm6"], ["Imaj7", "VIm", "IVmaj7", "V7"], [
    "IIm7", "V7", "Imaj7", "Imaj7"], ["IVmaj7", "V7", "Imaj7", "VIm6"], ["V7", "VIm7", "IV7", "V7"], ["VIm", "IVmaj7", "Imaj7", "V7"]]
not_dance_chords = [["I7", "VII", "VIm7", "V7"], ["I6", "VIm7", "III7", "VII"], [
    "Imaj7", "VII", "VIm", "IV7"], ["VIm", "IVmaj7", "Imaj7", "V9"], ["VIm", "IVmaj7", "Imaj7", "V79"], ["IV", "Imaj7", "V7", "VIm7"]]

# TODO have different chord progressions for each mood
MOOD_CHORD_DICT = {
    'happy': happy_chords,
    'exciting': dance_chords,
    'relaxing': not_dance_chords,
    'serene': not_dance_chords,
    'bored': not_dance_chords,
    'sad': sad_chords,
    'anxious': sad_chords,
    'angry': sad_chords,
}


def build_scale(key):
    ind = notes.index(key)
    major_scale = [notes[ind], notes[(ind + 2) % 12], notes[(ind + 4) % 12], notes[(
        ind + 5) % 12], notes[(ind + 7) % 12], notes[(ind + 9) % 12], notes[(ind + 11) % 12], notes[ind]]
    return major_scale


def choose_chords(va_value: str, key: str):
    moods = list(MOOD_CHORD_DICT.keys())

    if va_value not in moods:
        va_value = random.choice(moods)
    chords = random.choice(MOOD_CHORD_DICT[va_value])

    if key is None:
        key = random.choice(notes)
    scale = build_scale(key)
    new_chords = []
    for seq in chords:
        removed = seq.replace('7', '').replace('a', '').replace(
            '6', '').replace('9', '').replace('b', '').replace('m', '').replace('j', '').replace('5', '')
        if (removed != seq):
            removed_element = ""
            for lettera in seq:
                if lettera not in removed:
                    removed_element += lettera
        else:
            removed_element = ''

        new_chords.append(scale[grades[removed]]+removed_element)

    return new_chords, key

class ChordsMarkovChain:

    def __init__(self):
        self.__key = random.choice(notes)
        self.__scale = self._build_scale(self.__key)
        self.__prev_chords = []

        # TODO fill with possible chord symbols for every mood, ordered from left to right
        self._mood_chords_dict = {
            'happy': 'Imaj7 IImin7 IIImin7 IVmaj7 V7 VImin7 II7 III7'.split(' '),
            'exciting': [],
            'relaxing': [],
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
            'relaxing': np.array([[]]),
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
                               [],
                               []]),
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
        split_symbol = ''
        for c in reversed(range(len(symbol))):
            if symbol[c] in separators:
                split_symbol = symbol.rsplit(symbol[c], 1)
                split_symbol[0] += symbol[c]
                break

        if split_symbol == '':
            raise ValueError("Incorrect symbol found, was "+symbol)

        chord = str(self.__scale[grades.index(split_symbol[0])] + split_symbol[1])
        return chord

    def _build_scale(self, key: str):
        ind = notes.index(key)
        major_scale = [notes[ind], notes[(ind + 2) % 12], notes[(ind + 4) % 12], notes[(ind + 5) % 12],
                       notes[(ind + 7) % 12], notes[(ind + 9) % 12], notes[(ind + 11) % 12], notes[ind]]
        return major_scale

mark = ChordsMarkovChain()
print(mark.get_next_chord_progression('happy', 4))
print(mark.get_next_chord_progression('sad', 4))
mark.set_key('C#')
print('')
print(mark.get_next_chord_progression('happy', 4))
print(mark.get_next_chord_progression('sad', 4))