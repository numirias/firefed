import json
from feature import Feature
from output import good, bad, info
from tabulate import tabulate


class Addons(Feature):

    def run(self, args):
        with open(self.profile_path('extensions.json')) as f:
            addons = json.load(f)['addons']
        info(('%d addons found. (%d active)\n' % (len(addons), sum(addon['active'] for addon in addons))))
        if args.summarize:
            return
        addons.sort(key=lambda x: not x['active'])
        table = []
        for addon in addons:
            name = addon['defaultLocale']['name']
            id_ = addon['id']
            version = addon['version']
            active = good('enabled') if addon['active'] else bad('disabled')
            table.append([name, id_, version, active])
        info(tabulate(table, headers=['Name', 'ID', 'Version', 'Status']))
