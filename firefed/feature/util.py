from feature import Feature


def feature_map():
    return {
        module.__name__.lower(): module
        for module in Feature.__subclasses__()
    }
