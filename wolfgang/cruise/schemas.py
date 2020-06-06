# -*- coding: utf-8 -*-
"""
Schema used by REST interface.
"""
from flask_marshmallow import base_fields

from wolfgang.database.schemas import DefaultVersionedSchema
from wolfgang.flask_restplus_plus import DumpModelSchemaMixin, ModelSchema
from wolfgang.user.schemas import BaseProfileSchema, BaseUserSchema
from wolfgang.utils import EnumFieldPlus

from .models import Cruise as CruiseModel
from .models import CruisingArea as CruisingAreaModel
from .models import FuelPrice as FuelPriceModel
from .models import ProfileRole as ProfileRoleModel
from .models import SpecialCondition as SpecialConditionModel
from .yacht.schemas import BaseYachtSchema


class BaseCruiseSchema(DefaultVersionedSchema):
    """
    Base cruise schema exposes only the most general fields.
    """

    # SKIP_VALUES = set([None, []]) # Doesn't work: need a way to skip empty lists?

    status = EnumFieldPlus(CruiseModel.Status)
    yacht = base_fields.Nested(BaseYachtSchema, many=False)
    trip_type = EnumFieldPlus(CruiseModel.TripType, default=None, allow_none=True)
    cruise_areas = base_fields.Nested('CruisingAreaSchema', many=True)
    fuel_price = base_fields.Nested('FuelPriceSchema', many=False)
    special_conditions = base_fields.Nested('SpecialConditionSchema', many=True)

    roles = base_fields.Nested('RoleSchema', many=True)
    creator = base_fields.Nested(BaseUserSchema, many=False)
    brokers = base_fields.Nested(BaseProfileSchema, many=True)
    central_agents = base_fields.Nested(BaseProfileSchema, many=True)
    stakeholders = base_fields.Nested(BaseProfileSchema, many=True)
    captains = base_fields.Nested(BaseProfileSchema, many=True)
    clients = base_fields.Nested(BaseProfileSchema, many=True)
    passengers = base_fields.Nested(BaseProfileSchema, many=True)
    guests = base_fields.Nested(BaseProfileSchema, many=True)

    class Meta(DefaultVersionedSchema.Meta):
        # noqa
        model = CruiseModel

        dump_only = DefaultVersionedSchema.Meta.dump_only + (
            CruiseModel.status.key,
            CruiseModel.yacht.key,
            CruiseModel.creator.key,
            CruiseModel.roles.key,
        )
        # '$role' proxies are dump_only
        for role in CruiseModel.Role:
            dump_only += (CruiseModel.Role.to_proxy_name(role, plural=True),)

        fields = (
            CruiseModel.id.key,
            CruiseModel.version.key,
            CruiseModel.yacht.key,
            CruiseModel.status.key,
            CruiseModel.creator.key,
            'locked',
            'write_access',
        )
        load_only = (
            CruiseModel.yacht_id.key,
        )
        exclude = (
            CruiseModel.approvals.key,
            CruiseModel.waypoints.key,
            CruiseModel.approved_by_users.key,
        )
        # Exclude 'r_$role' relationship from output (use '$role' proxy instead)
        for role in CruiseModel.Role:
            exclude += ('r_' + CruiseModel.Role.to_proxy_name(role, plural=True),)


class DetailedCruiseSchema(BaseCruiseSchema):
    """
    Detailed cruise schema exposes all cruise fields.
    """

    class Meta(BaseCruiseSchema.Meta):
        # noqa
        fields = ()
        exclude = BaseCruiseSchema.Meta.exclude + (CruiseModel.roles.key, )


class DumpDetailedCruiseSchema(DetailedCruiseSchema, DumpModelSchemaMixin):
    """DumpModelSchemaMixin automatically removes load_only fields."""

    pass


class CruisingAreaSchema(ModelSchema):
    """Cruising area schema."""

    area = EnumFieldPlus(CruisingAreaModel.Area)

    class Meta(ModelSchema.Meta):
        # noqa
        model = CruisingAreaModel
        fields = (
            CruisingAreaModel.area.key,
        )


class FuelPriceSchema(DefaultVersionedSchema):
    """Fuel price schema."""

    class Meta(DefaultVersionedSchema.Meta):
        # noqa
        model = FuelPriceModel
        # fields = (
        #     FuelPriceModel.base_price_litre.key,  # For now, we hide quantity
        # )
        exclude = (FuelPriceModel.cruise.key, )


class SpecialConditionSchema(DefaultVersionedSchema):
    """Special condition schema."""

    class Meta(DefaultVersionedSchema.Meta):
        # noqa
        model = SpecialConditionModel
        fields = (
            SpecialConditionModel.name.key,
            SpecialConditionModel.product.key,
            SpecialConditionModel.price.key,
        )


class RoleSchema(DefaultVersionedSchema):
    """Role schema."""

    role = EnumFieldPlus(CruiseModel.Role)
    profile = base_fields.Nested(BaseProfileSchema, many=False)

    class Meta(DefaultVersionedSchema.Meta):
        # noqa
        model = ProfileRoleModel
        fields = (
            ProfileRoleModel.role.key,
            ProfileRoleModel.profile.key,
            ProfileRoleModel.cruise.key,
        )

class RoleStatusSchema(DefaultVersionedSchema):
    """Schema for each role with status (approval etc) info."""

    role = EnumFieldPlus(CruiseModel.Role)
    profile = base_fields.Nested(BaseProfileSchema, many=False)

    class Meta(DefaultVersionedSchema.Meta):
        # noqa
        model = ProfileRoleModel
        fields = (
            ProfileRoleModel.id.key,
            ProfileRoleModel.version.key,
            ProfileRoleModel.role.key,
            ProfileRoleModel.profile.key,
            ProfileRoleModel.cruise_id.key,
            ProfileRoleModel.last_edit_dt.key,
            'current_approval',
            'past_approval',
            'has_signed',
        )
