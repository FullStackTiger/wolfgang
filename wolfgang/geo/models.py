# -*- coding: utf-8 -*-
"""Cruise models."""
import enum

from sqlalchemy import and_
from sqlalchemy.orm import foreign, remote

from wolfgang.database.model import db


class Country(db.Model):
    """Import of geoname countryInfo.txt dataset."""

    iso = db.Column(db.String(2), nullable=False, primary_key=True)
    iso3 = db.Column(db.String(3), nullable=False, unique=True)
    iso_numeric = db.Column(db.SmallInteger, nullable=False)
    fips = db.Column(db.String(16), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    capital = db.Column(db.String(255), nullable=False)
    area = db.Column(db.BigInteger, nullable=True)
    population = db.Column(db.BigInteger, nullable=True)
    continent = db.Column(db.String(3), nullable=True)
    tld = db.Column(db.String(5), nullable=True)
    currency_code = db.Column(db.String(5), nullable=True)
    currency_name = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(16), nullable=True)
    postal_code_format = db.Column(db.String(32), nullable=True)
    postal_code_regex = db.Column(db.String(32), nullable=True)
    languages = db.Column(db.String(255), nullable=True)
    geoname_id = db.Column(db.BigInteger, nullable=True)  # , db.ForeignKey('geoname.geoname_id'
    neighbours = db.Column(db.String(255), nullable=True)
    equivalent_fips_code = db.Column(db.String(255), nullable=True)


class Geoname(db.Model):
    """Import of geoname dataset."""

    class FeatureClass(enum.Enum):
        """Geoname feature class."""

        A = 'country, state, region…'
        H = 'stream, lake…'
        L = 'parks, area…'
        S = 'spot, building, farm…'

    class FeatureCode(enum.Enum):
        """
        Subset of Geoname Feature codes.

        Full list: http://www.geonames.org/export/codes.html
        """

        ADM1 = 'first-order administrative division'
        ADM1H = 'historical first-order administrative division'
        ADM2 = 'second-order administrative division'
        ADM2H = 'historical second-order administrative division'
        ADM3 = 'third-order administrative division'
        ADM3H = 'historical third-order administrative division'
        ADM4 = 'fourth-order administrative division'
        ADM4H = 'historical fourth-order administrative division'
        ADM5 = 'fifth-order administrative division'
        ADM5H = 'historical fifth-order administrative division'  # probably error in data
        ADMD = 'administrative division'
        ADMDH = 'historical administrative division'
        LTER = 'leased area'
        PCL = 'political entity'
        PCLD = 'dependent political entity'
        PCLF = 'freely associated state'
        PCLH = 'historical political entity'
        PCLI = 'independent political entity'
        PCLIX = 'section of independent political entity'
        PCLS = 'semi-independent political entity'
        PRSH = 'parish'
        TERR = 'territory'
        ZN = 'zone'
        ZNB = 'buffer zone'

        DCK = 'dock(s)'
        DCKB = 'docking basin'
        HBR = 'harbor(s)'
        HBRX = 'section of harbor'
        JTY = 'jetty'
        LDNG = 'landing'
        MAR = 'marina'
        NVB = 'naval base'
        PRT = 'port'
        RDST = 'roadstead'

    geoname_id = db.Column(db.BigInteger, nullable=False, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    ascii_name = db.Column(db.String(255), nullable=False)
    alternate_names = db.Column(db.String(1000), nullable=True)
    latitude = db.Column(db.Float(Precision=64), nullable=False)
    longitude = db.Column(db.Float(Precision=64), nullable=False)
    feature_class = db.Column(db.Enum(FeatureClass), nullable=False)
    feature_code = db.Column(db.Enum(FeatureCode), nullable=False)
    country_code = db.Column(db.String(2), db.ForeignKey(Country.iso), nullable=False)
    cc2 = db.Column(db.String(16), nullable=False)
    admin1_code = db.Column(db.String(5), nullable=False)
    admin2_code = db.Column(db.String(5), nullable=False)
    admin3_code = db.Column(db.String(5), nullable=False)
    admin4_code = db.Column(db.String(5), nullable=False)
    population = db.Column(db.BigInteger, nullable=False)
    elevation = db.Column(db.SmallInteger)
    dem = db.Column(db.SmallInteger, nullable=False)
    timezone = db.Column(db.String(255), nullable=False)
    modification_date = db.Column(db.Date, nullable=False)

    country = db.relationship(Country, foreign_keys=country_code, uselist=False, lazy='select')

    __table_args__ = (
        db.Index('feature', feature_code),
        db.Index('country_feature_admin', country_code, feature_code, admin1_code, admin2_code, admin3_code),
        # Index coords?
        {})

    @classmethod
    def get(cls, id, fail_ns=None):
        """Get by id."""
        x = cls.query.filter_by(geoname_id=id).first()
        if x is None and fail_ns is not None:
            fail_ns.abort(404, "{} id {} doesn't exist".format(cls.__name__, id))
        return x

    @property
    def display_name(self):
        """Full location name."""
        str = self.name
        if self.country and self.country.name != self.name:
            str += ' (' + self.country.name + ')'
        return str


conditions = (remote(Geoname.country_code) == foreign(Geoname.country_code),)
for i in ('1', '2', '3', '4'):
    field = getattr(Geoname, 'admin{}_code'.format(i))
    conditions = conditions + (remote(field) == foreign(field),)
    setattr(Geoname,
            'admin' + i,
            db.relationship(
                'Geoname',
                primaryjoin=and_(*conditions, remote(Geoname.feature_code) == 'ADM' + i),
                uselist=False,
                lazy='select',
                join_depth=1
            ))
