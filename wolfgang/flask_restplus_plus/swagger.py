"""
Patched version of flask_restplus customised to handle marshmallow schema.
"""
from apispec.ext.marshmallow.swagger import schema2parameters
from flask_restplus.swagger import Swagger as OriginalSwagger


class Swagger(OriginalSwagger):
    """Customises API class."""

    def parameters_for(self, doc):
        """Overrides parameters_for."""
        schema = doc['params']

        if not schema:
            return []
        if isinstance(schema, list):
            return schema
        if isinstance(schema, dict) and all(isinstance(field, dict) for field in schema.values()):
            return list(schema.values())

        if 'in' in schema.context and 'json' in schema.context['in']:
            default_location = 'body'
            # name = 'json'
            name = None
        else:
            default_location = 'query'
            name = None
        return schema2parameters(schema, default_in=default_location, required=True, name=name)
