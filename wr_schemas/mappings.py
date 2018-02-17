import datetime as dt

from .utils import dump_for_mapping

# primitive types are those that by default are serialized as they are
primitive_types = (int, str, bool, float)


def none_aware_loader_of(value_type):
    def loader(raw_value):
        if raw_value is None:
            return raw_value
        return value_type(raw_value)

    return loader


def none_aware_dumper_of(value_type):
    def dumper(value):
        if value is None:
            return value
        return value_type(value)

    return dumper


class Mapping:
    def __init__(self, loader: callable, dumper: callable=str, **extras):
        self.loader = loader
        self.dumper = dumper
        self.extras = extras

    def reverse(self):
        return self.__class__(self.dumper, self.loader, **self.extras)

    def __getattr__(self, name):
        return self.extras[name]

    def __call__(self, raw_value):
        return self.load(raw_value)

    def load(self, raw_value):
        return self.loader(raw_value)

    def dump(self, value):
        return self.dumper(value)

    def append(self, mapping: 'Mapping'):
        def loader(raw_value):
            return mapping.load(self.load(raw_value))

        def dumper(value):
            return self.dump(mapping.dump(value))

        return Mapping(loader, dumper)

    @classmethod
    def none_aware_for(cls, value_type):
        return cls(none_aware_loader_of(value_type), none_aware_dumper_of(value_type))


def datetime_mapping(*formats, default_format='%Y-%m-%d %H:%M:%S', is_date=False):
    formats = formats if formats else [default_format]

    def loader(raw_value):
        value = -1
        last_exc = None

        if isinstance(raw_value, dt.datetime):
            if is_date:
                return dt.datetime(raw_value.year, raw_value.month, raw_value.day)
            else:
                return raw_value
        elif isinstance(raw_value, dt.date):
            return dt.datetime(raw_value.year, raw_value.month, raw_value.day)

        for f in formats:
            try:
                value = dt.datetime.strptime(raw_value, f)
            except Exception as e:
                last_exc = e

        if value == -1:
            raise last_exc
        else:
            return value

    def dumper(value):
        if value is None:
            return value
        return value.strftime(formats[0])

    return Mapping(loader, dumper)


def date_mapping(*formats, default_format='%Y-%m-%d', is_date=True):
    return datetime_mapping(*formats, default_format=default_format, is_date=is_date)


def list_mapping(item_mapping=str):
    def loader(raw_value):
        return [item_mapping(item) for item in list(raw_value)]

    def dumper(value):
        if value is None:
            return value
        return [dump_for_mapping(item_mapping, item) for item in value]

    return Mapping(loader, dumper)


class Mappings:
    int = Mapping.none_aware_for(int)
    str = Mapping.none_aware_for(str)
    float = Mapping.none_aware_for(float)

    date = date_mapping
    datetime = datetime_mapping
    list = list_mapping
