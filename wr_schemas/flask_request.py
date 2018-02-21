from .field import Field
from .schema import Schema


class FlaskRequestSchemaMixin:
    def from_request(self, **extras):
        """
        Reads values for fields from Flask request object. Values passed via `extras` take precedence.
        """
        assert isinstance(self, Schema)

        from flask import json, request

        if request.content_type == 'application/json' and request.data:
            request_body = json.loads(request.data)
        else:
            request_body = {}

        content = {}

        for f in self.fields:  # type: Field
            if f.has_value_in(extras):
                f.set_value_in(content, f.load(f.get_value_in(extras)))
            elif f.has_value_in(request.args):
                f.set_value_in(content, f.load(f.get_value_in(request.args)))
            elif f.has_value_in(request_body):
                f.set_value_in(content, f.load(f.get_value_in(request_body)))
            elif f.has_value_in(request.form):
                f.set_value_in(content, f.load(f.get_value_in(request.form)))
            elif f.forbidden:
                continue
            elif f.default is not Field.nothing:
                f.set_value_in(content, f.default)
            elif f.required:
                raise f.Missing(f.name, reason='required')

        if self.instance_factory is None:
            return content
        else:
            return self.instance_factory(**content)
