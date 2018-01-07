import re

from attr import attrib, attrs
import requests

from firefed.feature import Feature, arg
from firefed.output import bad, good, out

pref_regex = r'\s*user_pref\((["\'])(.+?)\1,\s*(.+?)\);'
userjs_url = 'https://raw.githubusercontent.com/pyllyukko/user.js/%s/user.js'


@attrs
class Preference:

    key = attrib()
    value = attrib()
    info = attrib(default=None)

    def __str__(self):
        return '%s = %s' % (self.key, self.type_to_repr(self.value))

    @staticmethod
    def type_to_repr(val):
        if isinstance(val, str):
            return '"%s"' % val
        if isinstance(val, bool):
            return repr(val).lower()
        return str(val)

    @staticmethod
    def repr_to_type(val):
        if val in ['true', 'false']:
            return val == 'true'
        try:
            return int(val)
        except ValueError:
            # Value will be a string, so just cut the surrounding quotes
            return val[1:-1]


@attrs
class Preferences(Feature):
    """Extract user preferences. (This doesn't include defaults.)"""

    recommended = arg('-r', '--recommended', default='userjs-relaxed', help='path to \
    user.js file with recommended settings (use "userjs-master" or \
    "userjs-relaxed" to load userjs config from Github)')
    check = arg('-c', '--check', action='store_true', help='check preferences for \
    dubious settings')

    def prepare(self):
        self.prefs = list(self.parse_prefs())

    def summarize(self):
        out('%d custom preferences found.' % len(self.prefs))

    def run(self):
        if not self.check:
            for pref in self.prefs:
                out(pref)
            return
        prefs_rec = list(self.parse_userjs(self.recommended))
        for pref in self.prefs:
            try:
                pref_rec = next((p for p in prefs_rec if p.key == pref.key))
            except StopIteration:
                continue
            markup = good if pref_rec.value == pref.value else bad
            rec_text = markup(Preference.type_to_repr(pref_rec.value))
            out(pref)
            out('    Recommended: %s' % rec_text)
            out('    Reason: %s' % pref_rec.info)
            out()

    def parse_prefs(self):
        with open(self.profile_path('prefs.js')) as f:
            data = f.read()
        matches = re.findall(pref_regex, data)
        for _, key, value in matches:
            yield Preference(key, Preference.repr_to_type(value))

    @staticmethod
    def parse_userjs(filename):
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
