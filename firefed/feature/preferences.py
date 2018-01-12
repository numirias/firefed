import re

from attr import attrib, attrs
import requests

from firefed.feature import Feature, arg
from firefed.output import bad, good, out, outitem

pref_regex = r'\s*user_pref\((["\'])(.+?)\1,\s*(.+?)\);'
userjs_url = 'https://raw.githubusercontent.com/pyllyukko/user.js/%s/user.js'
pref_files = ['prefs.js', 'user.js']


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
    """Extract user preferences. (This doesn't include defaults.)

    This feature reads the preferences from "prefs.js" and "user.js".
    """

    recommended_source = \
        arg('-r', '--recommended', default='userjs-relaxed', help='path to '
            'user.js file with recommended settings (use "userjs-master" or '
            '"userjs-relaxed" to load userjs config from Github)')
    check_recommended = \
        arg('-c', '--check', action='store_true', help='check preferences for '
            'dubious settings')
    # TODO No-override

    def prepare(self):
        self.prefs = list(self.parse_prefs())

    def summarize(self):
        out('%d custom preferences found.' % len(self.prefs))

    def run(self):
        if not self.check_recommended:
            if not self.prefs:
                out('No preferences found.')
                return
            for pref in self.prefs:
                out(pref)
            return
        self.summarize()
        prefs_rec = list(self.parse_userjs(self.recommended_source))
        out('%d recommendeded values read.\n' % len(prefs_rec))
        bad_num = 0
        for pref in self.prefs:
            try:
                pref_rec = next((p for p in prefs_rec if p.key == pref.key))
            except StopIteration:
                continue
            if pref_rec.value == pref.value:
                markup = good
            else:
                markup = bad
                bad_num += 1
            rec_text = markup(Preference.type_to_repr(pref_rec.value))
            outitem(pref, [
                ('Recommended', rec_text),
                ('Reason', pref_rec.info)
            ])
        if bad_num == 0:
            out(good('All preferences seem good.'))
        else:
            out('%d bad values found.' % bad_num)

    def parse_prefs(self):
        pref_dict = {}
        for pref_file in pref_files:
            try:
                with open(self.profile_path(pref_file)) as f:
                    data = f.read()
            except FileNotFoundError:
                data = ''
            # TODO Handle no preferences set
            matches = re.findall(pref_regex, data)
            for _, key, val in matches:
                pref_dict[key] = Preference(key, Preference.repr_to_type(val))
        return pref_dict.values()

    @staticmethod
    def parse_userjs(filename):
        if filename in ['userjs-master', 'userjs-relaxed']:
            branch = filename.split('-')[-1]
            data = requests.get(userjs_url % branch).text
        else:
            with open(filename) as f:
                data = f.read()
        description = None
        for line in data.split('\n'):
            match = re.match(pref_regex, line) # TODO findall?
            if match is not None:
                key, val = match[2], Preference.repr_to_type(match[3])
                yield Preference(key, val, info=description)
            elif 'PREF:' in line:
                description = line[9:]
            elif not line:
                description = None
