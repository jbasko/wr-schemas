import datetime as dt

import pytest

from wr_schemas import Field, Mappings, Schema
from wr_schemas.mappings import Mapping


@pytest.mark.parametrize('primitive_type', [str, int, float])
def test_primitive_type_mappings_are_none_aware(primitive_type):
    mapping = getattr(Mappings, primitive_type.__name__)
    assert mapping.load(None) is None
    assert mapping.dump(None) is None

    f = Field(name='f', mapping=mapping)
    assert f.load(None) is None
    assert f.dump(None) is None

    g = Field(name='g', mapping=mapping, nullable=False)
    with pytest.raises(Field.Invalid):
        g.load(None)


def test_chained_mappings():
    create_user = Schema(
        Field('username'),
        Field('password'),
        Field('created_time', source_name='created', mapping=Mappings.datetime()),
    )

    save_user = Schema(
        create_user.f.username.map_as('name'),
        create_user.f.password.map_as('pass'),
        create_user.f.created_time.reverse(),
    )

    input_dict = {'username': 'marcus', 'password': 'meditations', 'created': '2010-01-01 12:00:00'}

    assert save_user(create_user(input_dict)) == {
        'name': 'marcus',
        'pass': 'meditations',
        'created': '2010-01-01 12:00:00',
    }


def test_reversal_of_mappings():
    str_to_date = Mappings.date('%d.%m.%Y')
    assert str_to_date('31.12.2017') == dt.datetime(2017, 12, 31)

    date_to_str = str_to_date.reverse()
    assert date_to_str(dt.datetime(2017, 12, 31, 12, 55)) == '31.12.2017'

    list_of_dates = Mappings.list(Mappings.date('%d.%m.%Y'))
    assert list_of_dates(['01.01.2018', '02.01.2018']) == [dt.datetime(2018, 1, 1), dt.datetime(2018, 1, 2)]

    list_serializer = list_of_dates.reverse()
    assert list_serializer([dt.datetime(2018, 1, 1), dt.datetime(2018, 1, 2)]) == ['01.01.2018', '02.01.2018']


def test_composite_mapping():
    str_to_lower = Mapping(str.lower)
    str_to_int = Mapping(int)
    m = str_to_lower.append(str_to_int)
    assert m('555') == 555
    assert m.dump(555) == '555'

    n = m.reverse()
    assert n(555) == '555'
    assert n.dump('555') == 555
