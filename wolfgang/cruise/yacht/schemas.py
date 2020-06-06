# -*- coding: utf-8 -*-
"""
Schema used by REST interface.
"""
from flask_marshmallow import base_fields

from wolfgang.database.schemas import DefaultVersionedSchema
from wolfgang.flask_restplus_plus import DumpModelSchemaMixin
from wolfgang.geo.schemas import BaseCountrySchema, BaseGeonameSchema
from wolfgang.user.schemas import BaseUserSchema
from wolfgang.utils import EnumFieldPlus

from .models import Yacht as YachtModel, YachtPicture as YachtPictureModel


class BaseYachtSchema(DefaultVersionedSchema):
    """
    Base Yacht schema exposes only the most general fields.
    """

    port_of_registry = base_fields.Nested(BaseGeonameSchema)
    creator = base_fields.Nested(BaseUserSchema)
    type = EnumFieldPlus(YachtModel.Type)
    flag = base_fields.Nested(BaseCountrySchema)
    pictures = base_fields.Nested('YachtPictureSchema', many=True)

    class Meta(DefaultVersionedSchema.Meta):
        # noqa
        model = YachtModel

        dump_only = DefaultVersionedSchema.Meta.dump_only + (
            YachtModel.creator.key,
            YachtModel.flag.key,
            YachtModel.port_of_registry.key,
            YachtModel.pictures.key,
        )
        fields = (
            YachtModel.id.key,
            YachtModel.version.key,
            YachtModel.name.key,
        )
        load_only = (
            YachtModel.port_of_registry_id.key,
            YachtModel.flag_country_iso.key,
        )
        exclude = (
            YachtModel.creator_id.key,
        )


class YachtPictureSchema(DefaultVersionedSchema):
    """
    Exposes important info for yacht picture.
    """

    type = EnumFieldPlus(YachtPictureModel.Type)

    class Meta(DefaultVersionedSchema.Meta):
        # noqa
        model = YachtPictureModel
        fields = ('public_url', )

class DumpBaseYachtSchema(BaseYachtSchema, DumpModelSchemaMixin):
    """DumpModelSchemaMixin automatically removes load_only fields."""

    pass


class YachtSchema(BaseYachtSchema):
    """Full yacht schema."""

    class Meta(BaseYachtSchema.Meta):
        # noqa
        fields = ()


class DumpYachtSchema(YachtSchema, DumpModelSchemaMixin):
    """DumpModelSchemaMixin automatically removes load_only fields."""

    pass
