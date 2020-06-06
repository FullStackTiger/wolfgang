"""
Patched version of flask_restplus customised to handle marshmallow schema.
"""
import flask_restplus

from .api import Api
from .model import DefaultHTTPErrorSchema, DumpModelSchemaMixin, ModelSchema, Schema
from .namespace import Namespace
from .parameters import JSONParameters, Parameters, PatchJSONParameters
from .resource import Resource
from .swagger import Swagger
