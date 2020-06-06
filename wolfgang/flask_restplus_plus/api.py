"""
Patched version of flask_restplus customised to handle marshmallow schema.
"""
from http import HTTPStatus

from flask import jsonify
from flask_restplus import Api as OriginalApi
from werkzeug import cached_property

from .namespace import Namespace
from .swagger import Swagger


class Api(OriginalApi):
    """
    Extended Flast-RESTPlus Api to add options and override methods.
    """

    @cached_property
    def __schema__(self):
        """Only purpose of this method is to pass a custom Swagger class."""
        return Swagger(self).as_dict()

    def init_app(self, app, **kwargs):
        """Add errorhandler."""
        super(Api, self).init_app(app, **kwargs)
        app.errorhandler(HTTPStatus.UNPROCESSABLE_ENTITY.value)(handle_validation_error)

    def namespace(self, *args, **kwargs):
        """Only purpose of this method is to pass a custom Namespace class."""
        _namespace = Namespace(*args, **kwargs)
        self.add_namespace(_namespace)
        return _namespace


def handle_validation_error(err):
    """Return validation errors as JSON."""
    exc = err.data['exc']
    return jsonify({
        'status': HTTPStatus.UNPROCESSABLE_ENTITY.value,
        'message': exc.messages
    }), HTTPStatus.UNPROCESSABLE_ENTITY.value
