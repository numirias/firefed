import logging

import colorama
from colorama import Fore, Style


colorama.init()

# TODO: dependency on colorama really necessary?
def error(text):
    print(Fore.RED + 'Error: %s' % text + Style.RESET_ALL)

def fatal(text):
    error(text)
    raise SystemExit(1)

def info(*args, **kwargs):
    print(*args, **kwargs)

def good(text):
    return Fore.GREEN + text + Style.RESET_ALL

def bad(text):
    return Fore.RED + text + Style.RESET_ALL

def okay(text):
    return Fore.YELLOW + text + Style.RESET_ALL

# TODO Refactor logging
logger = logging.getLogger('firefed')

def init_logger():
    logger.setLevel(logging.ERROR)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

init_logger()
log = logger.info
