import pretty_midi
import numpy as np
import os
import random
from multiprocessing import Lock
from scipy.io.wavfile import read, write
from neural_network.chords_progression import moods


class Song:
    def __init__(self, audio_file_path: str, midi_file_path: str, sr: int):
        self.__audio_file = read(audio_file_path)
        self.__midi_file = pretty_midi.PrettyMIDI(midi_file_path)
        self.__audio_file_path = audio_file_path
        self.__midi_file_path = midi_file_path
        self.__sr = sr
        self.__used = False

    def get_files(self):
        assert(not self.__used)
        self.__used = True
        return self.__audio_file, self.__midi_file

    def assign_new_files(self, audio_file: np.ndarray, midi_file: pretty_midi.PrettyMIDI):
        assert(np.abs(np.max(audio_file)) <= 1.0 and audio_file.dtype == float)
        self.__audio_file = audio_file
        self.__midi_file = midi_file
        write(self.__audio_file_path, self.__sr, audio_file)
        midi_file.write(self.__midi_file_path)
        self.__used = False

    def is_used(self):
        return self.__used


class SongsContainer:
    def __init__(self, path_to_files: str, mood: str, number_of_songs: int, sr: int):
        self.__path = os.path.join(path_to_files, mood)
        self.__songs = []
        for i in range(number_of_songs):
            audio_path = os.path.join(self.__path, mood+str(i)+".wav")
            midi_path = os.path.join(self.__path, mood+str(i)+".mid")
            self.__songs.append(Song(audio_path, midi_path, sr))
        self.__lock = Lock()

    def get_random_song(self):
        self.__lock.acquire()
        song_files = None
        unordered_songs = random.sample(self.__songs, len(self.__songs))
        for song in unordered_songs:
            if not song.is_used():
                song_files = song.get_files()
                break
        self.__lock.release()
        return song_files

    def assign_random_song(self, audio_file: np.ndarray, midi_file: pretty_midi.PrettyMIDI):
        self.__lock.acquire()
        unordered_songs = random.sample(self.__songs, len(self.__songs))
        for song in unordered_songs:
            if song.is_used():
                song.assign_new_files(audio_file, midi_file)
        self.__lock.release()


class SongsHandler:
    def __init__(self, path_to_files: str, number_of_songs: int, sr=44100):
        self.__mood_songs_dict = dict()
        for mood in moods:
            self.__mood_songs_dict[mood] = SongsContainer(path_to_files, mood, number_of_songs, sr)

    def get_song_of_mood(self, mood: str):
        assert mood in moods
        return self.__mood_songs_dict[mood].get_random_song()

    def assign_song_of_mood(self, mood: str, audio_file: np.ndarray, midi_file: pretty_midi.PrettyMIDI):
        assert mood in moods
        self.__mood_songs_dict[mood].assign_random_song(audio_file, midi_file)
