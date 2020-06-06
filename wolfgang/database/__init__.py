"""Database package."""

from werkzeug.exceptions import HTTPException

from ..extensions import db


class ObjectLockedException(HTTPException):
    """Exception returned when SQLAlchemy tries to update a locked model."""

    pass
