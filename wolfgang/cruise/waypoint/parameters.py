# encoding: utf-8
"""
Input arguments (Parameters) for Yacht resources RESTful API.
"""

from flask_marshmallow import base_fields

from wolfgang.flask_restplus_plus import JSONParameters

from . import schemas


class WaypointParameters(JSONParameters, schemas.WaypointSchema):
    """Waypoint creation parameters."""

    geoname_id = base_fields.Integer(description='Geoname ID for waypoint', required=False)
    selected_wp_id = base_fields.Integer(description='WP currently selected', required=False)

    # @ma.post_load
    # def make_instance(self, data):
    #     """Deserialize data to an instance of the model. Update an existing row
    #     if specified in `self.instance` or loaded by primary key(s) in the data;
    #     else create a new row.
    #
    #     :param data: Data to deserialize.
    #     """
    #     instance = self.instance or self.get_instance(data)
    #     if instance is not None:
    #         for key, value in iteritems(data):
    #             setattr(instance, key, value)
    #         return instance
    #     return self.opts.model(**data)

    class Meta(schemas.WaypointSchema.Meta):  # noqa
        pass


class EditWaypointParameters(WaypointParameters):
    """Waypoint update parameters: all fields optional."""

    latitude = base_fields.Float(required=False)
    longitude = base_fields.Float(required=False)
    arr_date = base_fields.DateTime(required=False)

    class Meta(WaypointParameters.Meta):  # noqa
        exclude = WaypointParameters.Meta.exclude + ('selected_wp_id',)
