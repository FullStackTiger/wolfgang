# -*- coding: utf-8 -*-
"""Model unit tests."""
import datetime as dt

import pytest

from wolfgang.user.models import UserProfile, User
from wolfgang.cruise.models import ProfileRole, Cruise

from tests.factories import UserFactory
# from wolfgang.database.populate_db import PopulateDb


@pytest.mark.usefixtures('populated_db')
class TestUserModel:
    """User unit tests."""

    def test_get_by_id(self):
        """Get user by ID."""
        user = User.create(email='foo@bar.com')
        retrieved = User.query.get(user.id)
        assert retrieved == user
        user.delete()

    def test_get_existing_user(self):
        """get an existing user. """
        user = User.get_by(email='arsene@lupin.com')
        assert user != None
        assert len(user.profiles) == 2

    def test_created_at_defaults_to_datetime(self):
        """Test creation date."""
        user = User.create(email='foo@bar.com')
        assert bool(user.created_at)
        assert isinstance(user.created_at, dt.datetime)
        user.delete()

    def test_password_is_nullable(self):
        """Test null password."""
        user = User.create(email='foo@bar.com')
        assert user.password is None
        user.delete()

    def test_factory(self, db):
        """Test user factory."""
        user = UserFactory(password='myprecious')
        db.session.commit()
        assert bool(user.email)
        assert bool(user.created_at)
        assert user.is_admin is False
        assert user.is_active is True
        assert user.is_password_correct('myprecious')
        user.delete()

    def test_check_password(self):
        """Check password."""
        user = User.create(email='foo@bar.com',
                           password='foobarbaz123')
        assert user.is_password_correct('foobarbaz123') is True
        assert user.is_password_correct('barfoobaz') is False
        user.delete()

    def test_profile_version(self):
        u = User.create(email="tatin@tarte.com", password='test')
        p1v0 = UserProfile.create(first_name='tatin', last_name='tarte', user_id=u.id)
        u.profiles.append(p1v0)
        #p1v0.save()
        u.save()
        p1v0.version += 1
        p1v0.save()
        assert UserProfile.query.filter_by(user_id=u.id, id=p1v0.id).first() == p1v0
        #assert UserProfile.query.filter_by(user_id=u.id, id=p1v0.id).count() > 1

    # def test_full_name(self):
    #     """User full name."""
    #     user = UserFactory(first_name='Foo', last_name='Bar')
    #     assert user.full_name == 'Foo Bar'

    # def test_get_all_versions(self):
    #     get_all_versions

    # def test_list_roles(self):
    #     """Add a role to a user."""
    #     st = dt.datetime.utcnow()

    #     u = User.create(email="tatin@tarte.com", password='test')
    #     p1v0 = UserProfile.create(first_name='tatin', last_name='tarte')
    #     p1v0.save()
    #     u = User.create(email="captain@igloo.com", password='test')
    #     p2v0 = UserProfile.create(first_name='captain', last_name='igloo')
    #     p2v0.save()
    #     u = User.create(email="voleur@tarte.com", password='test')
    #     p3v0 = UserProfile.create(first_name='voleur', last_name='tarte')
    #     p3v0.save()
    #     r1v0 = ProfileRole.create(cruise_id=c.id, profile_id=p1v0.id, profile_version=p1v0.version, role=Cruise.Role.PASSENGER)
    #     r2v0 = ProfileRole.create(cruise_id=c.id, profile_id=p2v0.id, profile_version=p2v0.version, role=Cruise.Role.CAPTAIN)
    #     r3v0 = ProfileRole.create(cruise_id=c2.id, profile_id=p3v0.id, profile_version=p3v0.version, role=Cruise.Role.CENTRAL_AGENT)

    #     assert r1v0 in c.roles
    #     assert r2v0 in c.roles
    #     assert r3v0 not in c.roles
