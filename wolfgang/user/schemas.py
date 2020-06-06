# -*- coding: utf-8 -*-
"""
Schema used by REST interface.
"""
from flask_marshmallow import base_fields

from wolfgang.database.schemas import DefaultSchema, DefaultVersionedSchema
from wolfgang.flask_restplus_plus import DumpModelSchemaMixin
from wolfgang.geo.schemas import BaseCountrySchema

from .models import User as UserModel
from .models import UserProfile as UserProfileModel


class BaseUserSchema(DefaultSchema):
    """Base user schema exposes only the most general fields."""

    main_profile = base_fields.Nested('BaseProfileSchema', many=False)

    class Meta(DefaultSchema.Meta):  # noqa
        model = UserModel

        fields = (
            UserModel.id.key,
            UserModel.password.key,
            UserModel.email.key,
            UserModel.main_profile.key,
        )
        load_only = (
            UserModel.password.key,
            UserModel.is_admin.key,
            UserModel.is_active.key,
        )
        exclude = (
            UserModel.profiles_versioned.key,
        )


class DumpUserSchema(BaseUserSchema, DumpModelSchemaMixin):
    """DumpModelSchemaMixin automatically removes load_only fields."""

    pass


class DetailedUserSchema(BaseUserSchema):
    """Detailed user schema exposes all useful fields."""

    profiles = base_fields.Nested('DetailedProfileSchema', exclude=(UserProfileModel.user.key,), many=True)

    class Meta(BaseUserSchema.Meta):  # noqa
        fields = ()


class DumpDetailedUserSchema(DetailedUserSchema, DumpModelSchemaMixin):
    """DumpModelSchemaMixin automatically removes load_only fields."""

    pass


class BaseProfileSchema(DefaultVersionedSchema):
    """Base profile schema only exposes the most general fields."""

    user_id = base_fields.Integer()
    passport_country = base_fields.Nested(BaseCountrySchema)
    address_country = base_fields.Nested(BaseCountrySchema)
    company_reg_country = base_fields.Nested(BaseCountrySchema)
    bank_country = base_fields.Nested(BaseCountrySchema)
    initials = base_fields.String()
    full_name = base_fields.String()

    class Meta(DefaultVersionedSchema.Meta):  # noqa
        model = UserProfileModel
        fields = (
            UserProfileModel.id.key,
            UserProfileModel.version.key,
            # UserProfileModel.first_name.key,
            # UserProfileModel.last_name.key,
            UserProfileModel.profile_name.key,
            'full_name',
            'initials',
            UserProfileModel.company_name.key,
            UserProfileModel.passport_country.key,
            UserProfileModel.date_of_birth.key,
        )
        dump_only = DefaultVersionedSchema.Meta.dump_only + (
            UserProfileModel.passport_country.key,
            UserProfileModel.address_country.key,
            UserProfileModel.company_reg_country.key,
            UserProfileModel.bank_country.key,
            'full_name',
            'initials',
        )
        load_only = (
            UserProfileModel.passport_country_iso.key,
            UserProfileModel.address_country_iso.key,
            UserProfileModel.company_reg_country_iso.key,
            UserProfileModel.bank_country_iso.key,
        )
        exclude = (
            UserProfileModel.lower_edges.key,
            UserProfileModel.higher_edges.key,
            UserProfileModel.is_current_version.key,
            UserProfileModel.user.key,  # give user_id instead
        )


class ContactListSchema(BaseProfileSchema, DumpModelSchemaMixin):
    """Nested list of contacts with info about each profile's contacts."""

    from_profile_id = base_fields.Integer(attribute=UserProfileModel.id.key)
    contacts = base_fields.Nested(BaseProfileSchema, only=(UserProfileModel.id.key, 'full_name',), many=True)

    class Meta(BaseProfileSchema.Meta):  # noqa
        fields = ('from_profile_id', 'contacts',)


class DetailedProfileSchema(BaseProfileSchema):
    """Profile schema with every field."""

    class Meta(BaseProfileSchema.Meta):  # noqa
        fields = ()


# class UserSignupFormSchema(Schema):
#
#     recaptcha_server_key = base_fields.String(required=True)
