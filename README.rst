*****************************
wr-schemas
*****************************

.. code-block:: python

    from wr_schemas import Field, Schema, Mappings


    class Fields:
        user_id = Field('id', mapping=int, min=1)
        user_username = Field('username', min_len=5, max_len=100, regex=r'^[a-zA-Z0-9_\-\.@]+$')
        user_password = Field('password', min_len=10, max_len=100, regex=r'^[a-zA-Z0-9]+$')
        user_dob = Field('date_of_birth', mapping=Mappings.date())


    CreateUser = Schema(
        Fields.user_username.clone(required=True),
        Fields.user_password.clone(default=None),
        Fields.user_dob.clone(default=None),
    )

    payload = CreateUser.load({'username': 'marcus.aurelius@rome.gov'})
    assert payload.username == 'marcus.aurelius@rome.gov'
    assert payload.password is None
    assert payload.date_of_birth is None

    print(CreateUser.dump(payload))
