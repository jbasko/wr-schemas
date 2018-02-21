import datetime as dt

import pytest

from wr_schemas import Field, Mappings, Schema


def test_fields_passed_as_args():
    a = Field('a')
    b = Field('b')
    schema = Schema(a, b)
    assert schema.fields == [a, b]


def test_fields_set_in_class_declaration():
    a = Field('a')
    b = Field('b')

    class s(Schema):
        fields = [a, b]

    assert s.fields == [a, b]


def test_load():
    create_user = Schema(
        Field('username'),
        Field('password', default=None),
    )

    d = create_user.load({'username': 'admin'})
    assert d.username == 'admin'
    assert d.password is None


def test_dump():
    person = Schema(
        Field('weight', mapping=int, source_name='weight_in_kgs'),
    )

    assert person.load({'weight_in_kgs': '60'}) == {'weight': 60}
    assert person.load({'weight_in_kgs': 60}) == {'weight': 60}
    assert person.load({'weight_in_kgs': None}) == {'weight': None}
    assert person.dump({'weight': 60}) == {'weight_in_kgs': 60}
    assert person.dump({'weight': '60'}) == {'weight_in_kgs': 60}
    assert person.dump({'weight': None}) == {'weight_in_kgs': None}


def test_reverse():
    person = Schema(
        Field('name'),
        Field('date_of_birth', source_name='dob', mapping=Mappings.date()),
        Field('weight', mapping=int),
    )

    serialized = {'name': 'A', 'dob': '2000-01-01', 'weight': '60'}
    deserialized = {'name': 'A', 'date_of_birth': dt.datetime(2000, 1, 1), 'weight': 60}

    assert person.load(serialized) == person(serialized) == deserialized

    serializer = person.reverse()
    assert serializer.f.name
    assert serializer.f.dob
    assert serializer.f.weight
    with pytest.raises(AttributeError):
        assert not serializer.f.date_of_birth

    assert serializer(deserialized) == {'name': 'A', 'dob': '2000-01-01', 'weight': 60}

    assert serializer.f.name.dump('A') == 'A'
    assert serializer.f.dob.dump('2000-01-01') == dt.datetime(2000, 1, 1)
    assert serializer.f.weight.dump('60') == 60

    assert serializer.dump(serialized) == deserialized


def test_instance_factory_on_the_fly():
    class Person:
        def __init__(self, name=None, date_of_birth=None):
            self.name = name
            self.date_of_birth = date_of_birth

    person_schema = Schema(Field('name'), Field('date_of_birth', mapping=Mappings.date()), instance_factory=Person)
    person = person_schema.load({'date_of_birth': '1995-10-11'})
    assert isinstance(person, Person)
    assert person.name is None
    assert person.date_of_birth == dt.datetime(1995, 10, 11)
