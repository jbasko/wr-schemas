import copy
import re
import sys

from .utils import _nothing, dump_for_mapping


class Field:
    """
    A field is a description of a key-value pair in a payload.
    Field has a :attr:`.name`, a :attr:`.mapping` and a few optional restrictions.
    """

    nothing = _nothing

    class Error(Exception):
        """
        Base class for all Field-specific exceptions.
        """
        def __init__(self, name, reason=None, base_exc_info=None):
            self.name = name
            self.reason = reason
            self.base_exc_info = base_exc_info

        def __str__(self):
            return '{} (reason={})'.format(self.name, self.reason)

    class Invalid(Error):
        """
        Raised when a field value does not meet the restrictions.
        """
        pass

    class Missing(Error):
        """
        Raised when a required field is missing value in the payload.
        """
        pass

    class Forbidden(Error):
        """
        Raised when a field marked as forbidden has a value set in the payload.
        """
        pass

    def __init__(
        self,
        name=None, default=nothing, mapping=nothing, *,
        max_len=None, min_len=None, auto_trim=False,
        min=None, max=None,
        choices=None,
        required=None,
        regex=None,
        source_names=None, source_name=None,
        nullable=True,
        forbidden=None
    ):
        from .mappings import Mapping, none_aware_loader_of, none_aware_dumper_of, primitive_types

        self.name = name

        self._default = default
        if default is self.nothing and mapping is self.nothing:
            mapping = none_aware_loader_of(str)
        elif mapping is self.nothing:
            if default is None:
                mapping = none_aware_loader_of(str)
            else:
                mapping = none_aware_loader_of(type(default))

        if isinstance(mapping, Mapping):
            self.mapping = mapping
        else:
            if mapping in primitive_types:
                self.mapping = Mapping(none_aware_loader_of(mapping), none_aware_dumper_of(mapping))
            else:
                self.mapping = Mapping(mapping, none_aware_dumper_of(str))

        self.max_len = max_len
        self.min_len = min_len
        self.auto_trim = auto_trim
        self.min = min
        self.max = max
        self.choices = choices
        self.required = required
        self.regex = regex
        self.source_names = [source_name] if source_name else source_names
        self.nullable = nullable or (self._default is None)
        self.forbidden = forbidden

    def __str__(self):
        return self.name

    def __call__(self, raw_value):
        return self.load(raw_value)

    def clone(self, reverse=False, **overrides):
        overrides.setdefault('name', self.name)
        overrides.setdefault('mapping', self.mapping)
        overrides.setdefault('default', self.default)
        overrides.setdefault('max_len', self.max_len)
        overrides.setdefault('min_len', self.min_len)
        overrides.setdefault('auto_trim', self.auto_trim)
        overrides.setdefault('min', self.min)
        overrides.setdefault('max', self.max)
        overrides.setdefault('choices', self.choices)
        overrides.setdefault('required', self.required)
        overrides.setdefault('regex', self.regex)
        overrides.setdefault('source_names', self.source_names)
        overrides.setdefault('nullable', self.nullable)
        overrides.setdefault('forbidden', self.forbidden)

        if reverse:
            overrides['mapping'] = self.mapping.reverse()
            overrides['name'] = self.source_names[0] if self.source_names else self.name
            overrides['source_name'] = self.name

        return self.__class__(**overrides)

    def map_as(self, name=None, **extras):
        name = name or self.name
        return self.clone(name=name, source_name=self.name, **extras)

    def reverse(self, **extras):
        return self.clone(reverse=True, **extras)

    @property
    def default(self):
        if self._default is _nothing:
            return self._default
        else:
            return copy.copy(self._default)

    def has_value_in(self, container):
        if self.source_names:
            return any(n in container for n in self.source_names)
        else:
            return self.name in container

    def get_value_in(self, container, default=None):
        if self.source_names:
            for n in self.source_names:
                if n in container:
                    return container[n]
            return default
        else:
            return container.get(self.name, default)

    def set_value_in(self, container, value):
        if self.forbidden:
            raise self.Forbidden(self.name, reason='forbidden')
        container[self.name] = value

    def load(self, raw_value):
        if raw_value is None:
            if self.nullable:
                return raw_value
            else:
                raise self.Invalid(self.name, reason='nullable')

        try:
            value = self.mapping(raw_value)
        except Field.Invalid as invalid:
            raise self.Invalid(
                '{}.{}'.format(self.name, invalid.name),
                reason=invalid.reason,
                base_exc_info=sys.exc_info()
            )
        except Exception:
            raise self.Invalid(self.name, reason='mapping', base_exc_info=sys.exc_info())

        if self.max_len is not None:
            if len(value) > self.max_len:
                if self.auto_trim:
                    value = raw_value[:self.max_len]
                else:
                    raise self.Invalid(self.name, reason='max_len')

        if self.min_len is not None:
            if len(value) < self.min_len:
                raise self.Invalid(self.name, reason='min_len')

        if self.max is not None:
            if value > self.max:
                raise self.Invalid(self.name, reason='max')

        if self.min is not None:
            if value < self.min:
                raise self.Invalid(self.name, reason='min')

        if self.choices is not None:
            if value not in self.choices:
                raise self.Invalid(self.name, reason='choices')

        if self.regex is not None:
            if not isinstance(value, str):
                raise self.Invalid(self.name, reason='regex')
            if not re.match(self.regex, value):
                raise self.Invalid(self.name, reason='regex')

        return value

    def dump(self, value):
        return dump_for_mapping(self.mapping, value)
