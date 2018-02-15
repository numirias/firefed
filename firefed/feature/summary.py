from datetime import datetime

from attr import attrs

from firefed.feature import Feature
from firefed.output import out


@attrs
class Summary(Feature):
    """Summarize results of all (summarizable) features."""

    def creation_date(self):
        data = self.load_json('times.json')
        return datetime.fromtimestamp(data['created'] / 1000)

    def run(self):
        out('Profile created: %s' % self.creation_date())
        features = Feature.__subclasses__()
        features.remove(Summary)
        for Feature_ in features:
            if not Feature_.summarizable():
                continue
            Feature_(self.session, summary=True)()
