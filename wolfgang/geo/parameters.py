# encoding: utf-8
"""
Input arguments (Parameters) for Geo resources RESTful API.
"""

from wolfgang.flask_restplus_plus import Parameters

from . import schemas


# from app.extensions.api import abort


class SearchGeonameParameters(Parameters, schemas.GeonameSchema):
    """Cruise creation parameters."""

    def __init__(self, **kwargs):
        """Make all attributes optional."""
        super().__init__(**kwargs)
        for field in self.fields.values():
            field.required = False

    class Meta(schemas.GeonameSchema.Meta):
        pass
