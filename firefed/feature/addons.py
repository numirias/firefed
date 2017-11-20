import csv
import sys
import collections
import requests
from xml.etree import ElementTree
from io import StringIO
from urllib.parse import quote
from distutils.version import LooseVersion
from tabulate import tabulate

from firefed.feature import Feature, output_formats, argument
from firefed.output import good, bad, info, error


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


def signed_state(text):
    return good(text) if text in (v for k, v in SIGNED_STATES.items() if k > 0) else bad(text)


Addon = collections.namedtuple('Addon', 'id name version enabled signed visible')


@output_formats(['table', 'list', 'csv'], default='table')
@argument( '-i', '--id', help='select specific addon by id')
@argument( '-V', '--firefox-version', help='Firefox version to check updates against',)
@argument( '-o', '--outdated',  action='store_true',help='[experimental] check if addons are outdated (queries the addons.mozilla.org API)')
class Addons(Feature):

    update_check_url = 'https://versioncheck.addons.mozilla.org/update/VersionCheck.php?reqVersion=2&id={id}&appID=%7bec8030f7-c20a-464f-9b0e-13a3a9e97384%7d&appVersion={app_version}'

    def run(self):
        args = self.args
        if args.outdated and args.format != 'list':
            error('--outdated can only be used with list format (--format list).')
            return
        if args.outdated and args.firefox_version is None:
            error('--outdated needs a version (--firefox-version) to check against.')
            return
        addons = list(self.load_addons())
        if args.id:
            addons = [a for a in addons if a.id == args.id]
        info('%d addons found. (%d enabled)\n' %
             (len(addons), sum(a.enabled for a in addons)))
        if args.summarize:
            return
        addons.sort(key=lambda a: not a.enabled)
        self.build_format(addons)

    def load_addons(self):
        # We prefer "extensions.json" over "addons.json"
        addons_json = self.load_json('extensions.json')['addons']
        for addon in addons_json:
            try:
                signed = addon['signedState']
            except KeyError:
                signed = None
            yield Addon(
                id=addon['id'],
                name=addon['defaultLocale']['name'],
                version=addon['version'],
                enabled=addon['active'],
                signed=None if signed is None else SIGNED_STATES[signed],
                visible=addon['visible'],
            )

    def build_list(self, addons):
        args = self.args
        for addon in addons:
            enabled = good('[enabled]') if addon.enabled else bad('[disabled]')
            signed = signed_state(addon.signed) if addon.signed is not None \
                                                else '(empty)'
            visible = '' if addon.visible else bad('[invisible]')
            info('%s (%s) %s %s' % (addon.name, addon.id, enabled, visible))
            if args.outdated:
                latest = self.check_outdated(addon, self.args.firefox_version)
                if latest is None:
                    outdated_text = '(no version found)'
                else:
                    outdated = LooseVersion(latest) > LooseVersion(addon.version)
                    outdated_text = bad('(outdated, latest: %s)' % latest) if \
                                            outdated else good('(up-to-date)')
                version_text = '%s %s' % (addon.version, outdated_text)
            else:
                version_text = addon.version
            info('    Version:   %s' % version_text)
            info('    Signature: %s' % signed)
            info()

    def build_table(self, addons):
        table = []
        for addon in addons:
            enabled = good('enabled') if addon.enabled else bad('disabled')
            signed = signed_state(addon.signed) if addon.signed is not None \
                                                else '(empty)'
            visible = good('true') if addon.visible else bad('false')
            table.append([addon.name, addon.id, addon.version, enabled, signed,
                          visible])
        info(tabulate(table, headers=['Name', 'ID', 'Version', 'Status',
                                      'Signature', 'Visible']))

    def build_csv(self, addons):
        writer = csv.DictWriter(sys.stdout, fieldnames=Addon._fields)
        writer.writeheader()
        writer.writerows([addon._asdict() for addon in addons])

    def check_outdated(self, addon, app_version):
        url = self.update_check_url.format(
            id=quote(addon.id),
            app_version=quote(app_version),
        )
        update_res = requests.get(url).text
        ns = {node[0]: node[1] for _, node in ElementTree.iterparse(
            StringIO(update_res), events=['start-ns'])}
        root = ElementTree.fromstring(update_res)
        try:
            version = root.find('./RDF:Description/em:version', ns).text
        except AttributeError:
            version = None
        return version


# [1]: https://dxr.mozilla.org/mozilla-central/rev/967c95cee709756596860ed2a3e6ac06ea3a053f/toolkit/mozapps/extensions/AddonManager.jsm#3495
