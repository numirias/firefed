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


def warn(text):
    print(okay('Warning: %s' % text), file=sys.stderr)


def outitem(title, elems, indent=4):
    """Output formatted as list item."""
    out(title)
    max_key_len = max(len(key) for key, _ in elems) + 1
    for key, val in elems:
        key_spaced = ('%s:' % key).ljust(max_key_len)
        out('%s%s %s' % (indent * ' ', key_spaced, val))
    out()


def csv_writer():
    return csv.writer(sys.stdout)


colorama.init()
