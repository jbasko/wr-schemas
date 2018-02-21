import datetime as dt

import pytest
from flask import Flask, json

from wr_schemas import Field, Mappings, Schema
from wr_schemas.flask_request import FlaskRequestSchemaMixin


class UserSchema(Schema, FlaskRequestSchemaMixin):
    fields = (
        Field('username', required=True),
        Field('password', source_name='Password'),
        Field('dob', mapping=Mappings.date(), default=None)
    )


@pytest.fixture
def flask_app():
    return Flask(__name__)


def test_request_args(flask_app):
    with flask_app.test_request_context(query_string='username=user&Password=pass&dob=1994-07-29'):
        user = UserSchema().from_request()
        assert user.username == 'user'
        assert user.password == 'pass'
        assert user.dob == dt.datetime(1994, 7, 29)

    with flask_app.test_request_context(query_string='username=user'):
        user = UserSchema().from_request()
        assert user.username == 'user'
        assert 'password' not in user
        assert user.dob is None

    with flask_app.test_request_context(query_string='Password=pass'):
        with pytest.raises(Field.Missing) as exc_info:
            UserSchema().from_request()
        assert exc_info.value.name == 'username'
        assert exc_info.value.reason == 'required'


def test_request_form(flask_app):
    request = dict(method='POST', data={'username': 'user', 'Password': 'pass', 'dob': '1994-07-29'})
    with flask_app.test_request_context(**request):
        user = UserSchema().from_request()
        assert user.username == 'user'
        assert user.password == 'pass'
        assert user.dob == dt.datetime(1994, 7, 29)


def test_request_json_body(flask_app):
    request = dict(method='PUT', content_type='application/json', data=json.dumps({
        'username': 'user', 'Password': 'pass', 'dob': '1994-07-29',
    }))
    with flask_app.test_request_context(**request):
        user = UserSchema().from_request()
        assert user.username == 'user'
        assert user.password == 'pass'
        assert user.dob == dt.datetime(1994, 7, 29)


def test_request_args_override_request_body(flask_app):
    request = dict(
        method='POST',
        query_string='username=user&Password=RealPassword',
        content_type='application/json',
        data=json.dumps({
            'Password': 'pass',
            'dob': '1995-11-10',
        })
    )
    with flask_app.test_request_context(**request):
        user = UserSchema().from_request()
        assert user.username == 'user'
        assert user.password == 'RealPassword'
        assert user.dob == dt.datetime(1995, 11, 10)


def test_request_args_override_request_form(flask_app):
    request = dict(
        method='POST',
        query_string='username=user&Password=RealPassword',
        data={
            'Password': 'pass',
            'dob': '1995-11-10',
        }
    )
    with flask_app.test_request_context(**request):
        user = UserSchema().from_request()
        assert user.username == 'user'
        assert user.password == 'RealPassword'
        assert user.dob == dt.datetime(1995, 11, 10)


def test_request_extras_override_request_args(flask_app):
    with flask_app.test_request_context(query_string='username=user&Password=pass'):
        user = UserSchema().from_request(dob='1995-11-10', Password='RealPassword')
        assert user.username == 'user'
        assert user.password == 'RealPassword'
        assert user.dob == dt.datetime(1995, 11, 10)


def test_schema_instance_on_the_fly():
    schema = Schema(Field('username'), Field('password'), mixins=[FlaskRequestSchemaMixin])
    assert isinstance(schema, Schema)
    assert isinstance(schema, FlaskRequestSchemaMixin)
    assert schema.f.username
    assert schema.f.password
