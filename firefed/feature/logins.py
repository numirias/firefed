import base64
import csv
import sys
import collections
import getpass
import ctypes
from ctypes import CDLL, c_char_p, cast, byref, c_void_p, string_at
from tabulate import tabulate

from firefed.feature import Feature, output_formats, argument
from firefed.output import out, fatal


class SECItem(ctypes.Structure):

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
    """Wrapper for access to Mozilla's Network Security Services library."""

    def __init__(self, libnss='libnss3.so', path='.'):
        try:
            self.nss = nss = CDLL(libnss)
        except OSError as e:
            fatal('Can\'t open libnss: %s' % e)
        nss.PR_ErrorToString.restype = c_char_p
        nss.PR_ErrorToName.restype = c_char_p
        nss.PK11_GetInternalKeySlot.restype = c_void_p
        nss.PK11_CheckUserPassword.argtypes = [c_void_p, c_char_p]
        res = self.nss.NSS_Init(bytes(str(path), 'utf-8'))
        if res != 0:
            self.handle_error() # pragma: no cover
        keyslot = self.nss.PK11_GetInternalKeySlot()
        if keyslot is None:
            self.handle_error() # pragma: no cover
        self.keyslot = keyslot

    def check_password(self, password):
        p_password = ctypes.c_char_p(bytes(password, 'utf-8'))
        res = self.nss.PK11_CheckUserPassword(self.keyslot, p_password)
        if res != 0:
            self.handle_error() # pragma: no cover

    def decrypt(self, val):
        raw = base64.b64decode(val)
        input_ = SECItem()
        output = SECItem()
        input_.data = cast(c_char_p(raw), c_void_p)
        input_.len = len(raw)
        res = self.nss.PK11SDR_Decrypt(byref(input_), byref(output), None)
        if res != 0:
            self.handle_error() # pragma: no cover
        data = string_at(output.data, output.len)
        return str(data, 'utf-8')

    def handle_error(self):
        nss = self.nss
        error = nss.PORT_GetError()
        error_str = str(nss.PR_ErrorToString(error), 'utf-8')
        error_name = str(nss.PR_ErrorToName(error), 'utf-8')
        raise NSSError(error_name, error_str)


Login = collections.namedtuple('Login', 'host username password')


@argument('-l', '--libnss', default='libnss3.so', help='path to libnss3')
@argument('-p', '--master-password', help='profile\'s master password')
@output_formats(['table', 'list', 'csv'], default='table')
class Logins(Feature):

    def prepare(self):
        self.nss = NSSWrapper(self.libnss, self.session.profile)
        logins_json = self.load_json('logins.json')['logins']
        return logins_json

    @staticmethod
    def summarize(logins_json):
        out('%d logins found.' % len(logins_json))

    def run(self, logins_json):
        nss = self.nss
        if self.master_password is None:
            self.master_password = getpass.getpass(prompt='Master password: ')
            out()
        try:
            nss.check_password(self.master_password)
        except NSSError as e:
            if e.name == 'SEC_ERROR_BAD_PASSWORD':
                fatal('Incorrect master password (%s)' % e)
        logins = [Login(
            host=login['hostname'],
            username=nss.decrypt(login['encryptedUsername']),
            password=nss.decrypt(login['encryptedPassword']),
        ) for login in logins_json]
        self.build_format(logins)

    @staticmethod
    def build_table(logins):
        out(tabulate(logins, headers=['Host', 'Username', 'Password']))

    @staticmethod
    def build_list(logins):
        for host, username, password in logins:
            out(host)
            out('    Username: %s' % username)
            out('    Password: %s' % password)
            out()

    @staticmethod
    def build_csv(logins):
        writer = csv.DictWriter(sys.stdout, fieldnames=Login._fields)
        writer.writeheader()
        writer.writerows([l._asdict() for l in logins])
