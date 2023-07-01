import os
from multiprocessing import Process, Event, Queue
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient
from audio_handling import *
from utilities import *
from neural_network.chords_progression import moods
import neural_network.neural_network as nn

waiting_for_feedback = False
controller_connected = False


def default_handler(address, *args):
    """ Default osc message handler. Called only when a message has a generic, unrecognized osc address.

    **Args:**

    `address`: osc address assigned to this function.

    `args`: arguments of the incoming osc message.
    """
    print_warning("Received message with unrecognized OSC address: "+str(address))


def controller_connected_handler(address, fixed_args, *args):
    """ Default osc message handler. Called only when a message has a generic, unrecognized osc address.

    **Args:**

    `address`: osc address assigned to this function.

    `fixed_args`: arguments that are passed down from the python script and as such are fixed.

    `args`: arguments of the incoming osc message.
    """
    global controller_connected
    controller_connected = True
    _client_controller = fixed_args[0]
    _client_controller.send_message("/Controller/Connected", True)
    print_info("Connected to osc controller")


def ping_handler(address, fixed_args, *args):
    """ Handler for a ping osc message. Called to check if the osc controller is still connected and to check if
    for some reason it is blocked in a wrong state (loading, ...).

    **Args:**

    `address`: osc address assigned to this function.

    `fixed_args`: arguments that are passed down from the python script and as such are fixed.

    `args`: arguments of the incoming osc message.
    """
    is_voting = args[0]
    feedback_event = fixed_args[1]
    print_info("User is voting: "+str(is_voting))
    if not is_voting and not feedback_event.is_set():
        _client_controller = fixed_args[0]
        _client_controller.send_message("/Controller/VoteStart", True)

    elif is_voting and feedback_event.is_set():
        _client_controller = fixed_args[0]
        _client_controller.send_message("/Controller/VoteStop", True)


def feedback_handler(address, fixed_args, *args):
    """ Handler for a feedback osc message. Called when feedback is received from the osc controller, it parses the
    message into readable values and puts them in a multiprocessing queue for the main thread to start processing.

    **Args:**

    `address`: osc address assigned to this function.

    `fixed_args`: arguments that are passed down from the python script and as such are fixed.

    `args`: arguments of the incoming osc message.
    """
    feed_queue = fixed_args[0]
    feed_event = fixed_args[1]

    if not feed_event.is_set():
        try:
            feedback = []
            feedback.append(bool(args[0]))
            feedback.append(float(args[1]))
            feedback.append(float(args[2]))
            feedback.append(str(args[3]).lower())
            if feedback[3] not in moods:  # Checks if the mood can be used to generate the song
                raise NotImplementedError("Couldn't recognize mood, was: " + radar_mood_string)

            print_data_alt_color("Feedback: " + str(feedback[0]) + " " + str(feedback[3]))
            feed_queue.put(feedback)

        except NotImplementedError as nie:
            print_error(nie)
        except ValueError as ve:
            print_error(ve)
        except Exception as e:
            raise(e)
            print_error("Couldn't read incoming feedback (Broad Exception)")
        finally:
            return

    print_warning("Received feedback while producing song")


def server_worker(queue, event, client_controller):
    """ Creates a new OSC server and blocks the thread until an OSC message is received.

    **Args:**

    `queue`: Multiprocessing queue used to send parsed feedback from the OSC external controller.

    `event`: Multiprocessing event used to know if the program is currently running or if it is waiting for a feedback.

    `client_controller`: OSC client used to send messages to the external OSC controller.
    """
    dispatcher = Dispatcher()
    dispatcher.map("/Controller/Ping", ping_handler, client_controller, event)
    dispatcher.map("/Controller/Feedback", feedback_handler, queue, event)
    dispatcher.map("/Controller/Connected/Confirm", controller_connected_handler, client_controller)
    dispatcher.set_default_handler(default_handler)
    server = BlockingOSCUDPServer((SERVER_IP, SERVER_PORT), dispatcher)

    server.serve_forever()  # Blocks forever


if __name__ == "__main__":
    # Connections setup
    client_controller = SimpleUDPClient(CLIENT_CONTROLLER_IP, CLIENT_CONTROLLER_PORT)  # Create controller client

    client_visualizer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create visualizer client
    client_visualizer.bind((CLIENT_VISUALIZER_IP, CLIENT_VISUALIZER_PORT))
    client_visualizer.listen(1)

    client_startstop = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create visualizer client
    client_startstop.bind((CLIENT_STARTSTOP_IP, CLIENT_STARTSTOP_PORT))
    client_startstop.listen(1)

    # Output device setup
    out_device_index = choose_sound_card_index()
    pa = pyaudio.PyAudio()
    out_stream = pa.open(
        rate=SAMPLE_RATE,
        channels=CHANNELS,
        format=pyaudio.paFloat32,
        frames_per_buffer=CHUNK_SIZE,
        output=True,
        output_device_index=out_device_index,
    )

    # Gets the absolute path up to the main file and initializes the neural network model
    main_path = os.path.dirname(__file__)
    nn.initialize_model(main_path)

    # Waits for connection to the visualizer
    print_info("Connecting to visualizer...")
    conn, address = client_visualizer.accept()
    active, address_active = client_startstop.accept()
    print_success("Connected to visualizer!")

    # Creates multiprocessing objects
    feedback_event = Event()
    feedback_queue = Queue()
    server_process = Process(target=server_worker, args=(feedback_queue, feedback_event, client_controller,))
    server_process.start()

    while True:
        feedback = feedback_queue.get()  # Get feedback from OSC message
        feedback_event.set()  # Set running to true
        active.sendall("CREATING".encode())  # Send message to visualizer
        try:
            liked_the_song = feedback[0]
            radar_value_x = feedback[1]
            radar_value_y = feedback[2]
            radar_mood_string = feedback[3]

            mid = nn.create_song(va_mood=radar_mood_string,
                                 liked=liked_the_song)  # Creates the song as a midi from the nn
            wav = nn.create_wav(mid)  # Converts the PrettyMIDI object into a wav file
            print_success("Created midi and wav files")

            audio_frames, stft_audio_frames = get_audio_frames(wav,
                                                               CHUNK_SIZE)  # Splits song in frames for playback and
            # visualization
            active.sendall("START".encode())
            play_send_audio(audio_frames, stft_audio_frames, out_stream, conn)

        except Exception as e:
            print_error(e)

        finally:
            # Once done, prepare to receive another message
            waiting_for_feedback = True
            active.sendall("STOP".encode())
            feedback_event.clear()
