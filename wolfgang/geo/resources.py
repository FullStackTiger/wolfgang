# -*- coding: utf-8 -*-
"""Cruise resources."""
# DEBUG:
# import logging
from http import HTTPStatus

from sqlalchemy import orm

from wolfgang.api import Resource
from wolfgang.api import geo_ns as ns

from .water_loc import locate_water_point
from . import parameters, schemas
from .models import Country as CountryModel
from .models import Geoname as GeonameModel


# DEBUG SQL queries:
# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


@ns.route('/search', methods=['POST'])
class GeonameSearch(Resource):
    """Filtering operations on geoname DB."""

    @ns.parameters(parameters.SearchGeonameParameters())
    @ns.response(schemas.GeonamePortSchema(many=True))
    def post(self, payload):
        """List geonames that fit query params."""
        geonames = GeonameModel.query.filter_by(**payload).limit(100).all()

        if geonames is None:
            ns.abort(HTTPStatus.NOT_FOUND, 'No geonames record matching this query.')
        return geonames


@ns.route('/ports', methods=['GET'])
class Ports(Resource):
    """Return geoname DB rows marked as port."""

    @ns.response(schemas.GeonamePortSchema(many=True))
    def get(self):
        """List geonames that fit query params."""
        admin4 = orm.aliased(GeonameModel)
        geonames = (GeonameModel.query
                    .join(GeonameModel.country)
                    .join((admin4, GeonameModel.admin4))
                    .options(
                        orm.contains_eager(GeonameModel.country),
                        orm.contains_eager(GeonameModel.admin4, alias=admin4))
                    .filter(
                        GeonameModel.feature_code == 'PRT',
                        CountryModel.continent.in_(('EU', 'AF', 'NA')),
                    ).order_by(admin4.name).all())

        if geonames is None:
            ns.abort(HTTPStatus.NOT_FOUND, 'No geonames record matching this query.')
        return geonames


@ns.route('/countries', methods=['GET'])
class Countries(Resource):
    """Return list of geoname DB countries."""

    @ns.response(schemas.BaseCountrySchema(many=True))
    def get(self):
        """List country dataset from geoname."""
        countries = CountryModel.query.all()

        if countries is None:
            ns.abort(HTTPStatus.NOT_FOUND, 'Cannot get list of countries.')
        return countries


@ns.route('/<int:geoname_id>', methods=['GET'])
@ns.param('geoname_id', 'Geoname identifier', sqla_model=GeonameModel)
class Geoname(Resource):
    """Single Geoname resource."""

    @ns.response(schemas.GeonameSchema())
    @ns.resolve_arg('geoname_id')
    def get(self, geoname):
        """Fetch Geoname record."""
        return geoname

@ns.route('/test_water/<float:lat>/<float:lon>', methods=['GET'])
class WaterLoc(Resource):
    """Test if in territorial water."""

    @ns.response(schemas.BaseCountrySchema())
    def get(self, lat, lon):
        """Test if in territorial water."""
        c_iso = locate_water_point((lon, lat))
        print(c_iso)
        if c_iso is None:
            ns.abort(HTTPStatus.NOT_FOUND, 'Not in any known territorial water')
        country = CountryModel.query.filter_by(iso3=c_iso).first()
        return country
