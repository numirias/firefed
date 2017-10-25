import json
from feature import Feature
from output import good, bad, info
from tabulate import tabulate


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


class Addons(Feature):
    def run(self, args):
        with open(self.profile_path('extensions.json')) as f:
            addons = json.load(f)['addons']
        info('%d addons found. (%d active)\n' %
              (len(addons), sum(addon['active'] for addon in addons)))
        if args.summarize:
            return
        addons.sort(key=lambda x: not x['active'])
        table = []
        for addon in addons:
            name = addon['defaultLocale']['name']
            id_ = addon['id']
            version = addon['version']
            active = good('enabled') if addon['active'] else bad('disabled')
            try:
                signed = signed_state(addon['signedState'])
            except KeyError:
                signed = '(unspecified)'
            visible = good('true') if addon['visible'] else bad('false')
            table.append([name, id_, version, active, signed, visible])
        info(tabulate(table, headers=['Name', 'ID', 'Version', 'Status', 'Signature', 'Visible']))


# [1]: https://dxr.mozilla.org/mozilla-central/rev/967c95cee709756596860ed2a3e6ac06ea3a053f/toolkit/mozapps/extensions/AddonManager.jsm#3495
