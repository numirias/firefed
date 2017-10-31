import csv
import sys
import collections
import requests
import xml.etree.ElementTree
from urllib.parse import quote
from distutils.version import LooseVersion
from tabulate import tabulate

from feature import Feature
from output import good, bad, info, error


def signed_state(num):
    # See constants defined in [1]
    states = {
        -2: 'broken',
        -1: 'unknown',
        0: 'missing',
        1: 'preliminary',
        2: 'signed',
        3: 'system',
        4: 'privileged'
    }
    text = states[num]
    return good(text) if num > 0 else bad(text)


Addon = collections.namedtuple('Addon', 'id name version enabled signed visible')


class Addons(Feature):

    api_search_url = 'https://services.addons.mozilla.org/en-US/firefox/api/1.5/search/guid:%s'
    api_addon_url = 'https://services.addons.mozilla.org/en-US/firefox/api/1.5/addon/%d'

    def add_arguments(parser):
        parser.add_argument(
            '-o',
            '--outdated',
            help='check if addons are outdated (queries the addons.mozilla.org API)',
            action='store_true',
        )
        parser.add_argument(
            '-f',
            '--format',
            default='table',
            choices=['table', 'list', 'csv'],
            help='output format',
        )
        parser.add_argument(
            '-i',
            '--id',
            help='select specific addon by id',
        )

    def run(self):
        args = self.args
        if args.outdated and args.format != 'list':
            error('--outdated can only be used with list format (--format list).')
            return
        addons = list(self.load_addons())
        if args.id:
            addons = [a for a in addons if a.id == args.id]
        info('%d addons found. (%d enabled)\n' %
             (len(addons), sum(a.enabled for a in addons)))
        if args.summarize:
            return
        addons.sort(key=lambda a: not a.enabled)
        getattr(self, 'build_%s' % args.format)(addons)

    def load_addons(self):
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
                signed=signed,
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
                outdated, latest = self.check_outdated(addon)
                if latest == 'unknown':
                    outdated_text = '(latest version unknown)'
                else:
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

    def check_outdated(self, addon):
        search_res = requests.get(self.api_search_url % quote(addon.id))
        root = xml.etree.ElementTree.fromstring(search_res.text)
        xml_addon = root.find('addon')
        if xml_addon is None:
            return False, 'unknown'
        amo_id = int(xml_addon.attrib['id'])
        res = requests.get(self.api_addon_url % amo_id)
        root = xml.etree.ElementTree.fromstring(res.text)
        latest_version = root.find('version').text
        outdated = LooseVersion(latest_version) > LooseVersion(addon.version)
        return (outdated, latest_version)


# [1]: https://dxr.mozilla.org/mozilla-central/rev/967c95cee709756596860ed2a3e6ac06ea3a053f/toolkit/mozapps/extensions/AddonManager.jsm#3495
