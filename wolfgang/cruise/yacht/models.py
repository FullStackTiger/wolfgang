# -*- coding: utf-8 -*-
"""Yacht models."""

import enum
import os
import uuid
from http import HTTPStatus

from flask import request, current_app, url_for

from wolfgang.database import db
from wolfgang.database.versioned_model import VersionedModel
from wolfgang.geo.models import Country, Geoname
from wolfgang.user.models import User


class Yacht(VersionedModel):
    """Yacht used by cruise."""

    class Type(enum.Enum):
        """Yacht types."""

        SAIL = 'Sailing'
        MOTOR = 'Motor'

    name = db.Column(db.String(150), nullable=False)
    imo_nb = db.Column(db.Integer, nullable=True)
    flag_country_iso = db.Column(db.String(2), db.ForeignKey(Country.iso), nullable=True)
    flag = db.relationship(Country, foreign_keys=[flag_country_iso])
    port_of_registry_id = db.Column(db.BigInteger, db.ForeignKey(Geoname.geoname_id), nullable=True)
    port_of_registry = db.relationship(Geoname, foreign_keys=[port_of_registry_id])
    type = db.Column(db.Enum(Type), default=Type.MOTOR)
    loa = db.Column(db.Float)
    max_nb_passengers = db.Column(db.Integer, nullable=True)
    nb_berth = db.Column(db.Integer, nullable=True)
    max_nb_days = db.Column(db.Integer, nullable=True)
    max_spd = db.Column(db.Float, nullable=True)
    max_spd_cons = db.Column(db.Float, nullable=True)
    cruis_spd = db.Column(db.Float, nullable=True)
    cruis_spd_cons = db.Column(db.Float, nullable=True)
    eco_spd = db.Column(db.Float, nullable=True)
    eco_spd_cons = db.Column(db.Float, nullable=True)
    mmsi_num = db.Column(db.String(9), nullable=True)
    call_sign = db.Column(db.String(64), nullable=True)
    official_num = db.Column(db.String(64), nullable=True)
    year_built = db.Column(db.Integer, nullable=True)
    gross_tonnage = db.Column(db.Float, nullable=True)
    displacement = db.Column(db.Float, nullable=True)
    draft = db.Column(db.Float, nullable=True)
    beam = db.Column(db.Float, nullable=True)
    yard = db.Column(db.String(64), nullable=True)
    fuel_capacity = db.Column(db.Float, nullable=True)
    engine_type = db.Column(db.String(64), nullable=True)
    engine_quantity = db.Column(db.SmallInteger, nullable=True)
    total_power = db.Column(db.Integer, nullable=True)

    creator_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=True)
    creator = db.relationship(User)

    cruises = db.relationship('Cruise', back_populates='yacht')

    pictures = db.relationship('YachtPicture')

    @property
    def locked(self):
        """Ascend cruise dependency tree to check if resource is locked."""
        for cruise in self.cruises or []:
            if cruise.locked:
                return True
        return False

    def check_read_access(self, by_user):
        """If user is involved in any cruise associated to yacht."""
        if self.creator_id == by_user.id:
            return True
        for cruise in self.cruises or []:
            for id in [p_c.id for p_c in cruise.profiles]:
                if id in [p_u.id for p_u in by_user.profiles]:
                    return True
        return False

    def check_write_access(self, by_user):
        """If user is involved in any cruise associated to yacht with proper role."""
        if self.creator_id == by_user.id:
            return True
        for cruise in self.cruises or []:
            if not cruise.is_ongoing:
                continue
            for r in cruise.roles:
                if r.can_edit_cruise and r.profile.id in [p_u.id for p_u in by_user.profiles]:
                    return True
        return False

    def is_imo_number(self, imo):
        """IMO nb must be 6+1 digits + extra check https://en.wikipedia.org/wiki/IMO_number."""
        str_imo = str(imo)
        if len(str_imo) != 7:
            return False
        try:
            digits = [int(x) for x in str_imo]
        except ValueError:
            return False  # conversion to int failed (not a digit)
        check_num = 0
        for i in range(2, 8):
            check_num += digits[7 - i] * i
        if check_num % 10 != digits[6]:
            return False
        return True

class YachtPicture(VersionedModel):
    """Yacht pictures."""

    class Type(enum.Enum):
        """Yacht picture types."""

        INTERIOR = 'Interior'
        EXTERIOR = 'Exterior'

    yacht_id = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(64), nullable=False)
    type = db.Column(db.Enum(Type), default=Type.EXTERIOR)
    description = db.Column(db.String(250), nullable=True)

    __table_args__ = (db.ForeignKeyConstraint([yacht_id, 'version'], [Yacht.id, Yacht.version]),
                    db.UniqueConstraint(yacht_id, 'version', filename, name='yacht_filename'), {})

    def __init__(self, file, fail_ns, *pargs, **kwargs):
        extension = file.filename.rsplit('.', 1)[-1].lower()
        if extension not in ('png', 'jpg', 'jpeg'):
            fail_ns.abort(HTTPStatus.UNPROCESSABLE_ENTITY, 'Only .png and .jpg files are allowed.')
        filename = '{}.{}'.format(uuid.uuid4().hex, extension)
        if file.save("{}/{}".format(self.dir_path(), filename)):
            fail_ns.abort(HTTPStatus.CONFLICT, 'Cannot save image file.')
        super().__init__(*pargs, filename = filename, **kwargs)

    def dir_path(self):
        destination = current_app.config.get('YACHT_IMG_FOLDER')
        if not os.path.exists(destination):
            os.makedirs(destination)
        return destination

    @property
    def public_url(self):
        print(url_for('img.yacht_picture', filename=self.filename))
        return url_for('img.yacht_picture', filename=self.filename)
