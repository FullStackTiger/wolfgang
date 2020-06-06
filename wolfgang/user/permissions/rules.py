# encoding: utf-8
"""
RESTful API Rules.
"""
from http import HTTPStatus

from flask_jwt_extended import current_user, get_jwt_identity, jwt_optional
from permission import Rule as BaseRule

from wolfgang.api import abort


class DenyAbortMixin(object):
    """
    Helper permissions mixin raising HTTP Error on deny.

    NOTE: Apply this mixin before Rule class so it can override NotImplemented
    deny method.
    """

    DENY_ABORT_HTTP_CODE = HTTPStatus.FORBIDDEN
    DENY_ABORT_MESSAGE = None

    def deny(self):
        """
        Abort HTTP request by raising HTTP exception with specified HTTP code.
        """
        return abort(code=self.DENY_ABORT_HTTP_CODE, message=self.DENY_ABORT_MESSAGE)


class Rule(BaseRule):
    """
    Experimental Base Rule class: automatically handles inherited rules.

    Without having to call parent manually inside base()
    """

    def base(self):
        """
        Automatically calls the first appropriate parent classself.

        (converts class inheritance to rule inheritance)
        """
        for base_class in self.__class__.__bases__:
            if issubclass(base_class, Rule):
                if base_class in {Rule, BaseRule}:
                    continue
                return base_class()


class AllowAllRule(Rule):
    """Helper rule that always grants access."""

    def check(self):  # noqa
        return True


class ValidTokenRule(DenyAbortMixin, Rule):
    """Request must contain a valid token."""

    DENY_ABORT_HTTP_CODE = HTTPStatus.UNAUTHORIZED
    DENY_ABORT_MESSAGE = 'You need to be logged-in to perform this action'

    # @jwt_required ## Uncomment to get specific JWT error messages during debug
    @jwt_optional
    def check(self):  # noqa
        current_user = get_jwt_identity()
        return (current_user != None)


class ActiveUserRoleRule(ValidTokenRule):
    """User account must have is_active = True."""

    DENY_ABORT_HTTP_CODE = HTTPStatus.UNAUTHORIZED
    DENY_ABORT_MESSAGE = 'You need to be logged in with an active user account to perform this action'

    def check(self):  # noqa
        return current_user.is_active


class PasswordRequiredRule(DenyAbortMixin, Rule):
    """Ensure that the current user has provided a correct password."""

    DENY_ABORT_MESSAGE = 'Incorrect password'

    def __init__(self, password, **kwargs):
        """Stores password to check against current_user's."""
        super().__init__(**kwargs)
        self._password = password

    def check(self):  # noqa
        return current_user.is_password_correct(self._password)


class AdminRoleRule(ActiveUserRoleRule):
    """
    current_user must have an Admin role.
    """

    DENY_ABORT_MESSAGE = 'Only Admin users can access this endpoint'

    def check(self):  # noqa
        return current_user.is_admin


class PartialPermissionDeniedRule(Rule):
    """Helper rule that must fail on every check since it should never be checked."""

    def check(self):  # noqa
        raise RuntimeError('Partial permissions are not intended to be checked')


class WriteAccessRule(ActiveUserRoleRule):
    """
    Current user must have write access to the given object.
    """

    DENY_ABORT_MESSAGE = 'You are not allowed to modify this resource'

    def __init__(self, obj, **kwargs):
        """Stores target object to check permissions for."""
        super().__init__(**kwargs)
        self._obj = obj

    def check(self):  # noqa
        if not hasattr(self._obj, 'check_write_access'):
            return False
        return self._obj.check_write_access(current_user) is True


class ReadAccessRule(ActiveUserRoleRule):
    """Current user must have read access to the given object."""

    DENY_ABORT_MESSAGE = 'You are not allowed to view this resource'

    def __init__(self, obj, **kwargs):
        """Stores target object to check permissions for."""
        super().__init__(**kwargs)
        self._obj = obj

    def check(self):  # noqa
        if not hasattr(self._obj, 'check_read_access'):
            return False
        return self._obj.check_read_access(current_user) is True
