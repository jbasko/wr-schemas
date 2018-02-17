import copy
import re
import sys

from .types import Types
from .utils import _nothing


class Field:
    """
    A field is a description of a key-value pair in a payload.
    Field has a :attr:`.name`, a :attr:`.type` and a few optional restrictions.
    """

    nothing = _nothing

    class Error(Exception):
        """
        Base class for all Field-specific exceptions.
        """
        def __init__(self, name, base_exc_info=None):
            self.name = name
            self.base_exc_info = base_exc_info

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

    def __init__(
        self,
        name=None, type=Types.str, default=nothing, *,
        max_len=None, min_len=None, min=None, max=None, choices=None,
        required=None, regex=None,
    ):
        self.name = name
        self.type = type
        self._default = default
        self.max_len = max_len
        self.min_len = min_len
        self.min = min
        self.max = max
        self.choices = choices
        self.required = required
        self.regex = regex

    def clone(self, **overrides):
        overrides.setdefault('name', self.name)
        overrides.setdefault('type', self.type)
        overrides.setdefault('default', self.default)
        overrides.setdefault('max_len', self.max_len)
        overrides.setdefault('min_len', self.min_len)
        overrides.setdefault('min', self.min)
        overrides.setdefault('max', self.max)
        overrides.setdefault('choices', self.choices)
        overrides.setdefault('required', self.required)
        overrides.setdefault('regex', self.regex)
        return self.__class__(**overrides)

    @property
    def default(self):
        if self._default is _nothing:
            return self._default
        else:
            return copy.copy(self._default)

    def parse(self, raw_value):
        try:
            value = self.type(raw_value)
        except Exception:
            raise self.Invalid(self.name, base_exc_info=sys.exc_info())

        if self.max_len is not None:
            value = value[:self.max_len]

        if self.min_len is not None:
            if len(value) < self.min_len:
                raise self.Invalid(self.name)

        if self.max is not None:
            if value > self.max:
                raise self.Invalid(self.name)

        if self.min is not None:
            if value < self.min:
                raise self.Invalid(self.name)

        if self.choices is not None:
            if value not in self.choices:
                raise self.Invalid(self.name)

        if self.regex is not None:
            if not isinstance(value, str):
                raise self.Invalid(self.name)
            if not re.match(self.regex, value):
                raise self.Invalid(self.name)

        return value
