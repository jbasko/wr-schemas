from wr_schemas import Field, Schema


def test_wr_schemas():
    class CreateUser(Schema):
        fields = (
            Field('username'),
            Field('password', default=None),
        )

    d = CreateUser().parse_dict({'username': 'admin'})
    assert d.username == 'admin'
    assert d.password is None
