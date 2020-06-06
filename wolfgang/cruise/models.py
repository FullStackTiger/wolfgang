# -*- coding: utf-8 -*-
"""
Cruise models.
"""
import enum
from operator import attrgetter
import datetime as dt
from werkzeug.exceptions import Unauthorized

from flask_jwt_extended import current_user

from sqlalchemy import and_, event
from sqlalchemy.orm import foreign, object_session, session
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.associationproxy import association_proxy

from wolfgang.database import db
from wolfgang.database.versioned_model import Model, VersionedModel
from wolfgang.user.models import User, UserProfile
from wolfgang.billing.models import Charge
from wolfgang.utils import haversine

from .waypoint.models import DisEmbarkation, Waypoint
from .yacht.models import Yacht


class Cruise(VersionedModel):
    """A cruise object represents the different states of a contract."""

    class Status(enum.Enum):
        """Possible cruise (/contract) status."""

        DRAFT = 'Draft'
        LOCKED = 'Locked'
        CONTRACT = 'Contract'
        ADDENDUM = 'Addendum'
        ARCHIVED = 'Archived'

    class TripType(enum.Enum):
        """Type of trip."""

        OUTSIDE = 'Outside territorial waters'
        INTERNATIONAL = 'International waters'
        TERRITORIAL = 'Territorial waters'

    class Role(enum.Enum):
        """Cruise roles."""

        BROKER = 'Broker'
        CENTRAL_AGENT = 'Central Agent'
        STAKEHOLDER = 'Stakeholder'
        CAPTAIN = 'Captain'
        CLIENT = 'Client'
        CARRIER = 'Carrier'
        PASSENGER = 'Passenger'
        GUEST = 'Guest'

        @classmethod
        def to_proxy_name(cls, role, plural=True):
            """Transforms <ROLE> into <roles>."""
            return(role.name.lower() + ('s' if plural else ''))

    yacht_id = db.Column(db.Integer, nullable=True)
    yacht_version = db.Column(db.Integer, nullable=True)
    status = db.Column(db.Enum(Status), default=Status.DRAFT, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=True)
    creator = db.relationship(User)
    trip_type = db.Column(db.Enum(TripType), default=TripType.TERRITORIAL)

    charge_id = db.Column(db.Integer, db.ForeignKey(Charge.id), nullable=True)
    charge = db.relationship(Charge, back_populates='cruise')

    base_price_cruising = db.Column(db.Float, nullable=True)
    base_price_routing = db.Column(db.Float, nullable=True)
    vat_rate1 = db.Column(db.Float, nullable=True)
    payment_down_p1_amount = db.Column(db.Float, nullable=True)
    payment_down_p2_amount = db.Column(db.Float, nullable=True)
    payment_cea_amount = db.Column(db.Float, nullable=True)
    payment_bal_amount = db.Column(db.Float, nullable=True)

    payment_cea_datedue = db.Column(db.DateTime)
    payment_bal_datedue = db.Column(db.DateTime)
    payment_down_p2_datedue = db.Column(db.DateTime)

    roles = db.relationship('ProfileRole', back_populates='cruise', cascade='all,delete,delete-orphan', uselist=True)
    cruise_areas = db.relationship('CruisingArea', back_populates='cruise', cascade='all,delete,delete-orphan', uselist=True)

    approvals = db.relationship('UserCruiseApproval', back_populates='cruise', uselist=True, cascade = 'all,delete,delete-orphan')
    approved_by_users = db.relationship(User, secondary='user_cruise_approvals',
                                        uselist=True, backref='approved_cruises')
    special_conditions = db.relationship('SpecialCondition', back_populates='cruise', uselist=True)
    yacht = db.relationship(Yacht, back_populates='cruises')
    waypoints = db.relationship(Waypoint, back_populates='cruise', order_by=Waypoint.arr_date,
                                cascade='all, delete-orphan', uselist=True)

    fuel_price = db.relationship('FuelPrice', back_populates='cruise', cascade='all, delete-orphan', uselist=False)

    __table_args__ = (db.ForeignKeyConstraint([yacht_id, yacht_version], [Yacht.id, Yacht.version]), {})

    @property
    def profiles(self):
        """All cruise role profiles."""
        profiles = set()
        profiles.update(self.creator.profiles)
        for role in self.roles:
            profiles.add(role.profile)
        return profiles

    @property
    def approved_by_profiles(self):
        """Join user approval on cruise roles."""
        profiles = set()
        for approval in self.approvals:
            profiles.update(approval.profiles)
        return profiles


    ######### Template properties

    @property
    def first_waypoint(self):
        """Return first waypoint."""
        if self.waypoints is None:
            return None
        return self.waypoints[0]

    @property
    def last_waypoint(self):
        """Return last waypoint."""
        if self.waypoints is None:
            return None
        return self.waypoints[-1]

    @property
    def price_agreement(self):
        """Return price total agreement."""
        # PROBABLY MOVE TO DIFFERENT CLASS PRICE
        if self.fuel_price is None or self.fuel_price.base_price is None or self.base_price_routing is None:
            return None
        else:
            return self.fuel_price.base_price + self.base_price_routing + self.base_price_cruising or 0

    @property
    def total_distance(self):
        """Return total distance of route."""
        if not self.waypoints:
            return None
        if len(self.waypoints) <= 1:
            return 0

        distance = 0
        for wp1, wp2 in zip(self.waypoints[:-1], self.waypoints[1:]):
            distance += haversine(wp1.latitude, wp1.longitude,
                                  wp2.latitude, wp2.longitude)
        return distance

    def distance_to_go_from_wp(self, wp):
        """Return remaining distance from waypoint."""
        if not self.waypoints:
            return None
        wp_idx = self.waypoints.index(wp)
        if 1+wp_idx >= len(self.waypoints):
            return 0
        distance = 0
        for wp1, wp2 in zip(self.waypoints[wp_idx:-1], self.waypoints[1+wp_idx:]):
            distance += haversine(wp1.latitude, wp1.longitude,
                                  wp2.latitude, wp2.longitude)
        return distance

    @property
    def distance_nw(self):
        """Return distance in National waters."""
        # TO DO
        return 10

    @property
    def price_prorata_nw(self):
        """Return price prorata in National waters."""
        if (self.price_agreement is None) or (self.distance_nw is None) or (not self.total_distance):
            return None
        else:
            return self.distance_nw / self.total_distance * self.price_agreement

    @property
    def vat_amount(self):
        """Return price prorata in National waters."""
        if (self.price_agreement is None) or (self.vat_rate1 is None):
            return None
        else:
            return self.price_agreement * self.vat_rate1

    @property
    def price_agreement_vat_inc(self):
        """Return price prorata in National waters."""
        if (self.price_agreement is None) or (self.vat_amount is None):
            return None
        else:
            return self.price_agreement + self.vat_amount

    @property
    def price_agreement_pass_vat_inc(self):
        """Return price prorata in National waters."""
        if (self.price_agreement_vat_inc is None) or (self.r_passengers is None):
            return None
        else:
            return self.price_agreement_vat_inc / len(self.r_passengers)


    ######### Resource Access management:

    @property
    def is_ongoing(self):
        """Make sure cruise can still be modified."""
        return (self.status != Cruise.Status.ARCHIVED)

    @property
    def locked(self):
        """Lock cruise resource if it has been approved or is not Draft."""
        return (self.status is not None) and (self.status != Cruise.Status.DRAFT)

    unlockable = ('approvals', 'status')

    def change_status(self, val):
        if self.status == val:
            return

        if val is not Cruise.Status.DRAFT and not self.locked:
            self.freeze_dependencies()
            self.status = val
            # print('Yacht id {} v: {} (latest: {})'.format(self.yacht.id, self.yacht.version, Yacht.get_latest_version(self.yacht.id)))
        elif val is Cruise.Status.DRAFT and self.locked:
            self.new_version()
            self.status = Cruise.Status.DRAFT
            # print('Cruise id {} v: {} (latest: {})'.format(self.id, self.version, Yacht.get_latest_version(self.id)))
            self.unfreeze_dependencies()
            # print('Yacht id {} v: {} (latest: {})'.format(self.yacht.id, self.yacht.version, Yacht.get_latest_version(self.yacht.id)))
        else:
            self.status = val

        self.save()

    def check_read_access(self, by_user):
        """If user is any role."""
        if self.creator_id == by_user.id:
            return True
        # TODO: replace following by a query
        for p in self.profiles:
            if p.id in [p_user.id for p_user in by_user.profiles]:
                return True
        return False

    def check_write_access(self, by_user):
        """User must have appropriate role or be creator."""
        if self.creator_id == by_user.id:
            return True
        # TODO: replace following by a query
        for r in self.roles:
            if r.can_edit_cruise and r.profile.id in [p_user.id for p_user in by_user.profiles]:
                return True
        return False

    def check_approval_right(self, by_user):
        """User must have appropriate role."""
        # TODO: replace following by a query
        for r in self.roles:
            if r.can_approve_cruise and r.profile.id in [p_user.id for p_user in by_user.profiles]:
                return True
        return False

    def new_version(self):
        """Create new version of object and all dependent relationships."""

        from sqlalchemy import exc, or_
        try:
            for r in self.roles:
                r.new_version()
        except exc.IntegrityError as e:
            db.session().rollback()

        super().new_version()

    def freeze_dependencies(self):
        """Create new version for all independent relationships."""
        if self.yacht and self.yacht.is_current_version:
            self.yacht.new_version(stay_old=True)
        for role in self.roles:
            if role.profile.is_current_version:
                role.profile.new_version(stay_old=True)

    def unfreeze_dependencies(self):
        """Catch-up to newest version for all independent relationships."""
        if self.yacht:
            self.yacht.load_current_version()
        if self.yacht_id:
            self.yacht_version = Yacht.get_latest_version(self.yacht_id)
        for role in self.roles:
            if role.profile:
                role.profile.load_current_version()


@event.listens_for(Cruise.approvals, 'append')
def approvals_append(cruise, value, initiator):
    if cruise.status is Cruise.Status.DRAFT:
        cruise.change_status(Cruise.Status.LOCKED)

@event.listens_for(Cruise.approvals, 'remove')
def approvals_removed(cruise, value, initiator):
    print("Approvals-remove event!\nApprovals: {}".format(len(cruise.approvals)))
    if len(cruise.approvals) == 0 and cruise.status is Cruise.Status.LOCKED:
        cruise.change_status(Cruise.Status.DRAFT)

@event.listens_for(Cruise, 'load')
def loaded_cruise(cruise, context):
    """Make sure all related resources are their latest version, unless locked."""
    if not cruise.locked:
        print('Cruise Load event (not locked)')
        cruise.unfreeze_dependencies() # garantees we are on latest versions

@event.listens_for(Cruise, 'after_update')
def track_last_edit(mapper, connection, cruise):
    """."""
    if not object_session(cruise).is_modified(cruise, include_collections=True):
        return
    if current_user == None:
        return
    for r in cruise.roles:
        if r.profile in current_user.profiles:
            connection.execute(ProfileRole.__table__.
                            update().
                            values(last_edit_dt=dt.datetime.now()).
                            where(ProfileRole.id == r.id))

class CruisingArea(VersionedModel):
    """Cruise's areas."""

    class Area(enum.Enum):
        """Cruise areas."""

        CARIBEAN = 'Caribean'
        CORSICA = 'Corsica'
        MEDITERRANEAN = 'Mediterranean'

    name = db.Column(db.String(150), nullable=True)
    area = db.Column(db.Enum(Area))
    cruise_id = db.Column(db.Integer)
    cruise = db.relationship(Cruise, back_populates='cruise_areas')

    @property
    def locked(self):
        """Ascend cruise dependency tree to check if resource is locked."""
        if self.cruise:
            return self.cruise.locked
        else:
            return False

    __table_args__ = (db.ForeignKeyConstraint([cruise_id, 'version'], ['cruises.id', 'cruises.version']), {})


class ProfileRole(VersionedModel):
    """Role of a user's profile in a cruise."""

    profile_id = db.Column(db.Integer, nullable=False)
    profile_version = db.Column(db.Integer)
    cruise_id = db.Column(db.Integer, nullable=False)
    role = db.Column(db.Enum(Cruise.Role))
    cruise = db.relationship(Cruise, back_populates='roles')
    profile = db.relationship(UserProfile, back_populates='roles')
    disembs = db.relationship(DisEmbarkation, back_populates='profile_role')
    last_edit_dt = db.Column(db.DateTime, nullable=True)

    __table_args__ = (db.ForeignKeyConstraint([profile_id, profile_version], [UserProfile.id, UserProfile.version]),
                      db.ForeignKeyConstraint([cruise_id, 'version'], [Cruise.id, Cruise.version]),
                      db.UniqueConstraint(cruise_id, profile_id, role, 'version', name='cruise_role_profile'))

    @property
    def locked(self):
        """Ascend cruise dependency tree to check if resource is locked."""
        if self.cruise:
            return self.cruise.locked
        else:
            return False

    @hybrid_property
    def can_edit_cruise(self):
        """Can role edit cruise information."""
        return self.role in [Cruise.Role.BROKER,
                             Cruise.Role.CENTRAL_AGENT,
                             Cruise.Role.STAKEHOLDER,
                             Cruise.Role.CLIENT,
                             Cruise.Role.CARRIER,
                             Cruise.Role.CAPTAIN]

    @hybrid_property
    def can_approve_cruise(self):
        """Can approve and sign cruise info."""
        return self.role in [Cruise.Role.BROKER,
                             Cruise.Role.STAKEHOLDER,
                             Cruise.Role.CLIENT,
                             Cruise.Role.CARRIER]

    @property
    def current_approval(self):
        """Has approved current version."""
        return (self.profile.user in self.cruise.approved_by_users)

    @property
    def past_approval(self):
        """Has approved past version."""
        for c in self.cruise.get_previous_versions():
            if self.profile.user in c.approved_by_users:
                return True
        return False

    @property
    def has_signed(self):
        """Has signed current version."""
        #TODO: use a relationship
        return False

    @property
    def embarkation(self):
        """Return embark if any."""
        if not self.disembs:
            return None
        return min(self.disembs, key=attrgetter('date'))

    @property
    def disembarkation(self):
        """Return disembark if any."""
        if not self.disembs:
            return None
        return max(self.disembs, key=attrgetter('date'))

    @classmethod
    def create_with_profile_role(cls, profile, role):
        """Shortcut creation class method used by cruise proxy properties."""
        obj = cls()
        obj.profile = profile
        obj.role = role
        return obj


# Dynamically create a relationship and associated proxy for each Cruise.Role:
for role in Cruise.Role:
    relationship_name = 'r_' + Cruise.Role.to_proxy_name(role, plural=True)
    setattr(Cruise,
            relationship_name,
            db.relationship(ProfileRole,
                            primaryjoin=and_(ProfileRole.cruise_id == Cruise.id,
                                             ProfileRole.version == Cruise.version,
                                             ProfileRole.role == role.name),
                            uselist=True,
                            lazy='dynamic'))
    setattr(Cruise,
            Cruise.Role.to_proxy_name(role, plural=True),
            association_proxy(relationship_name,
                              'profile',
                              creator=lambda profile, role=role: ProfileRole.create_with_profile_role(profile, role)))

# Need to be added afterward to avoid circular import
UserProfile.roles = db.relationship(ProfileRole, back_populates='profile')


class UserCruiseApproval(Model):
    """Approval of a specific cruise version by a user."""

    cruise_id = db.Column(db.Integer, nullable=False)
    cruise_version = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    user = db.relationship(User, backref='approvals')
    cruise = db.relationship(Cruise, back_populates='approvals')

    __table_args__ = (db.ForeignKeyConstraint([cruise_id, cruise_version],
                                         [Cruise.id, Cruise.version],
                                            ondelete='CASCADE'),
                      db.UniqueConstraint(cruise_id, cruise_version, user_id, name='cruise_version_user'))

    @hybrid_property
    def profiles(self):
        return (r.profile for r in self.cruise.roles if r.can_approve_cruise and (r.profile.user_id == self.user_id))

class SpecialCondition(VersionedModel):
    """special condition for a cruise."""

    cruise_id = db.Column(db.Integer, nullable=False)
    cruise = db.relationship(Cruise, back_populates='fuel_price')
    name = db.Column(db.String(255), nullable=False)
    product = db.Column(db.String(255))
    price = db.Column(db.Float, nullable=True)
    cruise = db.relationship(Cruise, back_populates='special_conditions')

    __table_args__ = (db.ForeignKeyConstraint([cruise_id, 'version'], [Cruise.id, Cruise.version]), {})


class FuelPrice(VersionedModel):
    """Negotiated full price for a cruise."""

    cruise_id = db.Column(db.Integer, nullable=False)
    cruise = db.relationship(Cruise, back_populates='fuel_price')
    quantity_routing = db.Column(db.Integer, nullable=True)
    quantity_cruising = db.Column(db.Integer, nullable=True)
    base_price_litre = db.Column(db.Float, nullable=True)
    real_price_litre = db.Column(db.Float, nullable=True)

    @property
    def quantity_tot(self):
        """Total quantity available."""
        return (self.quantity_routing or 0) + (self.quantity_cruising or 0)

    @property
    def base_price(self):
        """Base price."""
        return (self.base_price_litre or 0) * self.quantity_tot

    @property
    def locked(self):
        """Ascend cruise dependency tree to check if resource is locked."""
        if self.cruise:
            return self.cruise.locked
        else:
            return False

    __table_args__ = (db.ForeignKeyConstraint([cruise_id, 'version'], [Cruise.id, Cruise.version]), {})
