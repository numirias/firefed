import base64
import json
import ctypes
from ctypes import CDLL, c_char_p, cast, byref, c_void_p, string_at
from feature import feature
from output import info
from tabulate import tabulate


class NSSEntry(ctypes.Structure):
    _fields_ = [('type', ctypes.c_uint), ('data', ctypes.c_void_p),
                ('len', ctypes.c_uint)]


class Logins(feature.Feature):

    def run(self, args):
        self.init_nss()
        with open(self.profile_path('logins.json')) as f:
            login_data = json.load(f)
        logins = login_data['logins']
        info('%d logins found.\n' % len(logins))
        if args.summarize:
            return
        table = []
        for login in logins:
            host = login['hostname']
            username = self.decrypt(login['encryptedUsername'])
            password = self.decrypt(login['encryptedPassword'])
            table.append([host, username, password])
        info(tabulate(table, headers=['Host', 'Username', 'Password']))
        self.nss.NSS_Shutdown()

    def init_nss(self):
        self.nss = CDLL('libnss3.so')
        path = bytes(self.ff.profile_dir, 'utf-8')
        res = self.nss.NSS_Init(path)
        if res != 0:
            raise Exception('NSS initialization failed.')

    def decrypt(self, val):
        raw = base64.b64decode(val)
        self.nss.PK11_GetInternalKeySlot()
        input_ = NSSEntry()
        output = NSSEntry()
        input_.data = cast(c_char_p(raw), c_void_p)
        input_.len = len(raw)
        self.nss.PK11SDR_Decrypt(byref(input_), byref(output), None)
        data = string_at(output.data, output.len)
        return data.decode('utf-8')
