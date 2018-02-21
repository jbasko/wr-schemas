from .field import Field
from .utils import AttrDict
from .utils import _nothing as nothing


class Schema:
    """
    A schema is a list of :class:`.Field` whose values need to be retrieved when parsing
    a request according to this schema.
    """

    class FieldsProxy:
        def __init__(self, schema):
            self._schema = schema

        def __getitem__(self, name) -> Field:
            try:
                return getattr(self, name)
            except AttributeError:
                raise KeyError(name)

        def __getattr__(self, name) -> Field:
            for field in self._schema.fields:
                if field.name == name:
                    return field
            raise AttributeError(name)

    instance_factory = AttrDict
    fields = ()

    def __new__(cls, *fields, excluding=None, instance_factory=None, mixins=None):
        if mixins:
            kls = type(
                '{}+{}'.format(cls.__name__, '_'.join(m.__name__ for m in mixins)),
                (cls,) + tuple(mixins),
                {},
            )
            schema_instance = kls()
        else:
            schema_instance = super().__new__(cls)

        schema_instance.instance_factory = instance_factory or cls.instance_factory
        return schema_instance

    def __init__(self, *fields, excluding=None, **kwargs):
        if excluding is None:
            excluding = []
        elif isinstance(excluding, str):
            excluding = [excluding]
        elif isinstance(excluding, (list, tuple)):
            excluding = excluding
        if fields:
            self.fields = [f for f in fields if f.name not in excluding and f not in excluding]
        else:
            self.fields = [f for f in self.fields if f.name not in excluding and f not in excluding]

        self.f = self.FieldsProxy(self)

    def load(self, dct=None, **extras):
        """
        Similar to :meth:`Schema.from_request`, but instead the field values are read from
        the given dictionary.
        """

        content = {}

        for f in self.fields:  # type: Field
            if f.has_value_in(extras):
                f.set_value_in(content, f.load(f.get_value_in(extras)))
            elif f.has_value_in(dct):
                f.set_value_in(content, f.load(f.get_value_in(dct)))
            elif f.forbidden:
                continue
            elif f.default is not nothing:
                f.set_value_in(content, f.default)
            elif f.required:
                raise f.Missing(f.name, reason='required')

        if self.instance_factory is None:
            return content
        else:
            return self.instance_factory(**content)

    def __call__(self, dct=None, **extras):
        return self.load(dct=dct, **extras)

    def dump(self, value):
        if value is None:
            return value

        assert isinstance(value, dict)

        serialized = {}
        for f in self.fields:  # type: Field
            if f.name in value:
                dump_name = f.source_names[0] if f.source_names else f.name
                serialized[dump_name] = f.dump(value[f.name])

        return serialized

    def reverse(self):
        fields = [f.clone(reverse=True) for f in self.fields]
        return self.__class__(*fields)
