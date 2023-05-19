import os
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient
from audio_handling import *
from utilities import *
from neural_network.chords_progression import MOOD_CHORD_DICT
import neural_network.neural_network as nn

waiting_for_feedback = False
controller_connected = False


def default_handler(address, *args):
    """ Default osc message handler. Called only when a message has a generic, unrecognized osc address

    :param address: osc address assigned to this function
    :param args: arguments of the incoming osc message
    :return:
    """
    print_warning("Received message with unrecognized OSC address: "+str(address))


def controller_connected_handler(address, fixed_args, *args):
    """ Default osc message handler. Called only when a message has a generic, unrecognized osc address

    :param address: osc address assigned to this function
    :param fixed_args: arguments that are passed down from the python script and as such are fixed
    :param args: arguments of the incoming osc message
    :return:
    """
    global controller_connected
    # if not controller_connected:
    controller_connected = True
    _client_controller = fixed_args[0]
    _client_controller.send_message("/Controller/Connected", True)
    print_info("Connected to osc controller")


def ping_handler(address, fixed_args, *args):
    """ Handler for a ping osc message. Called to check if the osc controller is still connected and to check if
    for some reason it is blocked in a wrong state (loading, ...)

    :param address: osc address assigned to this function
    :param fixed_args: arguments that are passed down from the python script and as such are fixed
    :param args: arguments of the incoming osc message
    :return:
    """
    is_voting = args[0]
    print_info("User is voting: "+str(is_voting))
    if not is_voting and waiting_for_feedback:
        _client_controller = fixed_args[0]
        _client_controller.send_message("/Controller/VoteStart", True)


def feedback_handler(address, fixed_args, *args):
    """ Handler for a feedback osc message. Called when feedback is received from the osc controller, it creates
    a new song based on the feedback in the form of midi and wav, then plays the songs and sends the audio data
    over to the visualizer

    :param address: osc address assigned to this function
    :param fixed_args: arguments that are passed down from the python script and as such are fixed
    :param args: arguments of the incoming osc message
    :return:
    """
    global waiting_for_feedback
    waiting_for_feedback = False

    _out_stream = fixed_args[0]
    client_connection = fixed_args[1]
    client_connection_startstop = fixed_args[2]
    _client_controller = fixed_args[3]

    client_connection_startstop.sendall("CREATING".encode())

    try:
        liked_the_song = bool(args[0])
        radar_value_x = float(args[1])
        radar_value_y = float(args[2])
        radar_mood_string = str(args[3]).lower()

        print_data_alt_color("Feedback: "+str(liked_the_song)+" "+str(radar_mood_string))

        if radar_mood_string not in list(MOOD_CHORD_DICT.keys()):  # Checks if the mood can be used to generate the song
            raise NotImplementedError("Couldn't recognize mood, was: "+radar_mood_string)

        mid = nn.create_song(va_mood=radar_mood_string, liked=liked_the_song)  # Creates the song as a midi from the nn
        wav = nn.create_wav(mid)  # Converts the PrettyMIDI object into a wav file
        print_success("Created midi and wav files")

        audio_frames, stft_audio_frames = get_audio_frames(wav, CHUNK_SIZE)  # Splits song in frames for playback and visualization
        client_connection_startstop.sendall("START".encode())
        play_send_audio(audio_frames, stft_audio_frames, _out_stream, client_connection)

    except NotImplementedError as nie:
        print_error(nie)
    except Exception as e:
        print_error("Something went wrong while handling feedback")
        raise e

    finally:
        waiting_for_feedback = True
        client_connection_startstop.sendall("STOP".encode())
        _client_controller.send_message("/Controller/VoteStart", True)


if __name__ == "__main__":
    client_controller = SimpleUDPClient(CLIENT_CONTROLLER_IP, CLIENT_CONTROLLER_PORT)  # Create controller client

    client_visualizer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create visualizer client
    client_visualizer.bind((CLIENT_VISUALIZER_IP, CLIENT_VISUALIZER_PORT))
    client_visualizer.listen(1)

    client_startstop = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create visualizer client
    client_startstop.bind((CLIENT_STARTSTOP_IP, CLIENT_STARTSTOP_PORT))
    client_startstop.listen(1)

    pa = pyaudio.PyAudio()
    out_stream = pa.open(
        rate=SAMPLE_RATE,
        channels=CHANNELS,
        format=pyaudio.paFloat32,
        frames_per_buffer=CHUNK_SIZE,
        output=True
    )

    main_path = os.path.dirname(__file__)
    nn.initialize_model(main_path)

    print_info("Connecting to visualizer...")
    conn, address = client_visualizer.accept()
    active, address_active = client_startstop.accept()
    print_success("Connected to visualizer")

    dispatcher = Dispatcher()
    dispatcher.map("/Controller/Ping", ping_handler, client_controller)
    dispatcher.map("/Controller/Feedback", feedback_handler, out_stream, conn, active, client_controller)
    dispatcher.map("/Controller/Connected/Confirm", controller_connected_handler, client_controller)
    dispatcher.set_default_handler(default_handler)
    server = BlockingOSCUDPServer((SERVER_IP, SERVER_PORT), dispatcher)

    server.serve_forever()  # Blocks forever
