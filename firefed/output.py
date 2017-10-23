from colorama import init, Fore, Style

init()

def error(text):
    print(Fore.RED + 'Error: %s' % text + Style.RESET_ALL)

def info(*args, **kwargs):
    print(*args, **kwargs)

def good(text):
    return Fore.GREEN + text + Style.RESET_ALL

def bad(text):
    return Fore.RED + text + Style.RESET_ALL
