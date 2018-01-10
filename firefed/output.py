import csv
import sys

import colorama
from colorama import Fore, Style


def out(*args, **kwargs):
    print(*args, **kwargs)


def good(text):
    return Fore.GREEN + text + Style.RESET_ALL


def bad(text):
    return Fore.RED + text + Style.RESET_ALL


def okay(text):
    return Fore.YELLOW + text + Style.RESET_ALL


def disabled(text):
    return Fore.LIGHTBLACK_EX + text + Style.RESET_ALL


def error(text):
    print(Fore.RED + 'Error: %s' % text + Style.RESET_ALL, file=sys.stderr)


def csv_writer():
    return csv.writer(sys.stdout)


colorama.init()
