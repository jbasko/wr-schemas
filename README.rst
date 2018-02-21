*****************************
wr-schemas
*****************************

A schema describes:

 1. a data structure
 2. a mapping of one data structure into another

A schema consists of a list of fields.

A field doesn't have a type -- it is a type itself, in a way. Instead of a type, a field has a bi-directional
mapping. Given two different data structures ``x`` and ``y``, a mapping describes how to calculate ``x.f`` from
``y.f`` and how to calculate ``y.f`` from ``x.f``.

Fields support following attributes:

 * name
 * mapping
 * default
 * source_name (source_names)
 * min_len, max_len, auto_trim
 * min, max
 * choices
 * regex
 * required, forbidden
 * nullable

Also:

 * Nested fields are supported.
 * Fields are easy to clone for reuse.
 * Fields and schemas are easy to reverse.
 * Schemas are easy to chain.

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


Flask:

.. code-block:: python

    from wr_schemas import Field, Schema, Mappings
    from wr_schemas.flask_request import FlaskRequestSchemaMixin

    CreateUser = Schema(
        Field('username', required=True),
        Field('password', required=True),
        mixins=[FlaskRequestSchemaMixin],
    )
    user = CreateUser.from_request()

