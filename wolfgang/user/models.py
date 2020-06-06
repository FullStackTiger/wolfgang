# -*- coding: utf-8 -*-
"""User models."""

from sqlalchemy import and_, asc, desc, event
from sqlalchemy.orm import Session, backref, foreign

from wolfgang.database import db
from wolfgang.database.model import Model
from wolfgang.database.versioned_model import VersionedModel
from wolfgang.extensions import bcrypt
from wolfgang.geo.models import Country


class User(Model):
    """Registered app user."""

    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.Binary(128), nullable=True)  # hashed by the ORM
    is_active = db.Column(db.Boolean(), default=True)
    is_admin = db.Column(db.Boolean(), default=False)
    profiles_versioned = db.relationship(
        'UserProfile',
        uselist=True,
        lazy='select',
        back_populates='user',
        cascade='all, delete-orphan'
    )

    # approved_cruises backref is defined in Cruise model
    # approvals backref is defined in UserCruiseApproval model
    # profiles and main_profile are defined after UserProfile

    def __init__(self, email, password=None, **kwargs):
        """Create new user."""
        Model.__init__(self, email=email, **kwargs)
        if password:
            self.set_password(password)
        else:
            self.password = None

    @property
    def contacts(self):
        """Aggregation of contacts for all profiles."""
        all_contacts = []
        for p in self.profiles:
            all_contacts.extend(p.contacts)
        return all_contacts

    @property
    def has_logged_in(self):
        """Whether user ever logged into the system."""
        return self.password is not None

    def set_password(self, password):
        """Set password."""
        self.password = bcrypt.generate_password_hash(password)

    def is_password_correct(self, value):
        """Check password."""
        return isinstance(value, str) and bcrypt.check_password_hash(self.password, value)

    def save(self, **kwargs):
        """Save the record after making sure there is only one main profile."""
        self.enforce_one_main()
        self.set_profile_names()
        return super().save(**kwargs)

    def enforce_one_main(self):
        """Automatically disable all but one profiles' main status."""
        are_main = [p.is_main is True for p in self.profiles]
        if len(are_main) > 0:
            if sum(are_main) > 1:  # Multiple main profile: pick last one
                picked = False
                for p in reversed(self.profiles):
                    if p.is_main is True:
                        if picked:
                            p.is_main = False
                        else:
                            picked = True
            elif sum(are_main) == 0:  # No main profile: pick first profile
                self.profiles[0].is_main = True

    def set_profile_names(self):
        """Makes sure all profiles have a profile_name."""
        alt_template = 'Alt Profile #'
        main_template = 'Main Profile'
        top_num = 0
        for p in self.profiles:
            if not p.is_main and p.profile_name == main_template:
                p.profile_name = None
            elif p.is_main and p.profile_name is None:
                p.profile_name = main_template
            elif p.profile_name and p.profile_name.startswith(alt_template):
                try:
                    num = int(p.profile_name.replaces(alt_template, ''))
                except BaseException:
                    num = 0
                top_num = max(num, top_num)
        top_num += 1
        for p in self.profiles:
            if p.profile_name is None:
                p.profile_name = alt_template + str(top_num)
                top_num += 1

    @property
    def full_name(self):
        """Full user name."""
        return self.main_profile.full_name

    def check_read_access(self, by_user):
        """User can read their own."""
        return self.id == by_user.id

    def check_write_access(self, by_user):
        """User can delete their own."""
        return self.id == by_user.id

    def __repr__(self):
        """Represent instance as a unique string."""
        return '<User id:{} ({})>'.format(self.id, self.email)


class UserProfile(VersionedModel):
    """User profile(s)."""

    profile_name = db.Column(db.String(150), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship('User', back_populates='profiles_versioned')

    is_main = db.Column(db.Boolean(), default=False, nullable=False)
    first_name = db.Column(db.String(150), nullable=True)
    last_name = db.Column(db.String(150), nullable=True)
    main_phone = db.Column(db.String(30), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    passport_num = db.Column(db.String(150), nullable=True)
    passport_country_iso = db.Column(db.String(2), db.ForeignKey(Country.iso), nullable=True)
    passport_country = db.relationship(Country, foreign_keys=[passport_country_iso])
    passport_expiration = db.Column(db.Date, nullable=True)
    place_of_birth = db.Column(db.String(150), nullable=True)
    address = db.Column(db.String(150), nullable=True)
    address_country_iso = db.Column(db.String(2), db.ForeignKey(Country.iso), nullable=True)
    address_country = db.relationship(Country, foreign_keys=[address_country_iso])

    is_company = db.Column(db.Boolean(), default=False)
    company_name = db.Column(db.String(150), nullable=True)
    company_reg_num = db.Column(db.String(150), nullable=True)
    company_reg_address = db.Column(db.String(150), nullable=True)
    company_reg_country = db.Column(db.String(150), nullable=True)
    company_reg_country_iso = db.Column(db.String(2), db.ForeignKey(Country.iso), nullable=True)
    company_reg_country = db.relationship(Country, foreign_keys=[company_reg_country_iso])
    company_vat_num = db.Column(db.String(150), nullable=True)
    company_insurance_pol = db.Column(db.String(150), nullable=True)
    company_insurance_name = db.Column(db.String(150), nullable=True)
    company_affil = db.Column(db.String(150), nullable=True)
    company_affil_num = db.Column(db.String(150), nullable=True)
    myba_num = db.Column(db.String(150), nullable=True)
    travel_agent_id = db.Column(db.String(150), nullable=True)
    financial_guarantee = db.Column(db.String(150), nullable=True)
    capacity = db.Column(db.String(150), nullable=True)

    bank_name = db.Column(db.String(150), nullable=True)
    bank_address = db.Column(db.String(150), nullable=True)
    bank_country_iso = db.Column(db.String(2), db.ForeignKey(Country.iso), nullable=True)
    bank_country = db.relationship(Country, foreign_keys=[bank_country_iso])
    account_num = db.Column(db.String(150), nullable=True)
    account_name = db.Column(db.String(150), nullable=True)
    iban = db.Column(db.String(150), nullable=True)
    swiftbic = db.Column(db.String(150), nullable=True)

    # roles relationship is defined after ProfileRole to avoid circular imports

    @property
    def locked(self):
        """Ascend cruise dependency tree to check if resource is locked."""
        for role in self.roles or []:
            if role.locked:
                return True
        return False

    @property
    def contacts(self):
        """Property that returns users' contacts (bijective relationship)."""
        all_nodes = [x.lower_profile for x in self.higher_edges]
        all_nodes.extend([x.higher_profile for x in self.lower_edges])
        return all_nodes

    def add_contacts(self, *profiles):
        """Add multiple profiles as contact."""
        for p in profiles:
            ContactEdge(self, p)
        return self

    def add_contact(self, profile):
        """Add single profile as contact."""
        if profile not in self.contacts:
            self.add_contacts(profile)
        return self

    def remove_contact(self, profile_id, fail_ns=None):
        """Remove profile_id from contacts (bijective relationship)."""
        ContactEdge.get(self.id, profile_id, fail_ns=fail_ns).delete()

    @property
    def full_name(self):
        """Full user name."""
        str = ''
        if self.first_name:
            str = self.first_name + ' '
        str += self.last_name or ''
        return str

    @property
    def initials(self):
        """Initials."""
        return ''.join([s[0] for s in self.full_name.split()])

    def check_read_access(self, by_user):
        """User can only read their own profile, contacts' and cruises'."""
        if self.user_id == by_user.id or self in by_user.contacts:
            return True
        for role in self.roles or []:
            if role.cruise.check_read_access(by_user):
                return True
        return False

    def check_write_access(self, by_user):
        """Can edit profiles of contacts that are non-connected or linked by cruise."""
        if self.user_id == by_user.id:
            return True
        if not self.user.has_logged_in and self in by_user.contacts:
            return True
        for role in self.roles or []:
            if role.cruise.check_write_access(by_user):
                return True
        return False

    def __repr__(self):
        return super().__repr__() + ': ' + str(self.first_name) + ' ' + str(self.last_name)


@event.listens_for(Session, 'before_flush')
def before_flush(session, flush_context, instances):
    """Validate profiles to avoid multiple/no mains."""
    for instance in session.dirty:
        if not isinstance(instance, UserProfile):
            continue
        if not session.is_modified(instance, passive=True):
            continue
        # if not attributes.instance_state(instance).has_identity:
        #     continue

        instance.user.enforce_one_main()


User.main_profile = db.relationship(
    UserProfile,
    uselist=False,
    primaryjoin=and_(foreign(UserProfile.user_id) == User.id,
                     UserProfile.is_current_version,
                     UserProfile.is_main))
User.profiles = db.relationship(
    UserProfile,
    uselist=True,
    primaryjoin=and_(foreign(UserProfile.user_id) == User.id,
                     UserProfile.is_current_version),
    # NOT setting cascade='all, delete-orphan' so that we can handle DELETE of versions by hand:
    order_by=(desc(UserProfile.is_main), asc(UserProfile.created_at)))


class ContactEdge(db.Model):
    """Association table between profiles."""

    __tablename__ = 'contact_edge'

    lower_id = db.Column(db.Integer,
                         db.ForeignKey(UserProfile.id),
                         primary_key=True)

    higher_id = db.Column(db.Integer,
                          db.ForeignKey(UserProfile.id),
                          primary_key=True)

    lower_profile = db.relationship(UserProfile, uselist=False,
                                    primaryjoin=and_(
                                        lower_id == UserProfile.id, UserProfile.is_current_version),
                                    backref=backref('lower_edges', uselist=True),
                                    viewonly=True)
    higher_profile = db.relationship(UserProfile, uselist=False,
                                     primaryjoin=and_(
                                         higher_id == UserProfile.id, UserProfile.is_current_version),
                                     backref=backref('higher_edges', uselist=True),
                                     viewonly=True)

    def __init__(self, n1, n2):
        """Always insure that lower.id <= higher.id."""
        if n1.id < n2.id:
            self.lower_profile = n1
            self.higher_profile = n2
            self.lower_id = n1.id
            self.higher_id = n2.id
        else:
            self.lower_profile = n2
            self.higher_profile = n1
            self.lower_id = n2.id
            self.higher_id = n1.id

    @classmethod
    def create(cls, **kwargs):
        """Create a new record and save it the database."""
        instance = cls(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    @classmethod
    def get(cls, n1_id, n2_id, fail_ns=None):
        """Get (bijective) contact edge from 2 profiles."""
        if n1_id < n2_id:
            lower_id = n1_id
            higher_id = n2_id
        else:
            lower_id = n2_id
            higher_id = n1_id
        x = cls.query.filter_by(lower_id=lower_id, higher_id=higher_id).first()
        if x is None and fail_ns is not None:
            fail_ns.abort(404, 'No link exists between these 2 profiles.')
        return x

    def delete(self, commit=True):
        """Remove the record from the database."""
        db.session.delete(self)
        return commit and db.session.commit()


# TODO: see if following model can be made bijective
# class ContactAssoc(db.Model):
#     __tablename__ = 'contact_assoc'
#     up1_id = db.Column(db.Integer, primary_key=True)
#     up1_version = db.Column(db.Integer, primary_key=True)
#     up2_id = db.Column(db.Integer, primary_key=True)
#     up2_version = db.Column(db.Integer, primary_key=True)
#     __table_args__ = (
#      ForeignKeyConstraint( [up1_id, up1_version], [UserProfile.id, UserProfile.version] ),
#      ForeignKeyConstraint( [up2_id, up2_version], [UserProfile.id, UserProfile.version] ),
#                         {})
#
# UserProfile.contacts = db.relationship(ContactAssoc, uselist=True,
#                            secondary='contact_assoc',
#                            primaryjoin='and_(ContactAssoc.up1_id==UserProfile.id,
#                            ContactAssoc.up1_version==UserProfile.version)',
#                            secondaryjoin='and_(ContactAssoc.up2_id==UserProfile.id,
#                            ContactAssoc.up2_version==UserProfile.version)'
#                            )

# TODO: figure out why version using a non-ORM table doesn't work:
# contact_assoc_table = db.Table('contact_assoc', db.Model.metadata,
#     db.Column('up1_id', Integer, primary_key=True),
#     db.Column('up1_version', Integer, primary_key=True),
#     db.Column('up2_id', Integer, primary_key=True),
#     db.Column('up2_version', Integer, primary_key=True),
#     ForeignKeyConstraint( ('up1_id', 'up1_version'), (UserProfile.id, UserProfile.version) ),
#     ForeignKeyConstraint( ('up2_id', 'up2_version'), (UserProfile.id, UserProfile.version) ),
# )
#
#
# UserProfile.contacts = db.relationship(contact_assoc_table, uselist=True,
#                           secondary='contact_assoc',
#                            primaryjoin='and_(contact_assoc.c.up1_id==UserProfile.id,
#                            contact_assoc.c.up1_version==UserProfile.version)',
#                            secondaryjoin='and_(contact_assoc.c.up2_id==UserProfile.id,
#                            contact_assoc.c.up2_version==UserProfile.version)'
#                            )
#
