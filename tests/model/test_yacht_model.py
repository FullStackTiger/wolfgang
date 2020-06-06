# -*- coding: utf-8 -*-
"""Model unit tests."""
import datetime as dt

import pytest

from wolfgang.cruise.yacht.models import Yacht

@pytest.mark.usefixtures('populated_db')
class TestYachtModel:
    """Yacht model unit tests."""

    def test_get_by_id(self):
        """Get user by ID."""
        yacht = Yacht.create(name='yachtox', imo_nb='007', type=Yacht.Type.SAIL)
        retrieved = Yacht.get(yacht.id)
        assert retrieved == yacht
        yacht.delete()
