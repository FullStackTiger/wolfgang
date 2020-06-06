# -*- coding: utf-8 -*-
"""Yacht resources."""

import werkzeug
from http import HTTPStatus

from flask_restplus import reqparse
from sqlalchemy import exc

from wolfgang.api import Resource
from wolfgang.api import yacht_ns as ns
from wolfgang.database import db
from wolfgang.geo.models import Geoname as GeonameModel
from wolfgang.user import permissions
from wolfgang.user.models import User as UserModel

from . import parameters, schemas
from .models import Yacht as YachtModel, YachtPicture as YachtPictureModel


@ns.route('/', methods=['GET'])
class YachtList(Resource):
    """Yacht Admin operations."""

    @ns.permission_required(permissions.AdminRolePermission)
    @ns.response(schemas.BaseYachtSchema(many=True))
    def get(self):
        """
        List all yachts.

        Mainly for debug purposes (see /yacht/by_user/)
        """
        yachts = YachtModel.query.all()
        return yachts


@ns.route('/by_user/<int:user_id>/', methods=['GET', 'POST'])
@ns.param('user_id', 'User ID', sqla_model=UserModel)
class UserYachtList(Resource):
    """User-specific Yacht operations."""

    @ns.permission_required(permissions.ReadAccessPermission, target_id='user_id')
    @ns.response(schemas.BaseYachtSchema(many=True))
    def get(self, user):
        """List Yachts accessible to user."""
        yachts = YachtModel.query.filter(YachtModel.creator_id == user.id).all()
        return yachts

    @ns.permission_required(permissions.WriteAccessPermission, target_id='user_id')
    @ns.parameters(parameters.AddYachtParameters())
    @ns.response(schemas.DumpYachtSchema())
    def post(self, payload, user):
        """
        Create a new yacht.

        Automatically assigns user as creator
        """
        if user.main_profile is None:
            ns.abort(HTTPStatus.CONFLICT,
                     'User id {} does not have a profile to associate with yacht'.format(user.id))
        if 'port_of_registry_id' in payload:
            loc = GeonameModel.get(payload.pop('port_of_registry_id'), fail_ns=ns)
        else:
            loc = None
        try:
            c = YachtModel(port_of_registry=loc, creator=user, **payload)
            c.save()
            return c
        except exc.IntegrityError as e:
            db.session().rollback()
            ns.abort(HTTPStatus.CONFLICT,
                     'Database Error: Could not create yacht')


@ns.route('/<int:yacht_id>/<int:version>', methods=['GET', 'PUT', 'DELETE'])
@ns.route('/<int:yacht_id>', defaults={'version': None}, methods=['GET', 'PUT', 'DELETE'])
@ns.param('yacht_id', 'Yacht identifier', sqla_model=YachtModel)
class Yacht(Resource):
    """Single yacht resource."""

    # @ns.permission_required(permissions.ReadAccessPermission, target_id='yacht_id')
    @ns.permission_required(permissions.ReadAccessPermission, target_id=('yacht_id', 'version'))
    @ns.response(schemas.DumpYachtSchema())
    def get(self, yacht):
        """Fetch yacht record."""
        return yacht

    @ns.permission_required(permissions.WriteAccessPermission, target_id=('yacht_id', 'version'))
    @ns.response(code=HTTPStatus.CONFLICT, description='Cannot update yacht')
    @ns.parameters(parameters.EditYachtParameters())
    @ns.response(schemas.DumpYachtSchema())
    def put(self, payload, yacht):
        """Update yacht record."""
        try:
            print(yacht)
            yacht.update(**payload)
        except exc.IntegrityError as e:
            db.session().rollback()
            ns.abort(HTTPStatus.CONFLICT,
                     'Cannot apply changes to yacht.')
        return yacht

    @ns.permission_required(permissions.WriteAccessPermission, target_id=('yacht_id', 'version'))
    @ns.response(code=HTTPStatus.NO_CONTENT, description='Yacht deleted')
    @ns.response(code=HTTPStatus.CONFLICT, description='Cannot delete yacht')
    def delete(self, yacht):
        """
        Delete yacht and associated roles.
        """
        # c_versions = YachtModel.get_all_versions(yacht.id, fail_ns=ns)
        try:
            yacht.delete()
            # for c in c_versions:
                # c.delete()
        except exc.IntegrityError as e:
            db.session().rollback()
            ns.abort(HTTPStatus.CONFLICT,
                     'This yacht is used in existing contract and cannot be deleted.')
        return '', HTTPStatus.NO_CONTENT


file_upload = reqparse.RequestParser()
file_upload.add_argument('file',
                         type=werkzeug.datastructures.FileStorage,
                         location='files',
                         required=True,
                         help='Image file')


@ns.route('/<int:yacht_id>/image', methods=['POST'])
@ns.param('yacht_id', 'Yacht identifier', sqla_model=YachtModel)
@ns.expect(file_upload)
class YachtPicture(Resource):
    """Upload yacht picture."""

    @ns.permission_required(permissions.WriteAccessPermission, target_id='yacht_id')
    @ns.response(schemas.YachtPictureSchema(many=True))
    def post(self, yacht):
        """
        Save uploaded picture for a yacht.
        Return list of pictures associated to yacht.
        """
        args = file_upload.parse_args()

        if 'file' not in args:
            ns.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'No file data present.')

        print(yacht.pictures)
        yacht.pictures.append(YachtPictureModel(file = args['file'], fail_ns=ns))
        yacht.save()
        print(yacht.pictures)
        # file = request.files['file']
        # print(file)
            # yacht.update(**payload)
        return yacht.pictures
