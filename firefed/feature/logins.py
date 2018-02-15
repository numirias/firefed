import base64
import ctypes
from ctypes import CDLL, byref, c_char_p, c_void_p, cast, string_at
import getpass

import attr
from attr import attrib, attrs

from firefed.feature import Feature, arg, formatter
from firefed.output import out, outitem
from firefed.util import tabulate, fatal


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


@attrs
class Login:

    host = attrib()
    username = attrib()
    password = attrib()


@attrs
class Logins(Feature):
    """List saved logins.

    You can provide a valid master password, but firefed doesn't (yet) support
    cracking an unkown password.
    """

    libnss = arg('-l', '--libnss', default='libnss3.so',
                 help='path to libnss3')
    password = arg('-p', '--master-password',
                   help='profile\'s master password (If not set, an empty '
                        'password is tried. If that fails, you\'re prompted.)')

    def prepare(self):
        self.nss = NSSWrapper(self.libnss, self.session.profile)
        logins_json = self.load_json('logins.json')['logins']
        self.logins = logins_json

    def summarize(self):
        out('%d logins found.' % len(self.logins))

    def run(self):
        nss = self.nss
        if self.password is None:
            try:
                nss.check_password('')
            except NSSError as e:
                if e.name != 'SEC_ERROR_BAD_PASSWORD':
                    fatal(e) # pragma: no cover
                self.password = getpass.getpass(prompt='Master password: ')
                out()
            else:
                self.password = ''
        try:
            nss.check_password(self.password)
        except NSSError as e:
            fatal(e)
        self.logins = [Login(
            host=login['hostname'],
            username=nss.decrypt(login['encryptedUsername']),
            password=nss.decrypt(login['encryptedPassword']),
        ) for login in self.logins]
        self.build_format()

    @formatter('table', default=True)
    def table(self):
        rows = [attr.astuple(x) for x in self.logins]
        tabulate(rows, headers=['Host', 'Username', 'Password'])

    @formatter('list')
    def list(self):
        for login in self.logins:
            outitem(login.host, [
                ('Username', login.username),
                ('Password', login.password),
            ])

    @formatter('csv')
    def csv(self):
        Feature.csv_from_items(self.logins)
