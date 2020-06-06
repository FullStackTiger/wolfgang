# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""
from math import asin, cos, radians, sin, sqrt

from flask import flash
from marshmallow_enum import EnumField


def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash('{0} - {1}'.format(getattr(form, field).label.text, error), category)


class EnumFieldPlus(EnumField):
    """Customised EnumField class that adds description."""

    def __init__(self, *pargs, **kwargs):
        """Insert description."""
        cls = pargs[0]
        description = kwargs.pop('description', None)
        if description is None:
            description = ' | '.join([x.name for x in cls])
        super().__init__(*pargs, description=description, **kwargs)


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate distance between two points on earth (specified in decimal degrees).
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles
    return c * r
