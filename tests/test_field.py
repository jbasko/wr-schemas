import datetime as dt

import pytest

from wr_schemas import Field, Mappings, Schema
from wr_schemas.mappings import Mapping


def test_initialises_field():
    one = Field('one')
    assert one.name == 'one'
    assert one.mapping('some_string') == 'some_string'
    assert one.mapping('10') == '10'
    assert one.mapping(10) == '10'

    two = Field('two', 5)
    assert two.default == 5
    assert two.mapping(10) == 10
    assert two.mapping('10') == 10
    assert two.mapping(None) is None

    three = Field('three', 'default value')
    assert three.default == 'default value'
    assert three.mapping('10') == '10'
    assert three.mapping(10) == '10'
    assert three.mapping(None) is None

    four = Field('four', None, int)
    assert four.default is None
    assert four.mapping('10') == 10
    assert four.mapping(10) == 10
    assert four.mapping(None) is None


def test_field_is_nullable_by_default():
    assert Field('one').nullable is True
    assert Field('two', nullable=False).nullable is False


def test_field_nullable_is_enforced():
    with pytest.raises(Field.Invalid) as exc_info:
        Field('one', nullable=False).load(None)
    assert exc_info.value.name == 'one'
    assert exc_info.value.reason == 'nullable'


def test_all_field_attributes():
    str_field = Field(
        name='name',
        default='default',
        mapping=str,
        max_len=20,
        min_len=2,
        choices=['one', 'two', 'three'],
        required=False,
        regex=r'^[a-zA-Z]+$',
        source_names=['name', 'Name'],
        forbidden=False,
        nullable=True,
    )
    assert str_field.__dict__ == str_field.clone().__dict__

    int_field = Field(
        name='name',
        required=True,
        mapping=int,
        min=0,
        max=100,
    )
    assert int_field.__dict__ == int_field.clone().__dict__


def test_calling_field_means_invoking_field_loader():
    f = Field(mapping=Mappings.datetime())
    assert f('2017-12-31 23:55:59') == dt.datetime(2017, 12, 31, 23, 55, 59)


def test_field_min_len_max_len():
    f1 = Field(name='name', min_len=3, max_len=8)

    assert f1.load('123') == '123'
    assert f1.load('12345678') == '12345678'

    with pytest.raises(Field.Invalid):
        f1.load('12')

    with pytest.raises(Field.Invalid):
        f1.load('123456789')

    # auto_trim=True
    assert Field(name='name', min_len=3, max_len=8, auto_trim=True).load('123456789') == '12345678'


def test_field_regex():
    f = Field(name='name', regex=r'^[a-z]+$', nullable=True)

    assert f.load('abc') == 'abc'
    assert f.load(None) is None

    with pytest.raises(Field.Invalid):
        f.load('Abc')

    with pytest.raises(Field.Invalid):
        f.load(0)


def test_field_min_max():
    f = Field(name='name', min=1, max=10, mapping=int)

    with pytest.raises(Field.Invalid):
        f.load('-1')

    with pytest.raises(Field.Invalid):
        f.load('11')

    assert f.load(10) == 10
    assert f.load('10') == 10
    assert f.load(1) == 1
    assert f.load('1') == 1


def test_field_in_container():
    f1 = Field(name='f1')

    c1 = {'f1': 'f1_value'}
    c2 = {'f2': 'f2_value'}

    assert f1.has_value_in(c1)
    assert not f1.has_value_in(c2)

    assert f1.get_value_in(c1) == 'f1_value'
    assert f1.get_value_in(c2) is None
    assert f1.get_value_in(c2, 'default') == 'default'

    f1.set_value_in(c2, 'new_value')
    assert c2['f1'] == 'new_value'


def test_field_custom_source_names_in_container():
    f1 = Field(name='f1', source_names=['f1_source'])

    assert not hasattr(f1, 'source_name')
    assert f1.source_names == ['f1_source']

    c1 = {'f1': 'f1_value'}
    c2 = {'f1_source': 'f1_value'}

    assert not f1.has_value_in(c1)
    assert f1.get_value_in(c1) is None

    assert f1.has_value_in(c2)
    assert f1.get_value_in(c2) == 'f1_value'


def test_none_as_default_means_nullable():
    assert Field('name', default=None).nullable


def test_none_as_default_value_means_str_as_parser_by_default():
    f = Field('name', default=None)
    assert f.mapping('10') == '10'
    assert f.mapping([10]) == '[10]'


def test_nested_field():
    person_schema = Schema(
        Field('first_name', default=None),
        Field('last_name', default=None),
    )
    director = Field(name='director', mapping=person_schema, nullable=True)
    assert director.has_value_in({'director': {}})

    assert director.get_value_in({'director': {}}) == {}

    assert director.get_value_in({'director': {'first_name': 'John', 'last_name': 'Smith'}}) == {
        'first_name': 'John',
        'last_name': 'Smith',
    }

    assert Schema(director).load({'director': {}}) == {'director': {'first_name': None, 'last_name': None}}
    assert Schema(director).load({'director': None}) == {'director': None}


def test_primitive_list_field():
    numbers = Field(name='numbers', mapping=Mappings.list(int))
    assert Schema(numbers).load({'numbers': ['1', 2, '3']}) == {'numbers': [1, 2, 3]}


def test_list_of_dicts_field():
    user = Schema(
        Field('username'),
        Field('password', default=None),
    )
    list_of_users = Field(name='users', mapping=Mappings.list(user))

    payload = {
        'users': [
            {'username': 'first'},
            {'username': 'second', 'password': '222'},
            {'username': 'third', 'email': 'third@schem.as'},
        ]
    }

    schema = Schema(list_of_users)
    assert schema.load(payload) == {
        'users': [
            {'username': 'first', 'password': None},
            {'username': 'second', 'password': '222'},
            {'username': 'third', 'password': None},
        ]
    }


def test_forbidden_field():
    user = Schema(
        Field('username'),
        Field('password', forbidden=True),
    )

    user.load({'username': 'user'})

    with pytest.raises(Field.Forbidden):
        user.load({'username': 'user', 'password': 'pass'})


def test_custom_date_and_datetime_formats():
    date_field = Field(name='date', mapping=Mappings.date('%d.%m.%Y.'))
    assert date_field.load('01.03.2018.') == dt.datetime(2018, 3, 1)

    datetime_field = Field(name='datetime', mapping=Mappings.datetime('%d.%m.%Y. %H:%M'))
    assert datetime_field.load('01.03.2018. 12:30') == dt.datetime(2018, 3, 1, 12, 30)

    with pytest.raises(Field.Invalid):
        date_field.load('01/03/2018')

    with pytest.raises(Field.Invalid):
        datetime_field.load('01/03/2018 12:30')

    assert date_field.load(dt.datetime(2018, 1, 1, 12, 55)) == dt.datetime(2018, 1, 1)
    assert date_field.load(dt.date(2018, 1, 1)) == dt.datetime(2018, 1, 1)
    assert datetime_field.load(dt.datetime(2018, 1, 1, 12, 55)) == dt.datetime(2018, 1, 1, 12, 55)
    assert datetime_field.load(dt.date(2018, 1, 1)) == dt.datetime(2018, 1, 1)

    date_field2 = Field(name='date', mapping=Mappings.date('%d/%m/%Y', '%d.%m.%Y.'))
    assert date_field2.load('01.03.2018.') == dt.datetime(2018, 3, 1)
    assert date_field2.load('01/03/2018') == dt.datetime(2018, 3, 1)


def test_reverse_reverses_mapping_and_names():
    f = Field(name='x', mapping=Mapping(int, str), source_name='x_at_source')
    g = f.reverse()
    assert g.mapping.loader == f.mapping.dumper
    assert g.mapping.dumper == f.mapping.loader
    assert g.source_names == ['x']
    assert g.name == 'x_at_source'


def test_clone_accepts_reverse():
    f = Field(name='x', mapping=Mapping(int, str))
    assert f('5') == 5
    assert f.dump('5') == '5'

    g = f.clone(reverse=True)
    assert g(5) == '5'
    assert g.dump('5') == 5


def test_map_as_accepts_reverse():
    f = Field(name='x', mapping=Mapping(int, str))
    g = f.map_as('x_str', reverse=True)
    assert g(5) == '5'
    assert g.dump('5') == 5
