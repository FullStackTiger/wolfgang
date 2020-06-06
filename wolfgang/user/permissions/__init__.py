# encoding: utf-8
"""
RESTful API permissions.
"""
import logging

from flask_sqlalchemy import BaseQuery
from permission import Permission as BasePermission

from . import rules


log = logging.getLogger(__name__)


class PermissionExtendedQuery(BaseQuery):
    """
    Extends BaseQuery class from flask_sqlalchemy to add get_or_403 method.

    Example:
    >>> DataTransformation.query.get_or_403(id)
    """

    def __init__(self, permisssion, *args, **kwargs):
        """Adds permission to BaseQuery."""
        super().__init__(*args, **kwargs)
        self.permisssion = permisssion

    def get_or_403(self, ident):
        """Fails with 403 error if required permission not fulfillled."""
        obj = self.get_or_404(ident)
        with self.permisssion(obj=obj):
            return obj


class Permission(BasePermission):
    """Provides extended BaseQuery to model, which adds additional method get_or_403."""

    @classmethod
    def get_query_class(cls):
        """
        Returns extended BaseQuery class for flask_sqlalchemy model to provide get_or_403 method.

        Example:
        >>> DataTransformation(db.Model):
        ...     query_class = OwnerRolePermission.get_query_class()
        """
        return lambda *args, **kwargs: PermissionExtendedQuery(cls, *args, **kwargs)


class PasswordRequiredPermissionMixin(object):
    """
    Mixin rule that checks for password.
    """

    def __init__(self, password_required=False, password=None, **kwargs):
        # NOTE: kwargs is required since it is a mixin
        """
        Ensure user password is correct if `password_required` is set to True.

        Args:
            password_required (bool) - in some cases you may need to ask
                users for a password to allow certain actions, enforce this
                requirement by setting this :bool:`True`.
            password (str) - pass a user-specified password here.
        """
        self._password_required = password_required
        self._password = password
        super(PasswordRequiredPermissionMixin, self).__init__(**kwargs)

    def rule(self):  # noqa
        _rule = super(PasswordRequiredPermissionMixin, self).rule()
        if self._password_required:
            _rule &= rules.PasswordRequiredRule(self._password)
        return _rule


class WriteAccessPermission(Permission):
    """
    User must be logged-in and have write access to the resource.
    """

    def __init__(self, obj=None, **kwargs):
        """
        Stores target object to check for permissions.

        Args:
            obj (object) - any object can be passed here, which will be asked
                via ``check_owner(current_user)`` method whether a current user
                has enough permissions to perform an action on the given
                object.
        """
        self._obj = obj
        super().__init__(**kwargs)

    def rule(self):  # noqa
        return rules.AdminRoleRule() | rules.WriteAccessRule(self._obj)


class ReadAccessPermission(Permission):
    """User must be logged-in and have read access to the resource."""

    def __init__(self, obj=None, **kwargs):
        """
        Stores target object to check for permissions.

        Args:
            obj (object) - any object can be passed here, which will be asked
                via ``check_owner(current_user)`` method whether a current user
                has enough permissions to perform an action on the given
                object.
        """
        self._obj = obj
        super().__init__(**kwargs)

    def rule(self):  # noqa
        return rules.AdminRoleRule() | rules.ReadAccessRule(self._obj)


class RolePermission(Permission):
    """This class aims to help distinguish all role-type permissions."""

    def __init__(self, partial=False, **kwargs):
        """
        Assigns permission as partial.

        Args:
            partial (bool) - True values is mostly useful for Swagger
                documentation purposes.
        """
        self._partial = partial
        super().__init__(**kwargs)

    def rule(self):  # noqa
        if self._partial:
            return rules.PartialPermissionDeniedRule()
        return rules.AllowAllRule()


class ActiveUserRolePermission(RolePermission):
    """Request must contain a token for an active user."""

    def rule(self):  # noqa
        return rules.ActiveUserRoleRule()


class AdminRolePermission(RolePermission):
    """User must be Admin."""

    def rule(self):  # noqa
        return rules.AdminRoleRule()


class WriteAccessWithPasswordPermission(PasswordRequiredPermissionMixin, RolePermission):
    """User must have write access and provide current password."""

    def __init__(self, obj=None, **kwargs):
        """
        Stores target object.

        Args:
            obj (object) - any object can be passed here, which will be asked
                via ``check_owner(current_user)`` method whether a current user
                has enough permissions to perform an action on the given
                object.
        """
        self._obj = obj
        super().__init__(**kwargs)

    def rule(self):  # noqa
        return (rules.AdminRoleRule() | rules.WriteAccessRule())
