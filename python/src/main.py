import os
import socket
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient
from audio_handling import *
from utilities import *
from neural_network.chords_progression import MOOD_CHORD_DICT
import neural_network.neural_network as nn


client_controller_ip = "127.0.0.1"
client_controller_port = 12345
client_controller = SimpleUDPClient(client_controller_ip, client_controller_port)  # Create controller client

client_visualizer_ip = "127.0.0.1"
client_visualizer_port = 54321
client_visualizer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create visualizer client
client_visualizer.bind((client_visualizer_ip, client_visualizer_port))
client_visualizer.listen(1)

client_startstop_ip = "127.0.0.1"
client_startstop_port = 13524
client_startstop = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create visualizer client
client_startstop.bind((client_startstop_ip, client_startstop_port))
client_startstop.listen(1)

server_ip = "127.0.0.1"
server_port = 55055

chunk_size = 2048
channels = 1
sample_rate = 44100

waiting_for_feedback = False
controller_connected = False


def default_handler(address, *args):
    print_warning("Received message with unrecognized OSC address: "+str(address))


def controller_connected_handler(address, *args):
    global controller_connected
    if not controller_connected:
        controller_connected = True
        client_controller.send_message("/Controller/Connected", True)


def ping_handler(address, *args):
    is_voting = args[0]
    print_info("User is voting: "+str(is_voting))
    if not is_voting and waiting_for_feedback:
        client_controller.send_message("/Controller/VoteStart", True)


def feedback_handler(address, fixed_args, *args):
    global waiting_for_feedback
    waiting_for_feedback = False

    try:
        liked_the_song = bool(args[0])
        radar_value_x = float(args[1])
        radar_value_y = float(args[2])
        radar_mood_string = str(args[3]).lower()
    except:
        print_error("Error while parsing feedback arguments")
        return

    print_info("Received feedback: "+str(liked_the_song)+" "+str(radar_value_x)+" "+str(radar_value_y)+" "+str(radar_mood_string))

    if radar_mood_string not in list(MOOD_CHORD_DICT.keys()):
        print_warning("Couldn't recognize mood, was: "+radar_mood_string)
        return

    mid = nn.create_song(va_value=radar_mood_string, liked=liked_the_song)
    wav = nn.create_wav(mid)
    print_success("Created midi and wav files")

    out_stream = fixed_args[0]
    client_connection = fixed_args[1]
    client_connection_startstop = fixed_args[2]
    audio_frames, stft_audio_frames = get_audio_frames(wav, chunk_size)
    play_send_audio(audio_frames, stft_audio_frames, out_stream, client_connection, client_connection_startstop)

    waiting_for_feedback = True
    client_controller.send_message("/Controller/VoteStart", True)


main_path = os.path.dirname(__file__)
pa = pyaudio.PyAudio()
out_stream = pa.open(
    rate=sample_rate,
    channels=channels,
    format=pyaudio.paFloat32,
    frames_per_buffer=chunk_size,
    output=True
)
nn.initialize_model(main_path)

print_info("Connecting to visualizer...")
conn, address = client_visualizer.accept()
active, address = client_startstop.accept()
print_success("Connected to visualizer")

dispatcher = Dispatcher()
dispatcher.map("/Controller/Ping", ping_handler)
dispatcher.map("/Controller/Feedback", feedback_handler, out_stream, conn, active)
dispatcher.map("/Controller/Connected/Confirm", controller_connected_handler)
dispatcher.set_default_handler(default_handler)
server = BlockingOSCUDPServer((server_ip, server_port), dispatcher)

server.serve_forever()  # Blocks forever
