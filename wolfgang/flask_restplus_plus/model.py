"""
Patched version of flask_restplus customised to handle marshmallow schema.
"""
import flask_marshmallow
from apispec.ext.marshmallow.swagger import field2property, fields2jsonschema
from flask_restplus.model import Model as OriginalModel
from werkzeug import cached_property


class SchemaMixin(object):
    """SchemaMixin."""

    def __deepcopy__(self, memo):
        """Flask-RESTplus does unnecessary data copying, but marshmallow.Schema doesn't support deepcopying."""
        return self


class Schema(SchemaMixin, flask_marshmallow.Schema):
    """Base Schema class."""

    pass


if flask_marshmallow.has_sqla:
    class ModelSchema(SchemaMixin, flask_marshmallow.sqla.ModelSchema):
        """Base Marshmallow Schema class."""

        pass


class DumpModelSchemaMixin(ModelSchema):
    """Mixin that removes load_only fields."""

    def __init__(self, *args, **kwargs):
        """Remove load_only fields from schema."""
        super(ModelSchema, self).__init__(*args, **kwargs)
        self.fields = {k: v for (k, v) in self.fields.items() if not v.load_only}


class DefaultHTTPErrorSchema(Schema):
    """Schema for errror code."""

    status = flask_marshmallow.base_fields.Integer()
    message = flask_marshmallow.base_fields.String()

    def __init__(self, http_code, **kwargs):
        """Return HTTP-Code-based error."""
        super(DefaultHTTPErrorSchema, self).__init__(**kwargs)
        self.fields['status'].default = http_code


class Model(OriginalModel):
    """Customised Model."""

    def __init__(self, name, model, **kwargs):
        """Wrapping with __schema__ is not a very elegant solution."""
        super(Model, self).__init__(name, {'__schema__': model}, **kwargs)

    @cached_property
    def __schema__(self):
        """Retrieving custom __schema__."""
        schema = self['__schema__']
        if isinstance(schema, flask_marshmallow.Schema):
            return fields2jsonschema(schema.fields)
        elif isinstance(schema, flask_marshmallow.base_fields.FieldABC):
            return field2property(schema)
        raise NotImplementedError()
