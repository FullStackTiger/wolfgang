# -*- coding: utf-8 -*-
"""
Billing models.
"""

from wolfgang.database import db
from wolfgang.database.model import Model
from wolfgang.user.models import User


class Charge(Model):
    """A charge object associated to a cruise."""

    cruise = db.relationship('Cruise')
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=True)
    user = db.relationship(User)
    amount = db.Column(db.Integer, nullable=True)
    currency = db.Column(db.String, default='usd', nullable=True)
    stripe_customer_id = db.Column(db.Integer, nullable=True)
    stripe_token = db.Column(db.String, nullable=True)
