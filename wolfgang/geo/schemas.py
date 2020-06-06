# -*- coding: utf-8 -*-
"""
Schema used by REST interface.
"""
from flask_marshmallow import base_fields
from marshmallow_enum import EnumField

from wolfgang.flask_restplus_plus import ModelSchema

from .models import Country as CountryModel
from .models import Geoname as GeonameModel


class BaseCountrySchema(ModelSchema):
    """
    Country-specific schema with small subset of fields.
    """

    class Meta:
        # noqa
        model = CountryModel
        fields = (
            # CountryModel.geoname_id.key,
            CountryModel.iso.key,
            CountryModel.name.key,
        )


class CountrySchema(BaseCountrySchema):
    """
    Country-specific schema.
    """

    class Meta(BaseCountrySchema.Meta):
        # noqa
        fields = ()


class BaseGeonameSchema(ModelSchema):
    """
    Display-friendly geoname record.
    """

    feature_class = EnumField(GeonameModel.FeatureClass)
    feature_code = EnumField(GeonameModel.FeatureCode)
    country = base_fields.Nested(CountrySchema,
                                 only=(CountryModel.name.key))
    admin1 = base_fields.Nested('BaseGeonameSchema',
                                only=(GeonameModel.geoname_id.key,
                                      GeonameModel.name.key),
                                attribute=GeonameModel.admin1.key)
    admin2 = base_fields.Nested('BaseGeonameSchema',
                                only=(GeonameModel.geoname_id.key,
                                      GeonameModel.name.key),
                                attribute=GeonameModel.admin2.key)
    admin3 = base_fields.Nested('BaseGeonameSchema',
                                attribute=GeonameModel.admin3.key,
                                only=(GeonameModel.geoname_id.key,
                                      GeonameModel.name.key))
    admin4 = base_fields.Nested('BaseGeonameSchema',
                                attribute=GeonameModel.admin4.key,
                                only=(GeonameModel.geoname_id.key,
                                      GeonameModel.name.key))

    class Meta:
        # noqa
        model = GeonameModel
        fields = (
            'display_name',
            GeonameModel.geoname_id.key,
            GeonameModel.feature_code.key,
            GeonameModel.name.key,
            GeonameModel.country.key,
        )
        exclude = (
        )
        dump_only = (
            GeonameModel.admin1.key,
            GeonameModel.admin2.key,
            GeonameModel.admin3.key,
            GeonameModel.admin4.key,
            GeonameModel.country.key,
        )


class GeonamePortSchema(BaseGeonameSchema):
    """
    Port-specific schema.
    """

    city_name = base_fields.Nested('BaseGeonameSchema',
                                   only=(GeonameModel.name.key),
                                   attribute=GeonameModel.admin4.key,
                                   many=False)
    port_name = base_fields.String(attribute=GeonameModel.name.key)

    class Meta(BaseGeonameSchema.Meta):
        # noqa
        fields = (
            'city_name',
            'port_name',
            GeonameModel.geoname_id.key,
            GeonameModel.country.key,
            GeonameModel.alternate_names.key,
            GeonameModel.latitude.key,
            GeonameModel.longitude.key,
        )


class GeonameSchema(BaseGeonameSchema):
    """
    All location fields.
    """

    class Meta(BaseGeonameSchema.Meta):
        # noqa
        fields = ()
