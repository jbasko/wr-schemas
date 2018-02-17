import argparse

from .utils import AttrDict
from .utils import _nothing as nothing


class Schema:
    """
    A schema is a list of :class:`.Field` whose values need to be retrieved when parsing
    a request according to this schema.
    """

    fields = ()

    def __init__(self, *fields, excluding=None):
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

    def parse_request(self, **extras):
        """
        Reads values for fields from Flask request object. Values passed via `extras` take precedence.
        First, field value is sought in `flask.request.args`, then, if it's an `application/json`
        request with a non-empty body, in JSON-encoded request body.

        The returned object is an :class:`.AttrDict` which allows accessing items as attributes.
        """

        from flask import json, request

        if request.content_type == 'application/json' and request.data:
            request_body = json.loads(request.data)
        else:
            request_body = {}

        content = {}

        for f in self.fields:
            if f.name in extras:
                content[f.name] = f.parse(extras[f.name])
            elif f.name in request.args:
                content[f.name] = f.parse(request.args[f.name])
            elif f.name in request_body:
                content[f.name] = f.parse(request_body[f.name])
            elif f.default is not nothing:
                content[f.name] = f.default
            elif f.required:
                raise f.Missing(f.name)

        return AttrDict(content)

    def parse_dict(self, dct, **extras):
        """
        Similar to :meth:`Schema.parse_request`, but instead the field values are read from
        the given dictionary.
        """

        content = {}

        for f in self.fields:
            if f.name in extras:
                content[f.name] = f.parse(extras[f.name])
            elif f.name in dct:
                content[f.name] = f.parse(dct[f.name])
            elif f.default is not nothing:
                content[f.name] = f.default
            elif f.required:
                raise f.Missing(f.name)

        return AttrDict(content)

    def parse_args(self, args: argparse.Namespace, **extras):
        return self.parse_dict(args.__dict__, **extras)
