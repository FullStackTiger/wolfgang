# -*- coding: utf-8 -*-
"""Model unit tests."""
import datetime as dt

import pytest

from wolfgang.cruise.models import Cruise, Yacht
from wolfgang.cruise.yacht.models import Yacht
from wolfgang.user.models import UserProfile, User
from wolfgang.cruise.models import ProfileRole

@pytest.mark.usefixtures('populated_db')
class TestCruiseModel:
    """Cruise model unit tests."""

    def test_get_by_id(self):
        """Get CRUISE by ID."""

        st = dt.datetime.utcnow()
        cruise = Cruise.create()
        cruise.save()
        retrieved = Cruise.get_by(id=cruise.id, version=cruise.version)
        assert retrieved == cruise
        assert cruise.version == retrieved.version
        cruise.delete()

    def test_get_by_yacht(self):
        """Get CRUISE by ID."""
        b = Yacht.create(name="La Baleine")
        cruise = Cruise()
        cruise.yacht = b
        cruise.save()

        retrievedYacht = Yacht.query.filter_by(id=b.id, version=b.version).first()
        assert retrievedYacht == b
        retrievedCruise = Cruise.query.filter_by(yacht_id=b.id, yacht_version=b.version).first()

        assert retrievedCruise == cruise
        assert cruise.version == retrievedCruise.version


    def test_get_role_by_cruise(self):
        """Get CRUISE by ID."""

        p = UserProfile.create(user_id = 2, first_name='Herlock', last_name='Sholmès')
        c = Cruise.get(1)
        c.passengers.append(p)
        c.save()

        retrievedRole = ProfileRole.query.filter_by(cruise_id=c.id, version=c.version, profile_id=p.id).first()

        assert retrievedRole.profile == p
        assert retrievedRole.role == Cruise.Role.PASSENGER
