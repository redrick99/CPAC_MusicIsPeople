import time
import pyaudio
import socket
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient
from audio_handling import *

client_controller_ip = "127.0.0.1"
client_controller_port = 12345
client_controller = SimpleUDPClient(client_controller_ip, client_controller_port)  # Create controller client

client_visualizer_ip = "127.0.0.1"
client_visualizer_port = 54321
client_visualizer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create visualizer client
client_visualizer.bind((client_visualizer_ip, client_visualizer_port))
client_visualizer.listen(1)

server_ip = "127.0.0.1"
server_port = 55055

chunk_size = 4096
channels = 2
sample_rate = 44100

waiting_for_feedback = False

controller_connected = False


def print_handler(address, *args):
    print(f"{address}: {args}")


def default_handler(address, *args):
    print(f"DEFAULT {address}: {args}")


def controller_connected_handler(address, *args):
    global controller_connected
    if not controller_connected:
        controller_connected = True
        client_controller.send_message("/Controller/Connected", True)


def ping_handler(address, *args):
    is_voting = args[0]
    print("Is Voting: "+str(is_voting))
    if not is_voting and waiting_for_feedback:
        client_controller.send_message("/Controller/VoteStart", True)


def feedback_handler(address, fixed_args, *args):
    global waiting_for_feedback
    waiting_for_feedback = False
    liked_the_song = args[0]
    radar_value_x = args[1]
    radar_value_y = args[2]
    # TODO feed values into neural network and get a file

    out_stream = fixed_args[0]
    client_connection = fixed_args[1]
    audio_frames, stft_audio_frames = process_wav("./resources/Troppo_Fra.wav", chunk_size, None)
    play_send_audio(audio_frames, stft_audio_frames, out_stream, client_connection)

    waiting_for_feedback = True
    client_controller.send_message("/Controller/VoteStart", True)


pa = pyaudio.PyAudio()
out_stream = pa.open(
    rate=sample_rate,
    channels=channels,
    format=pyaudio.paFloat32,
    frames_per_buffer=chunk_size,
    output=True
)

print("Connecting to visualizer...")
conn, address = client_visualizer.accept()
print("Connected to visualizer")

dispatcher = Dispatcher()
dispatcher.map("/Controller/Ping", ping_handler)
dispatcher.map("/Controller/Feedback", feedback_handler, out_stream, conn)
dispatcher.map("/Controller/Connected/Confirm", controller_connected_handler)
dispatcher.set_default_handler(default_handler)
server = BlockingOSCUDPServer((server_ip, server_port), dispatcher)

print("Waiting for controller...")
audio_frames, stft_audio_frames = process_wav("./resources/TroppoFra16Bit.wav", chunk_size, None)
print("Playing...")
play_send_audio(audio_frames, stft_audio_frames, out_stream, conn)
print("Starting Server...")
# server.serve_forever()  # Blocks forever
