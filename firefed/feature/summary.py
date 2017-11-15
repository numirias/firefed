from firefed.feature import Feature


class Summary(Feature):

    def run(self):
        args = self.args
        features = Feature.__subclasses__()
        features.remove(Summary)
        for Feature_ in features:
            args.summarize = True
            if not Feature.has_summary:
                continue
            Feature_(self.ff)(args)
