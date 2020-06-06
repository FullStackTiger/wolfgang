# -*- coding: utf-8 -*-
"""
User API endpoints.
"""
from http import HTTPStatus

from flask_jwt_extended import create_access_token, current_user
from sqlalchemy import exc

from wolfgang.api import Resource
from wolfgang.api import user_ns as ns
from wolfgang.database import db

from . import parameters, permissions, schemas
from .models import User as UserModel
from .models import UserProfile as UserProfileModel


def user_loader_callback(id):
    """Callback registered with jwt-extended that auto-loads user object."""
    u = UserModel.get(id)
    if u is None:
        ns.abort(HTTPStatus.UNAUTHORIZED, 'This user no longer exists.')
    return u


@ns.route('/login', methods=['POST'])
class Login(Resource):
    """
    Handles user login.
    """

    # No permission required
    @ns.parameters(parameters.LoginUserParameters())
    @ns.response(code=HTTPStatus.UNAUTHORIZED, description='Wrong email or password')
    def post(self, payload):
        """Returns a token for user."""
        email = payload.get('email')
        password = payload.get('password')
        u = UserModel.get_by(email=email)
        if u and u.is_password_correct(password):
            access_token = create_access_token(identity=u.id)
            return {'access_token': access_token}
        else:
            ns.abort(HTTPStatus.UNAUTHORIZED, 'Wrong email or password')


@ns.route('/me', methods=['GET'])
class UserMe(Resource):
    """Useful pointer to the authenticated user themself."""

    @ns.permission_required(permissions.ActiveUserRolePermission)
    @ns.response(schemas.DetailedUserSchema())
    def get(self):
        """Get current user details."""
        return current_user


@ns.route('/', methods=['GET', 'POST', 'OPTIONS'])
class UserList(Resource):
    """Handles user operations."""

    @ns.permission_required(permissions.AdminRolePermission)
    @ns.response(schemas.BaseUserSchema(many=True))
    def get(self):
        """Shows a list of all users."""
        return UserModel.query.all()

    # No permission required
    @ns.parameters(parameters.AddUserParameters())
    @ns.response(code=HTTPStatus.CONFLICT, description='User email already exists')
    @ns.response(schemas.DumpUserSchema())
    def post(self, payload):
        """Create a new user (with optional first/last name)."""
        try:
            profile = UserProfileModel(first_name=payload.pop('first_name'),
                                       last_name=payload.pop('last_name'), is_main=True)
            u = UserModel(**payload)
            u.profiles.append(profile)
            u.save()
            return u
        except exc.IntegrityError as e:
            db.session().rollback()
            ns.abort(HTTPStatus.CONFLICT, "User email '{}' is already registered".format(payload.get('email')))


@ns.route('/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@ns.param('user_id', 'User identifier', sqla_model=UserModel)
class User(Resource):
    """Single user resource."""

    @ns.permission_required(permissions.ReadAccessPermission, target_id='user_id')
    @ns.response(schemas.DumpDetailedUserSchema())
    def get(self, user):
        """Get user by id."""
        print(current_user)
        print(current_user.id)
        return user

    @ns.permission_required(permissions.WriteAccessPermission, target_id='user_id')
    @ns.response(code=HTTPStatus.NO_CONTENT, description='User deleted')
    def delete(self, user):
        """Delete a user given its id."""
        try:
            user.delete()
        except exc.IntegrityError as e:
            db.session().rollback()
            ns.abort(HTTPStatus.CONFLICT, 'Cannot delete this user, as it is being referenced in existing contracts')
        return '', HTTPStatus.NO_CONTENT

    @ns.permission_required(permissions.WriteAccessPermission, target_id='user_id')
    @ns.parameters(parameters.EditUserParameters())
    @ns.response(schemas.DumpUserSchema())
    @ns.response(code=HTTPStatus.UNAUTHORIZED, description='Wrong password')
    def put(self, payload, user):
        """Update a user's email or password (requires current password)."""
        if not user.is_password_correct(payload.get('current_password')):
            ns.abort(HTTPStatus.UNAUTHORIZED, 'Wrong password')
        try:
            email = payload.get('email')
            if email:
                user.email = email
            new_password = payload.get('new_password')
            if new_password:
                user.set_password(new_password)
            user.save()
        except exc.IntegrityError as e:
            db.session().rollback()
            ns.abort(HTTPStatus.CONFLICT, "User email '{}' is already registered".format(payload.get('email')))

        return user


@ns.route('/<int:user_id>/profile/', methods=['GET', 'POST'])
@ns.param('user_id', 'User identifier', sqla_model=UserModel)
class UserProfileList(Resource):
    """Profile management for user."""

    @ns.permission_required(permissions.ReadAccessPermission, target_id='user_id')
    @ns.response(schemas.DetailedProfileSchema(many=True))
    def get(self, user):
        """Shows a list of profiles for user by user_id."""
        return user.profiles

    @ns.permission_required(permissions.WriteAccessPermission, target_id='user_id')
    @ns.parameters(parameters.AddProfileParameters())
    @ns.response(schemas.DumpDetailedUserSchema())
    # @jwt_required
    def post(self, payload, user):
        """Inserts a profile for user by user_id."""
        profile = UserProfileModel(**payload)
        user.profiles.append(profile)
        user.save()
        return user

@ns.route('/profile/<int:profile_id>/<int:version>', methods=['GET', 'PUT', 'DELETE'])
@ns.route('/profile/<int:profile_id>', defaults={'version': None}, methods=['GET', 'PUT', 'DELETE'])
@ns.param('profile_id', 'The profile identifier', sqla_model=UserProfileModel, sqla_instance_name='profile')
class UserProfile(Resource):
    """Single profile resource for a user."""

    @ns.permission_required(permissions.ReadAccessPermission, target_id=('profile_id', 'version'))
    @ns.response(schemas.DetailedProfileSchema())
    def get(self, profile):
        """Fetch user profile by id."""
        return profile

    @ns.permission_required(permissions.WriteAccessPermission, target_id=('profile_id', 'version'))
    @ns.parameters(parameters.AddProfileParameters())  # Using same input as add profile
    @ns.response(schemas.DetailedProfileSchema())
    def put(self, payload, profile):
        """Update a profile by its id."""
        # TODO: triple-check that payload cannot contain read-only fields
        profile.update(commit=True, **payload)
        return profile

    @ns.permission_required(permissions.WriteAccessPermission, target_id=('profile_id', 'version'))
    # @ns.resolve_arg('profile_id')
    @ns.response(code=HTTPStatus.NO_CONTENT, description='Profile deleted')
    @ns.response(code=HTTPStatus.CONFLICT, description='Cannot delete last profile')
    def delete(self, profile):
        """Delete a user profile given its id."""
        if profile.user_id != current_user.id and not current_user.is_admin:
            ns.abort(HTTPStatus.FORBIDDEN, "Only admins can delete other user's profiles")
        if len(profile.user.profiles) <= 1:
            ns.abort(HTTPStatus.CONFLICT, 'Cannot delete the only remaining profile for this user')
        try:
            profile.delete()
        except exc.IntegrityError as e:
            db.session().rollback()
            ns.abort(HTTPStatus.CONFLICT, 'Cannot delete this profile, as it is being referenced in existing contracts')
        return '', HTTPStatus.NO_CONTENT


@ns.route('/<int:user_id>/contact/', methods=['GET', 'POST'])
@ns.param('user_id', 'User identifier', sqla_model=UserModel)
class UserContactList(Resource):
    """User contacts."""

    @ns.permission_required(permissions.ReadAccessPermission, target_id='user_id')
    @ns.response(schemas.ContactListSchema(many=True))
    def get(self, user):
        """
        List of contact profiles.

        Return list of nested contact profiles (one list for each owner profile).
        """
        return user.profiles

    @ns.permission_required(permissions.WriteAccessPermission, target_id='user_id')
    @ns.parameters(parameters.AddContactParameters())
    @ns.response(schemas.DetailedProfileSchema(many=False))
    def post(self, payload, user):
        """
        Create a new user and adds as contact to current user.

        Return new profile record.
        """
        from_p = UserProfileModel.get(payload.get('from_profile_id', user.main_profile.id), fail_ns=ns)
        email = payload.pop('email')
        contact_user = UserModel.get_by(email=email)
        if contact_user:
            for to_p in contact_user.profiles:
                if to_p in from_p.contacts:
                    return to_p
        else:
            contact_user = UserModel(email=email)
        contact_p = UserProfileModel(profile_name='Created by ' + from_p.full_name,
                                     first_name=payload.pop('first_name', None),
                                     last_name=payload.pop('last_name', None),
                                     main_phone=payload.pop('main_phone', None),
                                     is_main=True)
        contact_user.profiles.append(contact_p)
        contact_user.save()
        from_p.add_contact(contact_p).save()
        return contact_p


@ns.route('/<int:user_id>/profile/<int:profile_id>/contact/<int:contact_profile_id>', methods=['DELETE'])
@ns.param('profile_id', 'User profile id', sqla_model=UserProfileModel, sqla_instance_name='profile')
@ns.param('contact_profile_id', 'Contact profile id')
class ProfileContactDelete(Resource):
    """Delete contact link between two profile IDs."""

    @ns.permission_required(permissions.WriteAccessPermission, target_id='user_id')
    @ns.response(code=HTTPStatus.NO_CONTENT, description='Contact deleted')
    @ns.resolve_arg('profile_id')
    def delete(self, user, profile, contact_profile_id):
        """Delete contact between two profiles."""
        if profile.user_id != user.id:
            ns.abort(HTTPStatus.NOT_FOUND, "Profile id {} doesn't exist for this user".format(profile.id))
        profile.remove_contact(contact_profile_id, fail_ns=ns)
        return '', HTTPStatus.NO_CONTENT

    # @ns.response(code=HTTPStatus.NO_CONTENT, description='Profile deleted')
    # @ns.response(code=HTTPStatus.CONFLICT, description='Cannot delete last profile')
    # def delete(self, user_id, profile_id):
    #     """
    #     Delete a user profile given its id
    #     """
    #     u = UserModel.get(user_id, fail_ns = ns)
    #     p = UserProfileModel.get(profile_id, fail_ns = ns)
    #     if len(u.profiles) <= 1:
    #         ns.abort(HTTPStatus.CONFLICT, 'Cannot delete the only remaining profile for this user')
    #     try:
    #         p.delete_all_versions() #TODO: deal with case where some versions are required by other tables
    #     except exc.IntegrityError as e:
    #         ns.abort(HTTPStatus.CONFLICT,
    #                    'Cannot delete this profile, as it is being referenced in existing contracts')
    #
    #     return 'Profile deleted', HTTPStatus.NO_CONTENT #TODO: check why response code becomes 0
