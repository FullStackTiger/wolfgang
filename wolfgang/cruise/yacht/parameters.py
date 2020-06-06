# encoding: utf-8
"""
Input arguments (Parameters) for Yacht resources RESTful API.
"""

from flask_marshmallow import base_fields

from wolfgang.flask_restplus_plus import JSONParameters

from . import schemas


class AddYachtParameters(JSONParameters, schemas.YachtSchema):
    """Yacht creation parameters."""

    port_of_registry_id = base_fields.Integer(description='Geoname ID for port of registry', required=False)
    flag_country_iso = base_fields.String(2, description='Country ISO Code (returned by /geo/countries)',
                                          required=False)

    class Meta(schemas.YachtSchema.Meta):
        # noqa
        pass


class EditYachtParameters(AddYachtParameters):
    """Yacht edition parameters."""

    name = base_fields.String(required=False)

    class Meta(AddYachtParameters.Meta):
        # noqa
        pass
