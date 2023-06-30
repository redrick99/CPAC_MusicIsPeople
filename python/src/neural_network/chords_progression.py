import os
import random
import numpy as np
import pandas as pd

grades = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']
notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
moods = ['happy', 'exciting', 'relaxing', 'serene', 'bored', 'sad', 'anxious', 'angry']


class ChordsMarkovChain:
    """ Implements a second order markov chain used to get the next chord progression to feed to the neural network. """

    def __init__(self, main_path: str):
        """ Constructor for ChordsMarkovChain class. It reads first and second order transitional arrays along with
         their associated chord symbols from csv files given the path of the src folder.

        **Args:**

        ´main_path´: Path of the src folder passed down from the main script.
        """
        self.__key = random.choice(notes)
        self.__scale = self._build_scale(self.__key)
        self.__prev_chords = []
        self.__prev_chords_separator = "-"

        path_to_csv_chords = os.path.join(main_path, "resources", "mood_chords_symbols")
        path_to_csv_arrays = os.path.join(main_path, "resources", "mood_transition_arrays")

        happy_chords_symbols = [
            pd.read_csv(os.path.join(path_to_csv_chords, "happy_cs.csv"), index_col=False).to_numpy().transpose()[0].tolist(),
            pd.read_csv(os.path.join(path_to_csv_chords, "happy_cs2.csv"), index_col=False).to_numpy().transpose()[0].tolist()
        ]

        relaxing_chords_symbols = [
            pd.read_csv(os.path.join(path_to_csv_chords, "relaxing_cs.csv"), index_col=False).to_numpy().transpose()[0].tolist(),
            pd.read_csv(os.path.join(path_to_csv_chords, "relaxing_cs2.csv"), index_col=False).to_numpy().transpose()[0].tolist()
        ]

        sad_chords_symbols = [
            pd.read_csv(os.path.join(path_to_csv_chords, "sad_cs.csv"), index_col=False).to_numpy().transpose()[0].tolist(),
            pd.read_csv(os.path.join(path_to_csv_chords, "sad_cs2.csv"), index_col=False).to_numpy().transpose()[0].tolist()
        ]

        angry_chords_symbols = [
            pd.read_csv(os.path.join(path_to_csv_chords, "angry_cs.csv"), index_col=False).to_numpy().transpose()[0].tolist(),
            pd.read_csv(os.path.join(path_to_csv_chords, "angry_cs2.csv"), index_col=False).to_numpy().transpose()[0].tolist()
        ]

        happy_chords_tms = [
            pd.read_csv(os.path.join(path_to_csv_arrays, "happy_tm.csv"), index_col=False).to_numpy(),
            pd.read_csv(os.path.join(path_to_csv_arrays, "happy_tm2.csv"), index_col=False).to_numpy()
        ]

        relaxing_chords_tms = [
            pd.read_csv(os.path.join(path_to_csv_arrays, "relaxing_tm.csv"), index_col=False).to_numpy(),
            pd.read_csv(os.path.join(path_to_csv_arrays, "relaxing_tm2.csv"), index_col=False).to_numpy()
        ]

        sad_chords_tms = [
            pd.read_csv(os.path.join(path_to_csv_arrays, "sad_tm.csv"), index_col=False).to_numpy(),
            pd.read_csv(os.path.join(path_to_csv_arrays, "sad_tm2.csv"), index_col=False).to_numpy()
        ]

        angry_chords_tms = [
            pd.read_csv(os.path.join(path_to_csv_arrays, "angry_tm.csv"), index_col=False).to_numpy(),
            pd.read_csv(os.path.join(path_to_csv_arrays, "angry_tm2.csv"), index_col=False).to_numpy()
        ]

        # Contains first and second order chord symbols associated with the transitional arrays, divided by mood
        self._mood_chords_dict = {
            'happy': happy_chords_symbols,
            'exciting': happy_chords_symbols,
            'relaxing': relaxing_chords_symbols,
            'serene': relaxing_chords_symbols,
            'bored': sad_chords_symbols,
            'sad': sad_chords_symbols,
            'anxious': angry_chords_symbols,
            'angry': angry_chords_symbols,
        }

        # Contains first and second order transitional arrays, divided by mood
        self._mood_matrix_dict = {
            'happy': happy_chords_tms,
            'exciting': happy_chords_tms,
            'relaxing': relaxing_chords_tms,
            'serene': relaxing_chords_tms,
            'bored': sad_chords_tms,
            'sad': sad_chords_tms,
            'anxious': angry_chords_tms,
            'angry': angry_chords_tms,
        }

    def set_random_key(self):
        """ Sets a random key for the chord progression.
        """
        self.set_key(random.choice(notes))

    def set_key(self, key: str):
        """ Sets the key for the chord progression.

        **Args:**

        ´key´: New key to be set.
        """
        self.__key = key
        self.__scale = self._build_scale(key)

    def get_next_chord_progression(self, mood: str, chords_in_bar: int, new_song: bool):
        """ Generates a new chord progression either based on the previous or from scratch depending on
        if the user liked the previous song played by the application.

        **Args:**

        ´mood´: Mood of the progression to be generated.

        ´chords_in_bar´: Length of the chord progression in chords.

        ´new_song´: True if the user did not like the previous song.

        **Returns:**

        A new chord progression.
        """
        new_chord_progression = []

        if new_song or len(self.__prev_chords) == 0:
            self.set_random_key()
            self.__prev_chords = []
            self.__prev_chords.append(np.random.choice(self._mood_chords_dict[mood][0]))
            self.__prev_chords.append(self._get_next_chord(mood, ['', self.__prev_chords[-1]], order=1))

        new_chord_progression.append(self._get_next_chord(mood, [self.__prev_chords[-2], self.__prev_chords[-1]]))
        for i in range(1, chords_in_bar):
            if i == 1:
                prev_prev_chord = self.__prev_chords[-1]
            else:
                prev_prev_chord = new_chord_progression[i-2]
            prev_chord = new_chord_progression[i-1]
            next_chord = self._get_next_chord(mood, [prev_prev_chord, prev_chord])
            new_chord_progression.append(next_chord)

        self.__prev_chords = new_chord_progression.copy()
        print(new_chord_progression)
        for i in range(len(new_chord_progression)):
            new_chord_progression[i] = self._get_chord_from_symbol(new_chord_progression[i])

        return new_chord_progression

    def _get_next_chord(self, mood: str, prev_chords: list, order=2):
        """ Generates the next chord of the chord progression based on the previous chords.
        This function i recursive, as if an entry wasn't found in the second order transitional array for the two
        previous chords, the function is recalled with order=1.

        **Args:**

        ´mood´: Mood of the chords progression.

        ´prev_chords´: List containing the two previous chords.

        ´order´: Order of the markov chain to use.

        **Returns:**

        The next chord of the progression.
        """
        if order == 2:
            prev_chord_symbol = prev_chords[0] + self.__prev_chords_separator + prev_chords[1]
        elif order == 1:
            prev_chord_symbol = prev_chords[1]
        else:
            raise NotImplementedError("Order has to be 1 or 2, was "+str(order))
        m_matrix = self._mood_matrix_dict[mood][order-1]
        prev_possible_chords = self._mood_chords_dict[mood][order-1]
        try:
            next_possible_chords_index = prev_possible_chords.index(prev_chord_symbol)
            return np.random.choice(self._mood_chords_dict[mood][0], p=m_matrix[next_possible_chords_index])
        except ValueError:
            if order > 1:
                return self._get_next_chord(mood, prev_chords, order-1)  # Recursive call with order=1
            else:
                return np.random.choice(prev_possible_chords)

    def _get_chord_from_symbol(self, symbol: str):
        """ Converts the chord's symbol from grades to notes depending on the current chords progression key.

        **Args:**

        ´symbol´: Symbol of the chord to convert in grades.

        **Returns:**

        Symbol of the chord in its note representation.
        """
        separators = ['I', 'V']
        down_sharp_alt = '#b'
        split_symbol = ''
        for c in reversed(range(len(symbol))):  # Separates grade from quality of the chord
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
        """ Builds a new major scale based on the given key.

        **Args:**

        ´key´: Key from which to build the new scale.

        **Returns:**

        A list containing the major scale's notes.
        """
        ind = notes.index(key)
        major_scale = [notes[ind], notes[(ind + 2) % 12], notes[(ind + 4) % 12], notes[(ind + 5) % 12],
                       notes[(ind + 7) % 12], notes[(ind + 9) % 12], notes[(ind + 11) % 12], notes[ind]]
        return major_scale
