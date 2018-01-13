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
    print(bad('Error: %s' % text), file=sys.stderr)


def outitem(title, elems, indent=4):
    out(title)
    for e in elems:
        out('%s%s: %s' % (indent * ' ', *e))
    out()


def csv_writer():
    return csv.writer(sys.stdout)


colorama.init()
