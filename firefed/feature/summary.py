from firefed.feature import Feature


class Summary(Feature):

    def run(self):
        features = Feature.__subclasses__()
        features.remove(Summary)
        for Feature_ in features:
            if not hasattr(Feature_, 'summarize'):
                continue
            Feature_(self.session, summary=True)()
