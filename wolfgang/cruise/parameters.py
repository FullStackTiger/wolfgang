# encoding: utf-8
"""
Input arguments (Parameters) for Cruise resources RESTful API.
"""

from flask_marshmallow import base_fields

from wolfgang.flask_restplus_plus import JSONParameters

from . import schemas


class AddCruiseParameters(JSONParameters, schemas.DetailedCruiseSchema):
    """Cruise creation parameters."""

    yacht_id = base_fields.Integer(description='Existing Boad ID', required=False)

    # first_name = base_fields.String(description="", required=False)
    # password = base_fields.String(description="", required=False)
    class Meta(schemas.DetailedCruiseSchema.Meta):  # noqa
        pass


class AddApprovalParameters(JSONParameters):
    """Approval creation parameters."""

    user_id = base_fields.Integer(description='Approving User ID', required=True)


class UnlockParameters(JSONParameters):
    """Cruise unlock parameters."""

    user_id = base_fields.Integer(description='Unlocking User ID', required=True)
