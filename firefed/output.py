import logging
import sys
import colorama
from colorama import Fore, Style
from firefed.__version__ import __title__


def out(*args, **kwargs):
    print(*args, **kwargs)

def good(text):
    return Fore.GREEN + text + Style.RESET_ALL

def bad(text):
    return Fore.RED + text + Style.RESET_ALL

def okay(text):
    return Fore.YELLOW + text + Style.RESET_ALL

def error(text):
    print(Fore.RED + 'Error: %s' % text + Style.RESET_ALL, file=sys.stderr)

def fatal(text):
    error(text)
    raise SystemExit(1)

def make_logger():
    logger = logging.getLogger(__title__)
    logger.setLevel(logging.ERROR)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

colorama.init()
logger = make_logger()
info = logger.info
