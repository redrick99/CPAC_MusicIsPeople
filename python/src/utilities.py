import pyaudio

CLIENT_CONTROLLER_IP = "127.0.0.1"
CLIENT_CONTROLLER_PORT = 12345

CLIENT_VISUALIZER_IP = "127.0.0.1"
CLIENT_VISUALIZER_PORT = 54321

CLIENT_STARTSTOP_IP = "127.0.0.1"
CLIENT_STARTSTOP_PORT = 13524

SERVER_IP = "127.0.0.1"
SERVER_PORT = 55055

CHUNK_SIZE = 2048
CHANNELS = 1
SAMPLE_RATE = 44100


def choose_sound_card_index() -> int:
    """Gets the sound card index for live audio from user input.

    **Returns:**

    The index of the chosen sound card (depends on the number of available sound cards).
    """

    pa = pyaudio.PyAudio()
    info = pa.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    usable_devices = []
    sound_card_list = []

    for i in range(0, numdevices):
        if (pa.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels')) > 0:
            sound_card_list.append("(" + str(i) + ") " + pa.get_device_info_by_host_api_device_index(0, i).get('name'))
            usable_devices.append(i)

    while True:
        print("\n[Available Output Devices]")
        for s in sound_card_list:
            print(s)
        user_input = input("Please select your preferred output device (type only the index): ")
        try:
            user_input = int(user_input)
            if user_input in usable_devices:
                return user_input
            print("Please type only the number of the output you want to use (from 0 to " + str(numdevices) + ")")
        except Exception:
            print("Please enter a valid number")



class BColors:
    """ Colors used to print and debug.
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


__DEBUGGER_ACTIVE = True
__PRINTING_ACTIVE = True
__PRINTING_DATA_ACTIVE = True


def print_success(string, flush=True):
    """ Prints with [OK] and green color signature.

    **Args:**

    ´string´: String to print.

    ´flush´: Standard print's flush parameter.
    """
    if __PRINTING_ACTIVE:
        print(BColors.OKGREEN + "[OK] " + str(string) + BColors.ENDC, flush=flush)


def print_info(string, flush=True):
    """ Prints with [INFO] and blue color signature.

    **Args:**

    ´string´: String to print.

    ´flush´: Standard print's flush parameter.
    """
    if __PRINTING_ACTIVE:
        print(BColors.OKBLUE + "[INFO] " + BColors.UNDERLINE + str(string) + BColors.ENDC, flush=flush)


def print_data(data, flush=True):
    """ Prints with [DATA] and cyan color signature.

    **Args:**

    ´string´: String to print.

    ´flush´: Standard print's flush parameter.
    """
    if __PRINTING_DATA_ACTIVE:
        print(BColors.OKCYAN + "[DATA] ", data, BColors.ENDC, flush=flush)


def print_data_alt_color(data, flush=True):
    """ Prints with [DATA] and magenta color signature.

    **Args:**

    ´string´: String to print.

    ´flush´: Standard print's flush parameter.
    """
    if __PRINTING_DATA_ACTIVE:
        print(BColors.HEADER + "[DATA] ", data, BColors.ENDC, flush=flush)


def print_warning(string, flush=True):
    """ Prints with [WARNING] and yellow color signature.

    **Args:**

    ´string´: String to print.

    ´flush´: Standard print's flush parameter.
    """
    if __PRINTING_ACTIVE:
        print(BColors.WARNING + BColors.BOLD + "[WARNING] " + str(string) + BColors.ENDC, flush=flush)


def print_error(string, flush=True):
    """ Prints with [ERROR] and red color signature.

    **Args:**

    ´string´: String to print.

    ´flush´: Standard print's flush parameter.
    """
    if __PRINTING_ACTIVE:
        print(BColors.FAIL + BColors.BOLD + "[ERROR] " + str(string) + BColors.ENDC, flush=flush)


def print_dbg(string, flush=True):
    """ Prints with [DBG] and green color signature.

    **Args:**

    ´string´: String to print.

    ´flush´: Standard print's flush parameter.
    """
    if __PRINTING_ACTIVE and __DEBUGGER_ACTIVE:
        print(BColors.OKGREEN + "[DBG] " + str(string) + BColors.ENDC, flush=flush)
