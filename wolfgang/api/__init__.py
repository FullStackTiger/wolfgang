# encoding: utf-8
"""
API extension.
"""

from copy import deepcopy
from http import HTTPStatus

from flask import Blueprint, current_app

from wolfgang.database import ObjectLockedException, db
from wolfgang.flask_restplus_plus import Resource

from .api import Api
from .http_exceptions import abort
from .namespace import Namespace


authorizations = {
    'access_token': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'tokenUrl': 'https://localhost:5000/user/login',  # TODO: try and make Swagger display URL
        'description': "api_key should be of the format: 'Bearer [token]'"
    }
}

api_blueprint = Blueprint('api', __name__, url_prefix='/api')  # TODO: add versioning?
api = Api(
    api_blueprint,
    version='1.0',
    title='Wolfgang API',
    description='Wolfgang API',
    authorizations=authorizations,
    security='access_token')


@api.errorhandler(ObjectLockedException)
def handle_object_locked_exception(error):
    """Return a 423 Locked HTTP code, when trying to update a locked cruise-related object."""
    db.session.rollback()
    return {'message': 'This resource is locked and cannot be modified.'}, HTTPStatus.LOCKED


user_ns = api.namespace('user', 'User endpoints')
cruise_ns = api.namespace('cruise', 'Cruise endpoints')
yacht_ns = api.namespace('yacht', 'Yacht endpoints')
geo_ns = api.namespace('geo', 'Geo endpoints')
contract_ns = api.namespace('contract', 'Contract endpoints')
