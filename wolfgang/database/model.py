# -*- coding: utf-8 -*-
"""Database module, including the SQLAlchemy database object and DB-related utilities."""

import datetime as dt
import re

from flask_jwt_extended import current_user
from sqlalchemy.ext.declarative import declared_attr

from . import db


class Model(db.Model):
    """Base model class that includes CRUD and PK id convenience methods."""

    __abstract__ = True
    __table_args__ = {'extend_existing': True}

    @declared_attr
    def __tablename__(cls):  # noqa
        """Automatically assigns snake-case version of class name (plus optional 's') as tablename."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        snake_case_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        return (snake_case_name + ('s' if snake_case_name[-1] != 's' else ''))

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    @property
    def write_access(self):
        """Check if current user has write access to resource."""
        if current_user == None:
            return False
        return self.check_write_access(current_user)

    @classmethod
    def c(cls):
        """Shortcut to table column list."""
        return cls.__table__.c

    # @classmethod
    # def get_by_id(cls, record_id):
    #     """Get record by ID."""
    #     if any(
    #             (isinstance(record_id, (str, bytes)) and record_id.isdigit(),
    #              isinstance(record_id, (int, float))),
    #     ):
    #         return cls.query.get(int(record_id))
    #     return None

    @classmethod
    def create(cls, **kwargs):
        """Create a new record and save it the database."""
        instance = cls(**kwargs)
        return instance.save()

    @classmethod
    def get(cls, id, fail_ns=None):
        """Get by id."""
        x = cls.query.filter_by(id=id).first()
        if x is None and fail_ns is not None:
            fail_ns.abort(404, "{} id {} doesn't exist".format(cls.__name__, id))
        return x

    @classmethod
    def get_by(cls, fail_ns=None, **kwargs):
        """Get by arbitrary field."""
        x = cls.query.filter_by(**kwargs).first()
        if x is None and fail_ns is not None:
            fail_ns.abort(404, "Resource doesn't exist")
        return x

    def update(self, commit=True, **kwargs):
        """Update specific fields of a record."""
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return self.save(commit=commit)

    def save(self, commit=True):
        """Save the record."""
        db.session.add(self)
        # TODO: should we use db.session.merge() to ensure no other instance exists?
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        """Remove the record from the database."""
        db.session.delete(self)
        return commit and db.session.commit()

    def check_write_access(self, by_user):
        """Default read access: if object is tied to user."""
        if hasattr(self, 'user_id'):
            return self.user_id and (self.user_id == by_user.id)
        else:
            return False

    def check_read_access(self, by_user):
        """Default read access: same as write access."""
        return self.check_write_access(by_user)

    def __repr__(self):
        return '<' + self.__class__.__name__ + ' id=' + str(self.id) + '>'


def reference_col(tablename, nullable=False, pk_name='id', **kwargs):
    """
    Column that adds primary key foreign key reference.

    Usage:: :

        category_id = reference_col('category')
        category = db.relationship('Category', backref='categories')
    """
    return db.Column(
        db.ForeignKey('{0}.{1}'.format(tablename, pk_name)),
        nullable=nullable, **kwargs)
