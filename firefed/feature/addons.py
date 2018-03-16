from pathlib import Path

from attr import attrib, attrs

from firefed.feature import Feature, arg, formatter
from firefed.output import bad, disabled, good, out, outitem


EXTENSIONS_FILE = 'extensions.json'
STARTUP_FILE = 'addonStartup.json.lz4'
ADDONS_FILE = 'addons.json'
DEFAULT_LOCATION = 'app-profile'
# See constants defined in [1]
SIGNED_STATES = {
    -2: 'broken',
    -1: 'unknown',
    0: 'missing',
    1: 'preliminary',
    2: 'signed',
    3: 'system',
    4: 'privileged'
}


@attrs
class Addon:
    id = attrib()
    name = attrib()
    version = attrib()
    enabled = attrib()
    signed = attrib()
    visible = attrib()
    type = attrib()
    path = attrib()
    location = attrib()

    @property
    def enabled_markup(self):
        return '' if self.enabled else disabled('[disabled]')

    @property
    def signed_markup(self):
        signed = self.signed
        if signed is None:
            return '(empty)'
        if signed in (v for k, v in SIGNED_STATES.items() if k > 0):
            return good(signed)
        return bad(signed)

    @property
    def visible_markup(self):
        return good('true') if self.visible else bad('false')


@attrs
class Addons(Feature):
    """List installed addons/extensions."""

    show_all = arg('-a', '--all', action='store_true',
                   help='show all extensions (including system extensions)')
    show_addons_json = arg('-A', '--show-addons-json', action='store_true',
                           help='show entries from "%s"' % ADDONS_FILE)
    show_startup_json = arg('-S', '--show-startup-json', action='store_true',
                            help='show addon startup entries (from "%s")' %
                            STARTUP_FILE)

    def prepare(self):
        addons = list(self.load_addons())
        if not self.show_all:
            addons = [a for a in addons if a.location == DEFAULT_LOCATION]
        self.addons = addons

    def load_addons(self):
        data = self.load_json(EXTENSIONS_FILE).get('addons', [])
        for addon in data:
            yield Addon(
                id=addon.get('id'),
                name=addon.get('defaultLocale', {}).get('name'),
                version=addon.get('version'),
                enabled=addon.get('active'),
                signed=SIGNED_STATES.get(addon.get('signedState')),
                visible=addon.get('visible'),
                path=addon.get('path'),
                type=addon.get('type'),
                location=addon.get('location'),
            )

    def dump_addons_json(self):
        data = self.load_json(ADDONS_FILE).get('addons', [])
        out('%d entries in "%s":\n' % (len(data), ADDONS_FILE))
        for addon in data:
            out('%s (%s)' % (addon.get('name'), addon.get('id')))

    def dump_startup_json(self):
        data = self.load_json_mozlz4(STARTUP_FILE)
        num = sum(len(x.get('addons', {})) for x in data.values())
        out('%d entries in "%s":\n' % (num, STARTUP_FILE))
        for _, loc_data in data.items():
            for addon in loc_data.get('addons', {}).values():
                path = Path(loc_data['path']) / addon['path']
                out('%s%s' % (path, ' (enabled)' if addon['enabled'] else ''))

    def summarize(self):
        out('%d addons found. (%d enabled)' %
            (len(self.addons), sum(a.enabled for a in self.addons)))

    def run(self):
        if self.show_startup_json:
            self.dump_startup_json()
        elif self.show_addons_json:
            self.dump_addons_json()
        else:
            self.addons.sort(key=lambda a: not a.enabled)
            self.build_format()

    @formatter('list', default=True)
    def list(self):
        for addon in self.addons:
            head = '%s (%s) %s' % (addon.name, addon.id, addon.enabled_markup)
            outitem(head, [
                ('Version', addon.version),
                ('Type', addon.type),
                ('Visible', addon.visible_markup),
                ('Sig', addon.signed_markup),
                ('Path', addon.path),
            ])

    @formatter('short')
    def short(self):
        for addon in self.addons:
            out(addon.id, repr(addon.name))

    @formatter('csv')
    def csv(self):
        Feature.csv_from_items(self.addons)

# noqa [1]: https://dxr.mozilla.org/mozilla-central/rev/967c95cee709756596860ed2a3e6ac06ea3a053f/toolkit/mozapps/extensions/AddonManager.jsm#3495
