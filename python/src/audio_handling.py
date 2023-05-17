from scipy.io.wavfile import read
import librosa
import numpy as np
import pyaudio
import socket
import sys
np.set_printoptions(threshold=sys.maxsize, suppress=True)


def read_wav_file(path: str):
    sr, wav_array = read(path)
    wav_array_float32 = to_float32(wav_array)
    return sr, wav_array_float32


def get_audio_frames(audio_array: np.ndarray, chunk_size: int = 2048):
    audio_frames = []
    stft_audio_frames = []
    audio_array_norm = normalize(audio_array, "peak")
    stft_audio_array = np.abs(librosa.stft(audio_array_norm, n_fft=int(2*chunk_size), hop_length=int(chunk_size),
                                           win_length=int(chunk_size)), dtype=np.float32, order='C')
    stft_audio_array = normalize(stft_audio_array, "minmax")
    counter = 0

    while len(audio_array) > 0:
        if len(audio_array) < chunk_size:
            frame = np.pad(array=audio_array.copy(), pad_width=chunk_size-len(audio_array))
            audio_array = []
        else:
            frame = audio_array[0:chunk_size]
            audio_array = audio_array[chunk_size:len(audio_array)]

        stft_frame = stft_audio_array[:int(chunk_size/2), counter]
        audio_frames.append(frame)
        stft_audio_frames.append(stft_frame)
        counter += 1

    print("audio_frames: " + str(len(audio_frames)))
    print("stft_audio_frames: " + str(len(stft_audio_frames)))
    return audio_frames, stft_audio_frames


def process_wav(path: str, chunk_size: int, stft_params: dict):
    sr, audio_array = read_wav_file(path)
    mono_audio_array = (audio_array[:, 0] + audio_array[:, 1]) / 2.0
    mono_audio_array = normalize(mono_audio_array, "peak")
    audio_frames = []
    stft_audio_frames = []
    stft_audio_array = np.abs(librosa.stft(mono_audio_array, n_fft=int(chunk_size), hop_length=int(chunk_size / 2),
                                           win_length=int(chunk_size / 2)), dtype=np.float32, order='C')
    print(stft_audio_array.shape)
    stft_audio_array = normalize(stft_audio_array, "minmax")
    counter = 0

    while len(audio_array) > 0:
        if len(audio_array) < chunk_size:
            frame = audio_array.copy()
            audio_array = []

        else:
            frame = audio_array[0:int(chunk_size/2)]
            audio_array = audio_array[int(chunk_size/2):len(audio_array)]

        stft_frame = stft_audio_array[:1024, counter]
        audio_frames.append(frame)
        stft_audio_frames.append(stft_frame)
        counter += 1

    print("audio_frames: " + str(len(audio_frames)))
    print("stft_audio_frames: " + str(len(stft_audio_frames)))
    return audio_frames, stft_audio_frames


def play_send_audio(audio_frames: list, stft_audio_frames: list, out_stream: pyaudio.Stream, client: socket.socket, client_start_socket: socket.socket):
    try:
        client_start_socket.sendall("START".encode())
        for i in range(len(audio_frames) - 1):
            out_stream.write(audio_frames[i].tobytes(), exception_on_underflow=False)
            # print("Sending frame " + str(i) + " of " + str(len(audio_frames) - 1))
            message = np.array2string(stft_audio_frames[i], precision=3, separator=',', suppress_small=True)
            # print("MESSAGGIO" + message)
            if client is not None:
                client.sendall(message.encode())
        client_start_socket.sendall("STOP".encode())
    except:
        client_start_socket.sendall("STOP".encode())


def normalize(frame: np.array, type: str):
    _min = np.min(np.abs(frame))
    _max = np.max(np.abs(frame))
    if type == "minmax":
        return (frame - _min) / (_max - _min)
    if type == "peak":
        return frame / _max
    if type == "mean":
        return frame - np.mean(frame)


def to_float32(array: np.array):
    array_float32 = array.astype(dtype=np.float32, order='C')
    if array.dtype == np.int32:
        return array_float32 / 2147483392.0
    if array.dtype == np.int16:
        return array_float32 / 32768.0
    if array.dtype == np.int8:
        return array_float32 / 255.0
    if array.dtype == np.float32:
        return array
