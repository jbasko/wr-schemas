import datetime as dt

from wr_schemas import Field, Mappings, Schema


def test_primitive_fields():
    assert Field('first', mapping=int).dump(5) == 5
    assert Field('first', mapping=int).dump(None) is None

    assert Field('second', mapping=str).dump('6') == '6'
    assert Field('second', mapping=str).dump(None) is None

    assert Field('third', mapping=float).dump(7.8) == 7.8
    assert Field('third', mapping=float).dump(None) is None


def test_date_and_datetime_fields():
    assert Field(
        name='datetime', mapping=Mappings.datetime()
    ).dump(dt.datetime(2018, 12, 31, 16, 55, 33)) == '2018-12-31 16:55:33'

    assert Field(
        name='date', mapping=Mappings.date()
    ).dump(dt.datetime(2018, 12, 31)) == '2018-12-31'

    assert Field(name='date', mapping=Mappings.date()).dump(None) is None
    assert Field(name='date', mapping=Mappings.datetime()).dump(None) is None


def test_primitive_list():
    list_field = Field(name='numbers', mapping=Mappings.list(int))
    assert list_field.dump([1, 2, 3]) == [1, 2, 3]
    assert list_field.dump(None) is None
    assert list_field.dump([]) == []
    assert list_field.dump([None]) == [None]


def test_list_of_dates():
    list_field = Field(name='dates', mapping=Mappings.list(Mappings.date()))
    assert list_field.dump([dt.datetime(2018, 1, 1), dt.datetime(2018, 12, 31, 12, 55)]) == [
        '2018-01-01', '2018-12-31',
    ]
    assert list_field.dump(None) is None
    assert list_field.dump([]) == []
    assert list_field.dump([None]) == [None]


def test_list_of_dicts():
    user = Schema(Field(name='username'), Field(name='password', default=None))
    list_of_users = Field(name='users', mapping=Mappings.list(user))

    obj = [{'username': 'first'}, {'username': 'second', 'password': '222'}]
    assert list_of_users.dump(obj) == obj


def test_list_of_dates_serialization():
    list_of_dates = [dt.datetime(2018, 1, 1), dt.datetime(2018, 2, 1), dt.datetime(2018, 3, 1)]
    mapping = Field(name='dates', mapping=Mappings.list(Mappings.date()))
    assert mapping.dump(list_of_dates) == ['2018-01-01', '2018-02-01', '2018-03-01']
