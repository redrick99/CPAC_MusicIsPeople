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


class BColors:
    """ Colors used to print and debug
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
    if __PRINTING_ACTIVE:
        print(BColors.OKGREEN + "[OK] " + str(string) + BColors.ENDC, flush=flush)


def print_info(string, flush=True):
    if __PRINTING_ACTIVE:
        print(BColors.OKBLUE + "[INFO] " + BColors.UNDERLINE + str(string) + BColors.ENDC, flush=flush)


def print_data(data, flush=True):
    if __PRINTING_DATA_ACTIVE:
        print(BColors.OKCYAN + "[DATA] ", data, BColors.ENDC, flush=flush)


def print_data_alt_color(data, flush=True):
    if __PRINTING_DATA_ACTIVE:
        print(BColors.HEADER + "[DATA] ", data, BColors.ENDC, flush=flush)


def print_warning(string, flush=True):
    if __PRINTING_ACTIVE:
        print(BColors.WARNING + BColors.BOLD + "[WARNING] " + str(string) + BColors.ENDC, flush=flush)


def print_error(string, flush=True):
    if __PRINTING_ACTIVE:
        print(BColors.FAIL + BColors.BOLD + "[ERROR] " + str(string) + BColors.ENDC, flush=flush)


def print_dbg(string, flush=True):
    if __PRINTING_ACTIVE and __DEBUGGER_ACTIVE:
        print(BColors.OKGREEN + "[DBG] " + str(string) + BColors.ENDC, flush=flush)
