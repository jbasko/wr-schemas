class AttrDict(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


_nothing = object()
