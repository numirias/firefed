from attr import attrs

from firefed.feature import Feature


@attrs
class Summary(Feature):

    """Create report summary."""

    def run(self):
        features = Feature.__subclasses__()
        features.remove(Summary)
        for Feature_ in features:
            if Feature_.summary:
                continue
            Feature_(self.session, summary=True)()
