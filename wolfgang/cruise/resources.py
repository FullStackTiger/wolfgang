# -*- coding: utf-8 -*-
"""Cruise resources."""
from http import HTTPStatus

from flask_jwt_extended import current_user
from sqlalchemy import exc, or_, and_

import wolfgang.user.parameters as userParameters
import wolfgang.user.schemas as userSchemas
from wolfgang.api import Resource
from wolfgang.api import cruise_ns as ns
from wolfgang.database import db
from wolfgang.user import permissions
from wolfgang.user.models import User as UserModel
from wolfgang.user.models import UserProfile as UserProfileModel

from . import parameters, schemas
from .models import Cruise as CruiseModel
from .models import ProfileRole as ProfileRoleModel
from .models import UserCruiseApproval as UserCruiseApprovalModel
from .waypoint.resources import ns as waypoint_ns  # noqa - Ensure file is loaded and endpoint added
from .yacht.models import Yacht as YachtModel

# DEBUG SQL queries:
# import logging
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

@ns.route('/', methods=['GET'])
class CruiseList(Resource):
    """Cruise Admin operations."""

    @ns.permission_required(permissions.AdminRolePermission)
    @ns.response(schemas.BaseCruiseSchema(many=True))
    def get(self):
        """
        List all cruises.

        Mainly for debug purposes (see /cruise/by_user/)
        """
        cruises = CruiseModel.query.all()
        return cruises


@ns.route('/by_user/<int:user_id>/', methods=['GET', 'POST'])
@ns.param('user_id', 'User ID', sqla_model=UserModel)
class UserCruiseList(Resource):
    """User-specific cruise operations."""

    @ns.permission_required(permissions.ReadAccessPermission, target_id='user_id')
    @ns.response(schemas.BaseCruiseSchema(many=True))
    def get(self, user):
        """List cruises accessible to user."""
        cruises = CruiseModel.query.outerjoin(ProfileRoleModel).outerjoin(UserProfileModel).filter(
            and_(CruiseModel.is_current_version == True,
                or_(CruiseModel.creator_id == user.id, UserProfileModel.user_id == user.id))
        ).all()
        return cruises

    @ns.permission_required(permissions.WriteAccessPermission, target_id='user_id')
    @ns.parameters(parameters.AddCruiseParameters())
    @ns.response(schemas.DumpDetailedCruiseSchema())
    def post(self, payload, user):
        """
        Create a new cruise.

        Automatically assigns user as creator
        """
        if user.main_profile is None:
            ns.abort(HTTPStatus.CONFLICT,
                     'User id {} does not have a profile to associate with cruise.'.format(user.id))
        if 'yacht_id' in payload:
            payload['yacht'] = YachtModel.get(id=payload.pop('yacht_id'),
                                              version=payload.pop('yacht_version', None),
                                              fail_ns=ns)
        try:
            c = CruiseModel(creator=user, **payload)
            c.save()
        except exc.IntegrityError as e:
            db.session().rollback()
            ns.abort(HTTPStatus.CONFLICT,
                     'Database Error: Could not create cruise')
        return c


@ns.route('/<int:cruise_id>', methods=['GET', 'PUT', 'DELETE'])
@ns.param('cruise_id', 'Cruise ID', sqla_model=CruiseModel)
class Cruise(Resource):
    """Single Cruise resource."""

    @ns.permission_required(permissions.ReadAccessPermission, target_id='cruise_id')
    @ns.response(schemas.DumpDetailedCruiseSchema())
    def get(self, cruise):
        """Fetch cruise record."""
        return cruise

    @ns.permission_required(permissions.WriteAccessPermission, target_id='cruise_id')
    @ns.parameters(parameters.AddCruiseParameters())
    @ns.response(schemas.DumpDetailedCruiseSchema())
    def put(self, payload, cruise):
        """Update cruise record."""
        if 'yacht_id' in payload:
            payload['yacht'] = YachtModel.get(id=payload.pop('yacht_id'),
                                              version=payload.pop('yacht_version', None),
                                              fail_ns=ns)
        try:
            cruise.update(**payload)
        except exc.IntegrityError as e:
            db.session().rollback()
            ns.abort(HTTPStatus.CONFLICT,
                     'Database Error: Could not edit cruise')
        return cruise

    @ns.permission_required(permissions.WriteAccessPermission, target_id='cruise_id')
    @ns.response(code=HTTPStatus.NO_CONTENT, description='Cruise deleted')
    @ns.response(code=HTTPStatus.CONFLICT, description='Cannot delete cruise')
    def delete(self, cruise):
        """
        Delete all versions of a cruise and all associated roles.
        """
        c_versions = CruiseModel.get_all_versions(cruise.id, fail_ns=ns)
        try:
            for c in c_versions:
                for r in c.roles:
                    r.delete_all_versions()
                c.delete()
        except exc.IntegrityError as e:
            db.session().rollback()
            ns.abort(HTTPStatus.CONFLICT, '')
        return '', HTTPStatus.NO_CONTENT


role_proxies = [CruiseModel.Role.to_proxy_name(r) for r in CruiseModel.Role]


@ns.route('/<int:cruise_id>/<string:role>/', methods=['GET', 'POST'])
@ns.param('cruise_id', 'Cruise ID', sqla_model=CruiseModel)
@ns.param('role', ' | '.join(role_proxies))
class ListByRole(Resource):
    """Role specific cruise operations."""

    @ns.permission_required(permissions.ReadAccessPermission, target_id='cruise_id')
    @ns.response(userSchemas.BaseProfileSchema(many=True))
    def get(self, role, cruise):
        """List cruise users for specified role."""
        if role not in role_proxies:
            ns.abort(HTTPStatus.NOT_FOUND,
                     '{} is not a supported role for this endpoint.'.format(role))
        role_profiles = getattr(cruise, role)  # dynamically get <role> proxy
        # list() ensures that the list is actually created through the proxy function,
        # before the parent is destroyed (when leaving the function):
        return list(role_profiles)

    @ns.permission_required(permissions.WriteAccessPermission, target_id='cruise_id')
    @ns.response(userSchemas.BaseProfileSchema(many=True))
    @ns.parameters(userParameters.ProfileByIdParameters())
    def post(self, payload, role, cruise):
        """Give specified role to user on specified cruise."""
        if role not in role_proxies:
            ns.abort(HTTPStatus.NOT_FOUND,
                     '{} is not a supported role for this endpoint'.format(role))

        p = UserProfileModel.get(payload.get('profile_id'), fail_ns=ns)
        if p not in current_user.profiles and p not in current_user.contacts:
            ns.abort(HTTPStatus.FORBIDDEN,
                     'You can only add profiles from your contact list.')

        role_profiles = getattr(cruise, role)  # dynamically get <role> proxy
        role_profiles.append(p)
        try:
            cruise.save()
            # list() ensures that the list is actually created by the proxy,
            # before c is destroyed (when leaving the function):
            return list(role_profiles)
        except exc.IntegrityError as e:
            db.session.rollback()
            ns.abort(HTTPStatus.CONFLICT,
                     "{} is already registered as one of this cruise's {}".format(p.first_name, role))


@ns.route('/<int:cruise_id>/<string:role>/by_profile/<int:profile_id>', methods=['DELETE'])
@ns.param('cruise_id', 'Cruise ID', sqla_model=CruiseModel)
@ns.param('role', '|'.join(role_proxies))
@ns.param('profile_id', 'User profile identifier')
class DeleteByRole(Resource):
    """Role specific deletion operations."""

    @ns.permission_required(permissions.WriteAccessPermission, target_id='cruise_id')
    @ns.resolve_arg('profile_id')
    @ns.response(userSchemas.BaseProfileSchema(many=True))
    @ns.response(code=HTTPStatus.CONFLICT, description='Cannot delete role')
    def delete(self, cruise, role, profile):
        """Remove specified role for user on specified cruise."""
        if role not in role_proxies:
            ns.abort(HTTPStatus.NOT_FOUND, '{} is not a supported role for this endpoint'.format(role))

        profiles = getattr(cruise, role)  # dynamically get <role> proxy
        if profile not in profiles:
            ns.abort(HTTPStatus.NOT_FOUND,
                     "Profile id {} is not currently one of this cruise's {}".format(profile.id, role))
        for r in cruise.roles:
            proxy_role = CruiseModel.Role.to_proxy_name(r.role)
            if r.profile_id == profile.id and proxy_role == role:
                r.delete()  # TODO: make sure versionning is handled correctly
        try:
            cruise.save()
        except exc.IntegrityError as e:
            db.session.rollback()
            ns.abort(HTTPStatus.CONFLICT,
                     "{} cannot be removed as one of this cruise's {}".format(profile.first_name, role))
        return '', HTTPStatus.NO_CONTENT

@ns.route('/<int:cruise_id>/approval/', methods=['GET', 'POST'])
@ns.param('cruise_id', 'Cruise ID', sqla_model=CruiseModel)
class CruiseApprovalList(Resource):
    """Cruise approval list resource."""

    @ns.permission_required(permissions.ReadAccessPermission, target_id='cruise_id')
    @ns.response(userSchemas.BaseProfileSchema(many=True))
    def get(self, cruise):
        """Fetch approval record.

        Returns list of profiles that have approved cruise.
        """
        print(cruise.approvals)
        print(cruise.approved_by_profiles)
        return cruise.approved_by_profiles

    @ns.permission_required(permissions.WriteAccessPermission, target_id='cruise_id')
    @ns.parameters(parameters.AddApprovalParameters())
    @ns.response(userSchemas.BaseProfileSchema(many=True))
    def post(self, payload, cruise):
        """
        Add approval record.

        Takes user ID as input, but returns list of *profiles* that have approved cruise.
        """
        user = UserModel.get(payload['user_id'], fail_ns=ns)
        if user != current_user and not current_user.is_admin:
            ns.abort(HTTPStatus.UNAUTHORIZED, 'You are not allowed to approve for this user.')
        if not cruise.check_approval_right(user):
            ns.abort(HTTPStatus.UNAUTHORIZED, 'You are not allowed to approve this cruise.')
        try:
            UserCruiseApprovalModel.create(cruise=cruise, user=user)
        except exc.IntegrityError as e:
            db.session.rollback()
            ns.abort(HTTPStatus.CONFLICT, 'User has already approved cruise.')
        return cruise.approved_by_profiles


@ns.route('/<int:cruise_id>/approval_by/<int:user_id>', methods=['DELETE'])
@ns.param('cruise_id', 'Cruise ID', sqla_model=CruiseModel)
@ns.param('user_id', 'User ID', sqla_model=UserModel)
class CruiseApproval(Resource):
    """Cruise approval resource."""

    @ns.permission_required(permissions.WriteAccessPermission, target_id='cruise_id')
    @ns.permission_required(permissions.WriteAccessPermission, target_id='user_id')
    @ns.response(code=HTTPStatus.NO_CONTENT, description='Approval deleted')
    @ns.response(code=HTTPStatus.CONFLICT, description='Cannot delete approval')
    def delete(self, cruise, user):
        """
        Delete user approval for cruise.
        """
        try:
            removed = False
            for approval in cruise.approvals:
                if approval.user == user and approval.cruise == cruise:
                    cruise.approvals.remove(approval)
                    removed = True
            if not removed:
                ns.abort(HTTPStatus.NOT_FOUND, 'No approval from this user for this cruise.')
            else:
                cruise.save()
        except exc.IntegrityError as e:
            db.session().rollback()
            ns.abort(HTTPStatus.CONFLICT, 'Cannot delete approval.')
        return '', HTTPStatus.NO_CONTENT

@ns.route('/<int:cruise_id>/role_status/', methods=['GET'])
@ns.param('cruise_id', 'Cruise ID', sqla_model=CruiseModel)
class CruiseUserStatusList(Resource):
    """Status of each user (approved, signed etc) for cruise."""

    @ns.permission_required(permissions.ReadAccessPermission, target_id='cruise_id')
    @ns.response(schemas.RoleStatusSchema(many=True))
    def get(self, cruise):
        """Fetch approval, signature and last edit info for each role.

        Returns list of roles with profiles and status info for relevant roles.
        """
        return [r for r in cruise.roles if r.can_approve_cruise]

@ns.route('/<int:cruise_id>/lock', methods=['POST', 'DELETE'])
@ns.param('cruise_id', 'Cruise ID', sqla_model=CruiseModel)
class Lock(Resource):
    """Cruise locking (status == LOCKED)."""

    @ns.permission_required(permissions.WriteAccessPermission, target_id='cruise_id')
    @ns.parameters(parameters.UnlockParameters())
    @ns.response(schemas.DumpDetailedCruiseSchema())
    def post(self, payload, cruise):
        """Lock cruise resource."""
        user = UserModel.get(payload['user_id'], fail_ns=ns)
        if user != current_user and not current_user.is_admin:
            ns.abort(HTTPStatus.UNAUTHORIZED, 'You are not allowed to lock on behalf of this user.')
        cruise.change_status(CruiseModel.Status.LOCKED)
        return cruise

    @ns.permission_required(permissions.WriteAccessPermission, target_id='cruise_id')
    @ns.response(code=HTTPStatus.NO_CONTENT, description='Cruise unlocked')
    def delete(self, cruise):
        """Unlock cruise resource."""
        cruise.change_status(CruiseModel.Status.DRAFT)
        return '', HTTPStatus.NO_CONTENT
