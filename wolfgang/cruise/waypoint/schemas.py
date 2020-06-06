# -*- coding: utf-8 -*-
"""
Schema used by REST interface.
"""
from flask_marshmallow import base_fields

from wolfgang.database.schemas import DefaultVersionedSchema
from wolfgang.flask_restplus_plus import DumpModelSchemaMixin
from wolfgang.geo.schemas import BaseGeonameSchema

from .models import Waypoint as WaypointModel


# from wolfgang.user.schemas import BaseUserSchema


class WaypointSchema(DefaultVersionedSchema):
    """
    Exposes all fields for waypoint.
    """

    geoname = base_fields.Nested(BaseGeonameSchema)
    version = base_fields.Integer(required=False)  # TODO: check if needed
    distance_to_go = base_fields.Float()

    class Meta(DefaultVersionedSchema.Meta):  # noqa
        model = WaypointModel

        dump_only = DefaultVersionedSchema.Meta.dump_only + (
            WaypointModel.geoname.key,
            'distance_to_go'
        )
        fields = ()
        load_only = (
            WaypointModel.geoname_id.key,
        )
        exclude = (
            WaypointModel.cruise.key,
            WaypointModel.is_current_version.key,
        )


class DumpWaypointSchema(WaypointSchema, DumpModelSchemaMixin):
    """DumpModelSchemaMixin automatically removes load_only fields."""

    pass
