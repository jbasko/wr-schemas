class AttrDict(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


_nothing = object()


def dump_for_mapping(mapping, value):
    if mapping in (int, str, bool, float):
        return value

    serializer = getattr(mapping, 'dump', str)
    return serializer(value)
