from feature import Feature


class Summary(Feature):
    def run(self, args):
        features = Feature.__subclasses__()
        features.remove(Summary)
        for Feature_ in features:
            args.summarize = True
            Feature_(self.ff)(args)
