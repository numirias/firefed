from attr import attrs

from firefed.feature import Feature


@attrs
class Summary(Feature):

    def summarize(self):
        pass

    def run(self):
        features = Feature.__subclasses__()
        features.remove(Summary)
        for Feature_ in features:
            if not hasattr(Feature_, 'summarize'):
                print('hey')
                continue
            Feature_(self.session, summary=True)()
