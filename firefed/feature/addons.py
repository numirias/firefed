from distutils.version import LooseVersion
from io import StringIO
from urllib.parse import quote
from xml.etree import ElementTree
from attr import attrib, attrs
import requests
from tabulate import tabulate

from firefed.feature import Feature, output_formats, argument
from firefed.output import out, good, bad, okay, fatal


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
UPDATE_CHECK_URL = 'https://versioncheck.addons.mozilla.org/update/VersionCheck.php?reqVersion=2&id={id}&appID=%7bec8030f7-c20a-464f-9b0e-13a3a9e97384%7d&appVersion={app_version}' # noqa

@attrs
class Addon:
    id = attrib()
    name = attrib()
    version = attrib()
    enabled = attrib()
    signed = attrib()
    visible = attrib()

    @property
    def enabled_markup(self):
        return good('enabled') if self.enabled else bad('disabled')

    @property
    def signed_markup(self):
        signed = self.signed
        if signed is None:
            return '(empty)'
        if signed in (v for k, v in SIGNED_STATES.items() if k > 0):
            return good(signed)
        return bad(signed)

    @property
    def visible_tag_markup(self):
        return '' if self.visible else bad('[invisible]')

    @property
    def visible_bool_markup(self):
        return good('true') if self.visible else bad('false')

    def outdated_markup(self, app_version):
        latest = self.get_latest_version(app_version)
        if latest is None:
            return okay('(no version found)')
        if LooseVersion(latest) > LooseVersion(self.version):
            return bad('(outdated, latest: %s)' % latest)
        return good('(up-to-date)')

    def get_latest_version(self, app_version):
        url = UPDATE_CHECK_URL.format(id=quote(self.id),
                                      app_version=quote(app_version))
        update_res = requests.get(url).text
        ns = {k: v for _, (k, v) in ElementTree.iterparse(StringIO(update_res),
                                                          events=['start-ns'])}
        root = ElementTree.fromstring(update_res)
        try:
            return root.find('./RDF:Description/em:version', ns).text
        except AttributeError:
            return None

@argument('-i', '--id', dest='addon_id', help='select specific addon by id')
@argument('-V', '--firefox-version', help='Firefox version for which updates '
          'should be checked')
@argument('-o', '--outdated', action='store_true', dest='check_outdated',
          help='[experimental] check if addons are outdated (queries the '
          'addons.mozilla.org API)')
@output_formats(['table', 'list', 'csv'], default='table')
class Addons(Feature):

    def prepare(self):
        if self.check_outdated:
            if self.format != 'list':
                fatal('--outdated can only be used with list format (--format '
                      'list).')
            if self.firefox_version is None:
                fatal('--outdated needs a version (--firefox-version) to '
                      'check against.')
        addons = list(self.load_addons())
        if self.addon_id:
            addons = [a for a in addons if a.id == self.addon_id]
        return addons

    def load_addons(self):
        # We prefer "extensions.json" over "addons.json"
        addons_json = self.load_json('extensions.json').get('addons', [])
        for addon in addons_json:
            yield Addon(
                id=addon.get('id'),
                name=addon.get('defaultLocale', {}).get('name'),
                version=addon.get('version'),
                enabled=addon.get('active'),
                signed=SIGNED_STATES.get(addon.get('signedState')),
                visible=addon.get('visible'),
            )

    @staticmethod
    def summarize(addons):
        out('%d addons found. (%d enabled)' %
            (len(addons), sum(a.enabled for a in addons)))

    def run(self, addons):
        addons.sort(key=lambda a: not a.enabled)
        self.build_format(addons)

    def build_list(self, addons):
        for addon in addons:
            out('%s (%s) %s %s' % (addon.name, addon.id, addon.enabled_markup,
                                   addon.visible_tag_markup))
            version = addon.version
            if self.check_outdated:
                version += ' ' + addon.outdated_markup(self.firefox_version)
            out('    Version:   %s' % version)
            out('    Signature: %s\n' % addon.signed_markup)

    @staticmethod
    def build_table(addons):
        headers = ['ID', 'Name', 'Version', 'Status', 'Signature', 'Visible']
        rows = [(
            addon.id,
            addon.name,
            addon.version,
            addon.enabled_markup,
            addon.signed_markup,
            addon.visible_bool_markup,
        ) for addon in addons]
        out(tabulate(rows, headers=headers))

    @staticmethod
    def build_csv(addons):
        Feature.csv_from_items(Addon, addons)

# noqa [1]: https://dxr.mozilla.org/mozilla-central/rev/967c95cee709756596860ed2a3e6ac06ea3a053f/toolkit/mozapps/extensions/AddonManager.jsm#3495
