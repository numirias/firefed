import re
import requests
from collections import defaultdict
from tabulate import tabulate

from firefed.feature import Feature
from firefed.output import info, good, bad


pref_regex = r'\s*user_pref\((["\'])(.+?)\1,\s*(.+?)\);'
userjs_url = 'https://raw.githubusercontent.com/pyllyukko/user.js/%s/user.js'


class Preference:

    def __init__(self, key, value, info=None):
        self.key = key
        self.value = value
        self.info = info

    def __str__(self):
        return '%s = %s' % (self.key, self.type_to_repr(self.value))

    @staticmethod
    def type_to_repr(val):
        if type(val) == str:
            return '"%s"' % val
        elif type(val) == bool:
            return repr(val).lower()
        return str(val)

    @staticmethod
    def repr_to_type(val):
        if val in ['true', 'false']:
            return True if val == 'true' else False
        else:
            try:
                return int(val)
            except ValueError:
                # Must be a string
                return val[1:-1]


class Preferences(Feature):

    def add_arguments(parser):
        parser.add_argument(
            '-r',
            '--recommended',
            default='userjs-relaxed',
            help='path to user.js file with recommended settings (use "userjs-master" or "userjs-relaxed" to load userjs config from Github)',
        )
        parser.add_argument(
            '-c',
            '--check',
            help='check preferences for dubious settings',
            action='store_true',
        )

    def run(self):
        prefs = list(self.parse_prefs())
        info('%d custom preferences found.\n' % len(prefs))
        if self.args.summarize:
            return
        if not self.args.check:
            for pref in prefs:
                info(pref)
            return
        prefs_rec = list(self.parse_userjs(self.args.recommended))
        for pref in prefs:
            try:
                pref_rec = next((p for p in prefs_rec if p.key == pref.key))
            except StopIteration:
                continue
            markup = good if pref_rec.value == pref.value else bad
            rec_text = markup(Preference.type_to_repr(pref_rec.value))
            info(pref)
            info('    Recommended: %s' % rec_text)
            info('    Reason: %s' % pref_rec.info)
            info()

    def parse_prefs(self):
        with open(self.profile_path('prefs.js')) as f:
            data = f.read()
        matches = re.findall(pref_regex, data)
        for match in matches:
            yield Preference(match[1], Preference.repr_to_type(match[2]))

    def parse_userjs(self, filename):
        if filename in ['userjs-master', 'userjs-relaxed']:
            branch = 'relaxed' if filename == 'userjs-relaxed' else 'master'
            data = requests.get(userjs_url % branch).text
        else:
            with open(filename) as f:
                data = f.read()
        description = None
        for line in data.split('\n'):
            match = re.match(pref_regex, line)
            if match is not None:
                key, val = match[2], Preference.repr_to_type(match[3])
                yield Preference(key, val, info=description)
            elif 'PREF:' in line:
                description = line[9:]
