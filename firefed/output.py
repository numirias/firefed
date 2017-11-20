from colorama import init, Fore, Style


init()

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
