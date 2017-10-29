import base64
import json
import ctypes
from ctypes import CDLL, c_char_p, cast, byref, c_void_p, string_at
from feature import feature
from output import info, error
from tabulate import tabulate


class NSSEntry(ctypes.Structure):

    _fields_ = [
        ('type', ctypes.c_uint),
        ('data', ctypes.c_void_p),
        ('len', ctypes.c_uint)
    ]


class NSSError(Exception):

    def __init__(self, name, message):
        super().__init__(name, message)
        self.name = name
        self.message = message

    def __str__(self):
        return '%s: %s' % self.args


class NSSWrapper:

    def __init__(self, libnss='libnss3.so', path='.'):
        self.nss = nss = CDLL(libnss)
        nss.PR_ErrorToString.restype = ctypes.c_char_p
        nss.PR_ErrorToName.restype = ctypes.c_char_p
        nss.PK11_GetInternalKeySlot.restype = ctypes.c_void_p
        nss.PK11_CheckUserPassword.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        res = self.nss.NSS_Init(bytes(path, 'utf-8'))
        if res != 0:
            self.handle_error()
        keyslot = self.nss.PK11_GetInternalKeySlot()
        if keyslot is None:
            self.handle_error()
        self.keyslot = keyslot

    def check_password(self, password):
        p_password = ctypes.c_char_p(bytes(password, 'utf-8'))
        res = self.nss.PK11_CheckUserPassword(self.keyslot, p_password)
        if res != 0:
            self.handle_error()

    def decrypt(self, val):
        raw = base64.b64decode(val)
        input_ = NSSEntry()
        output = NSSEntry()
        input_.data = cast(c_char_p(raw), c_void_p)
        input_.len = len(raw)
        res = self.nss.PK11SDR_Decrypt(byref(input_), byref(output), None)
        if res != 0:
            self.handle_error()
        data = string_at(output.data, output.len)
        return str(data, 'utf-8')

    def handle_error(self):
        nss = self.nss
        error = nss.PORT_GetError()
        error_str = str(nss.PR_ErrorToString(error), 'utf-8')
        error_name = str(nss.PR_ErrorToName(error), 'utf-8')
        raise NSSError(error_name, error_str)

    def shutdown(self):
        self.nss.NSS_Shutdown()


class Logins(feature.Feature):

    def add_arguments(parser):
        parser.add_argument(
            '-l',
            '--libnss',
            help='path to libnss3',
            default='libnss3.so',
        )
        parser.add_argument(
            '-p',
            '--master-password',
            help='profile\'s master password',
            default='',
        )

    def run(self, args):
        logins = self.load_json('logins.json')['logins']
        info('%d logins found.\n' % len(logins))
        if args.summarize:
            return
        nss = NSSWrapper(args.libnss, self.ff.profile_dir)
        try:
            nss.check_password(args.master_password)
        except NSSError as e:
            if e.name == 'SEC_ERROR_BAD_PASSWORD':
                error('Incorrect master password.')
                nss.shutdown()
                return
        table = []
        for login in logins:
            host = login['hostname']
            username = nss.decrypt(login['encryptedUsername'])
            password = nss.decrypt(login['encryptedPassword'])
            table.append([host, username, password])
        info(tabulate(table, headers=['Host', 'Username', 'Password']))
        nss.shutdown()
