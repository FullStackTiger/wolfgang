# -*- coding: utf-8 -*-
"""Cruise models."""


from wolfgang.database import db
from wolfgang.database.versioned_model import VersionedModel
from wolfgang.geo.models import Geoname


class Waypoint(VersionedModel):
    """A waypoint in the cruise route (version should match cruise's)."""

    cruise_id = db.Column(db.Integer, nullable=False)
    cruise = db.relationship('Cruise')
    latitude = db.Column(db.Float(Precision=64), nullable=False)
    longitude = db.Column(db.Float(Precision=64), nullable=False)
    is_call = db.Column(db.Boolean, default=False)
    geoname_id = db.Column(db.BigInteger, db.ForeignKey(Geoname.geoname_id))
    geoname = db.relationship(Geoname)
    call_location_str = db.Column(db.String(255))
    arr_date = db.Column(db.DateTime, nullable=False)
    dep_date = db.Column(db.DateTime)

    @property
    def locked(self):
        """Ascend cruise dependency tree to check if resource is locked."""
        return self.cruise.locked

    @property
    def call_location(self):
        """Location based on user-input or geoname."""
        if self.call_location_str and len(self.call_location_str) > 0:
            return self.call_location_str
        elif self.geoname:
            return self.geoname.display_name
        else:
            return ''
    @property
    def distance_to_go(self):
        return self.cruise.distance_to_go_from_wp(self)

    __table_args__ = (db.ForeignKeyConstraint([cruise_id, 'version'], ['cruises.id', 'cruises.version']), {})


class DisEmbarkation(VersionedModel):
    """A dis/embarkation Point for one user."""

    waypoint_id = db.Column(db.Integer)
    waypoint = db.relationship(Waypoint, viewonly=True)
    profile_role_id = db.Column(db.Integer, nullable=True)
    profile_role = db.relationship('ProfileRole', back_populates='disembs')
    date = db.Column(db.DateTime)

    @property
    def locked(self):
        """Ascend cruise dependency tree to check if resource is locked."""
        return self.profile_role.locked

    __table_args__ = (db.ForeignKeyConstraint([waypoint_id, 'version'], [Waypoint.id, Waypoint.version]),
                      db.ForeignKeyConstraint([profile_role_id, 'version'],
                                              ['profile_roles.id',
                                               'profile_roles.version']))
