# -*- coding: utf-8 -*-
"""
Default schemas for model and versioned_model classes.
"""
from flask_marshmallow import base_fields

from wolfgang.flask_restplus_plus import ModelSchema


# from .model import Model
# from .versioned_model import VersionedModel


class DefaultSchema(ModelSchema):
    """
    Default schema defines load/dump fields.
    """

    write_access = base_fields.Boolean()

    class Meta(ModelSchema.Meta):
        # noqa
        dump_only = (
            'id',
            'write_access',
            'created_at',
            'updated_at',
        )


class DefaultVersionedSchema(DefaultSchema):
    """
    Default schema for VersionedModel classes.
    """

    locked = base_fields.Boolean()

    class Meta(DefaultSchema.Meta):
        # noqa
        dump_only = DefaultSchema.Meta.dump_only + (
            'version',
            'locked',
            'is_current_version',
        )
