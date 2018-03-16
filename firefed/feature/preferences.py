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
    """A Preference entry."""
    key = attrib()
    value = attrib()
    info = attrib(default=None)

    def __str__(self):
        return '%s = %s' % (self.key, self.type_to_repr(self.value))

    @staticmethod
    def type_to_repr(val):
        if val is None:
            return 'undefined'
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
    """List user preferences.

    This feature reads the preferences from `prefs.js` and `user.js`.
    Unfortunately, we can't extract any default values since these aren't
    stored in the profile.
    """
    allow_duplicates = \
        arg('-d', '--duplicates', action='store_true', help='show all '
            'preferences, even if the key appears multiple times (otherwise, '
            'only the last occurence is shown because it overrides all '
            'previous occurences)')
    want_check_recommended = \
        arg('-c', '--check', action='store_true', help='compare preferences '
            'with recommended settings')
    recommended_source = \
        arg('-S', '--source', default='userjs-relaxed', metavar='PATH',
            help='path to file with recommended settings (use "userjs-master" '
            'or "userjs-relaxed" to load userjs config from Github)')
    bad_only = \
        arg('-b', '--bad-only', action='store_true', help='when comparing with'
            ' recommendations, show only bad values')
    include_undefined = \
        arg('-i', '--include-undefined', action='store_true', help='when '
            'comparing with recommendations, treat undefined preferences as '
            'bad values')

    def prepare(self):
        self.prefs = list(self.parse_prefs())

    def summarize(self):
        out('%d custom preferences found.' % len(self.prefs))

    def run(self):
        if self.want_check_recommended:
            self.check_recommended()
        elif not self.prefs:
            out('No preferences found.')
        else:
            for pref in self.prefs:
                out(pref)

    def check_recommended(self):
        self.summarize()
        prefs_rec = list(self.parse_userjs(self.recommended_source))
        out('%d recommendeded values read.\n' % len(prefs_rec))
        bad_num = 0
        for pref_rec in prefs_rec:
            try:
                pref = next(p for p in self.prefs if p.key == pref_rec.key)
            except StopIteration:
                if self.include_undefined:
                    # Create a fake preference with an undefined value
                    pref = Preference(pref_rec.key, None)
                else:
                    continue
            if pref_rec.value == pref.value:
                if self.bad_only:
                    continue
                markup = good
            else:
                markup = bad
                bad_num += 1
            rec_text = markup(Preference.type_to_repr(pref_rec.value))
            outitem(pref, [
                ('Should', rec_text),
                ('Reason', pref_rec.info)
            ])
        if bad_num == 0:
            out(good('All preferences seem good.'))
        else:
            out('%d bad values found.' % bad_num)

    def parse_prefs(self):
        prefs = {}
        for pref_file in pref_files:
            try:
                with open(self.profile_path(pref_file), encoding='utf-8') as f:
                    data = f.read()
            except FileNotFoundError:
                data = ''
            matches = re.findall(pref_regex, data)
            for _, key, val in matches:
                # With allow_duplicates we don't actually want unique pref keys
                dict_key = key + val if self.allow_duplicates else key
                prefs[dict_key] = Preference(key, Preference.repr_to_type(val))
        return prefs.values()

    @staticmethod
    def parse_userjs(filename):
        if filename in ['userjs-master', 'userjs-relaxed']:
            branch = filename.split('-')[-1]
            data = requests.get(userjs_url % branch).text
        else:
            with open(filename, encoding='utf-8') as f:
                data = f.read()
        description = None
        for line in data.split('\n'):
            match = re.match(pref_regex, line)
            if match is not None:
                key, val = match[2], Preference.repr_to_type(match[3])
                yield Preference(key, val, info=description)
            elif 'PREF:' in line:
                description = line[9:]
            elif not line:
                description = None
