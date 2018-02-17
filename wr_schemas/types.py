import builtins
import datetime as dt


def _date_type(raw_value):
    if isinstance(raw_value, dt.datetime):
        return raw_value
    elif isinstance(raw_value, str):
        return dt.datetime.strptime(raw_value, '%Y-%m-%d')
    else:
        raise ValueError(raw_value)


def _datetime_type(raw_value):
    if isinstance(raw_value, dt.datetime):
        return raw_value
    elif isinstance(raw_value, str):
        return dt.datetime.strptime(raw_value, '%Y-%m-%d %H:%M:%S')
    else:
        raise ValueError(raw_value)


class Types:
    int = builtins.int
    str = builtins.str
    float = builtins.float
    date = _date_type
    datetime = _datetime_type
