# -*- coding: utf-8 -*-
"""Cruise models."""

from sqlalchemy import desc, event, select, text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.session import object_session

from . import ObjectLockedException, db
from .model import Model


class VersionedModel(Model):
    """Abstract SQLAlchemy class that adds versioning."""

    __abstract__ = True
    __table_args__ = {'extend_existing': True}

    @declared_attr
    def id(cls):  # noqa
        return db.Column(db.Integer, primary_key=True, default=select(
            [text('COALESCE(MAX(id), 0)+1 FROM ' + cls.__tablename__)]).as_scalar())

    @declared_attr
    def version(cls):  # noqa
        return db.Column(db.Integer, primary_key=True, default=0, autoincrement=False)

    is_current_version = db.Column(db.Boolean, default=True)

    @property
    def locked(self):
        """Every sub-class must define a locked property."""
        raise NotImplementedError

    unlockable = ()

    def load_current_version(self):
        """Replace instance by latest version with same id."""
        if not self.is_current_version:
            self = self.query.filter_by(id=self.id, is_current_version=True).first()

    def new_version(self, stay_old=False):
        """Create new version and set previous version to have is_current_version=False."""
        old_version = self.version
        self.load_current_version()
        db.session.query(self.__class__).filter_by(id=self.id).update(
            values=dict(is_current_version=False), synchronize_session=False
        )
        db.make_transient(self)  # make us transient (removes persistent identity).
        self.version += 1  # increment version_id, which means we have a new PK.
        db.session.add(self)
        db.session.commit()
        if stay_old:
            self = self.query.filter_by(id=self.id, version=old_version).first()
        return self

    def get_previous_versions(self):
        """Get all previous versions."""
        all_x = self.query.filter(self.__class__.id == self.id, self.__class__.version < self.version ).order_by(desc('version')).all()
        return all_x or []

    @classmethod
    def get(cls, id, version=None, fail_ns=None):
        """Get by id."""
        x = cls.query.filter_by(id=id)
        if version is None:
            x = x.order_by(desc('version'))
        else:
            x = x.filter_by(version=version)
        x = x.first()
        if x is None and fail_ns is not None:
            fail_ns.abort(404, "{} id {} doesn't exist".format(cls.__name__, id))
        return x

    @classmethod
    def get_all_versions(cls, id, fail_ns=None):
        """Get by id."""
        all_x = cls.query.filter_by(id=id).order_by(desc('version')).all()
        if (all_x is None or len(all_x) == 0) and fail_ns is not None:
            fail_ns.abort(404, "{} id {} doesn't exist".format(cls.__name__, id))
        return all_x

    @classmethod
    def get_latest_version(cls, id):
        """Get by id"""
        x = cls.query.filter_by(id=id).order_by(desc('version')).first()
        return x.version

    def delete_all_versions(self, commit=True):
        """Remove the record from the database."""
        for x in self.query.filter_by(id=self.id).all():
            db.session.delete(x)
        return commit and db.session.commit()

    def __repr__(self):
        return '<' + self.__class__.__name__ + ' id=' + str(self.id) + 'v.' + str(self.version) + '>'


def check_if_locked(mapper, connection, target):
    """Check model's locked property and raise exception if needed."""
    is_updated = object_session(target).is_modified(target, include_collections=True)
    state = db.inspect(target)
    changes = set()
    for attr in state.attrs:
        hist = state.get_history(attr.key, True)
        if hist.has_changes():
            changes.add(attr.key)
    if is_updated and changes.difference(target.unlockable) and target.locked:
        # DEBUG:
        raise ObjectLockedException(str(target) + ' is locked and cannot be modified.')


event.listen(VersionedModel, 'before_update', check_if_locked, propagate=True)


# TODO: automatically add new version when needed
# @event.listens_for(Session, "before_flush")
# def before_flush(session, flush_context, instances):
#     for instance in session.dirty:
#         if not isinstance(instance, Versioned):
#             continue
#         if not session.is_modified(instance, passive=True):
#             continue
#
#         if not attributes.instance_state(instance).has_identity:
#             continue
#
#         # make it transient
#         instance.new_version(session)
#
#         # re-add
#         session.add(instance)
