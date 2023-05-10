from scipy.io.wavfile import read
import librosa
import numpy as np
import pyaudio
import socket


def read_wav_file(path: str):
    sr, wav_array = read(path)
    wav_array_float32 = wav_array.astype(dtype=np.float32, order='C') / 32768.0
    return sr, wav_array_float32


def process_wav(path: str, chunk_size: int, stft_params: dict):
    sr, audio_array = read_wav_file(path)
    mono_audio_array = (audio_array[:, 0] + audio_array[:, 1]) / 2.0
    audio_frames = []
    stft_audio_frames = []
    stft_audio_array = np.abs(librosa.stft(mono_audio_array, n_fft=int(chunk_size), hop_length=int(chunk_size), win_length=int(chunk_size/2)))
    counter = 0

    while len(audio_array) > 0:
        if len(audio_array) < chunk_size:
            frame = audio_array.copy()
            audio_array = []

        else:
            frame = audio_array[0:chunk_size]
            audio_array = audio_array[chunk_size:len(audio_array)]

        stft_frame = stft_audio_array[:, counter]
        audio_frames.append(frame)
        stft_audio_frames.append(stft_frame)
        counter += 1

    print(len(audio_frames))
    print(len(stft_audio_frames))
    return audio_frames, stft_audio_frames


def play_send_audio(audio_frames: list, stft_audio_frames: list, out_stream: pyaudio.Stream, client: socket.socket):
    for i in range(len(audio_frames)-1):
        with client:
            message = np.array2string(stft_audio_frames[i], precision=4, separator=',', suppress_small=False)
            client.sendall(message.encode())
        out_stream.write(audio_frames[i].tobytes(), exception_on_underflow=False)