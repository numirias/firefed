from attr import attrs

from firefed.feature import Feature


@attrs
class Summary(Feature):
    """Summarize results of all features (that can be summarized)."""

    def run(self):
        features = Feature.__subclasses__()
        features.remove(Summary)
        for Feature_ in features:
            if not Feature_.summarizable():
                continue
            Feature_(self.session, summary=True)()
