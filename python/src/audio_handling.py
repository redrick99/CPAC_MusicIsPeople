import librosa
import numpy as np
import pyaudio
import socket
import sys
np.set_printoptions(threshold=sys.maxsize, suppress=True)


def get_audio_frames(audio_array: np.ndarray, chunk_size: int = 2048):
    """ Performs a stft and splits the audio and obtained spectrum into smaller pieces ready to be played
    and visualized.

    **Args:**

    ´audio_array´: Array containing the song's signal.

    ´chunk_size´: Defines the length of the frames and the parameters of the stft.

    **Returns:**

    `tuple` containing the audio and the stft of the audio split in frames.
    """
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

    return audio_frames, stft_audio_frames


def play_send_audio(audio_frames: list, stft_audio_frames: list, out_stream: pyaudio.Stream, client: socket.socket):
    """ Plays the generated song frame by frame while simultaneously sending data to the client socket for
    visualization.

    **Args:**

    ´audio_frames´ Audio to be played split in frames.

    ´stft_audio_frames´: Stft of the audio to be played split in frames.

    ´out_stream´: Output stream used to play the song as output audio.

    ´client´: socket through which to send the visualization data.
    """
    for i in range(len(audio_frames) - 1):
        out_stream.write(audio_frames[i].tobytes(), exception_on_underflow=False)
        message = np.array2string(stft_audio_frames[i], precision=3, separator=',', suppress_small=True)
        if client is not None:
            client.sendall(message.encode())


def normalize(frame: np.array, norm_type: str):
    """ Normalizes a given array with a method specified as a string.

    **Args:**

    ´frame´: Array to normalize.

    ´norm_type´: Normalization type to apply.

    **Returns:**

    The normalized array.
    """
    _min = np.min(np.abs(frame))
    _max = np.max(np.abs(frame))
    if norm_type == "minmax":
        return (frame - _min) / (_max - _min)
    if norm_type == "peak":
        return frame / _max
    if norm_type == "mean":
        return frame - np.mean(frame)


def to_float32(array: np.array):
    """ Converts a given array to its `float32` representation.

    **Args:**

    ´array´: Array to be converted.

    **Returns:**

    The converted array.
    """
    array_float32 = array.astype(dtype=np.float32, order='C')
    if array.dtype == np.int32:
        return array_float32 / 2147483392.0
    if array.dtype == np.int16:
        return array_float32 / 32768.0
    if array.dtype == np.int8:
        return array_float32 / 255.0
    if array.dtype == np.float32:
        return array
