# encoding: utf-8
"""Input arguments (Parameters) for User resources RESTful API."""

from flask_marshmallow import base_fields
from marshmallow import ValidationError, validates_schema

from wolfgang.flask_restplus_plus import ModelSchema, Parameters, JSONParameters

from . import schemas
from .models import UserProfile as UserProfileModel


class LoginUserParameters(Parameters, ModelSchema):
    """User creation parameters."""

    email = base_fields.Email(description='Example: test@gmail.com', required=True)
    password = base_fields.String(description='No rules yet', required=True)


class AddUserParameters(LoginUserParameters):
    """New user creation (sign up) parameters."""

    class Meta:  # noqa
        additional = (UserProfileModel.first_name.key, UserProfileModel.last_name.key)


class EditUserParameters(Parameters, ModelSchema):
    """User modification parameters."""

    current_password = base_fields.String(description='Current password', required=True)
    email = base_fields.Email(description='Example: test@gmail.com', required=False)
    new_password = base_fields.String(description='New password', required=False)

    @validates_schema
    def enforce_email_or_password(self, data):
        """Require either email or password."""
        if not data.get('email') and not data.get('new_password'):
            raise ValidationError('You must provide either a new password or new email')


class AddProfileParameters(JSONParameters, schemas.DetailedProfileSchema):
    """Profile creation parameters."""

    passport_country_iso = base_fields.String(2, description='Country ISO', required=False)
    address_country_iso = base_fields.String(2, description='Country ISO', required=False)
    company_reg_country_iso = base_fields.String(2, description='Country ISO', required=False)
    bank_country_iso = base_fields.String(2, description='Country ISO', required=False)

    class Meta(schemas.DetailedProfileSchema.Meta):
        model = UserProfileModel
        # additional = (UserProfileModel.first_name.key,UserProfileModel.last_name.key)
        # fields = ()
        exclude = schemas.DetailedProfileSchema.Meta.exclude + (UserProfileModel.user.key, )


class ProfileByIdParameters(Parameters):
    """Simple profile id input field."""

    profile_id = base_fields.Integer(description='Existing profile ID', required=True)


class AddContactParameters(AddProfileParameters):
    """From/(optional) To contact edge fields."""

    email = base_fields.Email(description='Example: test@gmail.com', required=True)
    from_profile_id = base_fields.Integer(description='(will use main_profile by default)', required=False)

    class Meta(AddProfileParameters.Meta):
        fields = (
            'email',
            UserProfileModel.first_name.key,
            UserProfileModel.last_name.key,
            UserProfileModel.main_phone.key,
            'from_profile_id',
        )
