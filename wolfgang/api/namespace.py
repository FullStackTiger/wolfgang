# encoding: utf-8
"""
Extended Api Namespace implementation with an application-specific helpers.
"""
import logging
from contextlib import contextmanager
from functools import wraps
from http import HTTPStatus

import flask_marshmallow
import sqlalchemy

from wolfgang.flask_restplus_plus import Namespace as BaseNamespace

from . import http_exceptions
from .webargs_parser import CustomWebargsParser


log = logging.getLogger(__name__)


class Namespace(BaseNamespace):
    """
    Having app-specific handlers here.
    """

    WEBARGS_PARSER = CustomWebargsParser()

    _sqla_models = {}

    def param(self, *args, **kwargs):
        """
        Customised @ns.param decorator that registers an associated object.
        """
        if 'sqla_model' in kwargs:
            model = kwargs.pop('sqla_model')
            if 'sqla_instance_name' in kwargs:
                instance_name = kwargs.pop('sqla_instance_name')
            else:
                instance_name = model.__tablename__[:-1] if model.__tablename__[-1] == 's' else model.__tablename__

            self._sqla_models[args[0]] = (model, instance_name)
            # print(self._sqla_models)
        return super().param(*args, **kwargs)

    def resolve_arg(self, route_arg):
        """Resolves single route_arg."""
        return self.resolve_args([route_arg])

    def resolve_args(self, route_args):
        """Resolves route_args (eg 'user_id' becomes object 'user')."""
        if callable(route_args):
            func = route_args
            route_args = None
        else:
            func = None
        # TODO: see if this can work despite sharing all models across the namespace…
        # if route_args is None:
        #     route_args = self._sqla_models.keys()
        for arg_name in route_args:
            if type(arg_name) is list or type(arg_name) is tuple:
                obj = self._sqla_models[arg_name[0]]
            else:
                obj = self._sqla_models[arg_name]
            func_wrap = self.resolve_object_by_model(model=obj[0], object_arg_name=obj[1], identity_arg_names=arg_name)
            if func is None:
                func = func_wrap
            else:
                func = func_wrap(func)
        return func

    def resolve_object_by_model(self, model, object_arg_name, identity_arg_names=None):
        """
        A helper decorator to resolve DB record instance by id.

        Arguments:
            model (type) - a Flask-SQLAlchemy model class with
                ``query.get_or_404`` method
            object_arg_name (str) - argument name for a resolved object
            identity_arg_names (tuple) - a list of argument names holding an
                object identity, by default it will be auto-generated as
                ``%(object_arg_name)s_id``.

        Example:
        >>> @namespace.resolve_object_by_model(User, 'user')
        ... def get_user_by_id(user):
        ...     return user
        >>> get_user_by_id(user_id=3)
        <User(id=3, ...)>

        >>> @namespace.resolve_object_by_model(MyModel, 'my_model', ('user_id', 'model_name'))
        ... def get_object_by_two_primary_keys(my_model):
        ...     return my_model
        >>> get_object_by_two_primary_keys(user_id=3, model_name="test")
        <MyModel(user_id=3, name="test", ...)>
        """
        if identity_arg_names is None:
            identity_arg_names = ('%s_id' % object_arg_name, )
        elif not isinstance(identity_arg_names, (list, tuple)):
            identity_arg_names = (identity_arg_names, )

        return self.resolve_object(
            object_arg_name,
            resolver=lambda kwargs: model.get(
                *[kwargs.pop(identity_arg_name) for identity_arg_name in identity_arg_names],
                fail_ns=self
            )
        )

    def resolve_object(self, object_arg_name, resolver, force_resolve=False):
        """
        Helper decorator to resolve object instance from arguments (e.g. identity).

        Override from parent that skips if object_arg_name is already set
        (unless force_resolve = True)

        Example:
        >>> @namespace.route('/<int:user_id>')
        ... class MyResource(Resource):
        ...    @namespace.resolve_object(
        ...        object_arg_name='user',
        ...        resolver=lambda kwargs: User.query.get_or_404(kwargs.pop('user_id'))
        ...    )
        ...    def get(self, user):
        ...        # user is a User instance here
        """
        def decorator(func_or_class):
            if isinstance(func_or_class, type):
                # Handle Resource classes decoration
                # pylint: disable=protected-access
                func_or_class._apply_decorator_to_methods(decorator)
                return func_or_class

            @wraps(func_or_class)
            def wrapper(*args, **kwargs):
                # If object has been already resolved, skip:
                if force_resolve or (object_arg_name not in kwargs.keys()):
                    kwargs[object_arg_name] = resolver(kwargs)
                return func_or_class(*args, **kwargs)
            return wrapper
        return decorator

    def model(self, name=None, model=None, **kwargs):
        # pylint: disable=arguments-differ
        """
        Decorator which registers a model (aka schema / definition).

        This extended implementation auto-generates a name for
        ``Flask-Marshmallow.Schema``-based instances by using a class name
        with stripped off `Schema` prefix.
        """
        if isinstance(model, flask_marshmallow.Schema) and not name:
            name = model.__class__.__name__
            if name.endswith('Schema'):
                name = name[:-len('Schema')]
        return super().model(name=name, model=model, **kwargs)

    def permission_required(self, permission, kwargs_on_request=None, arg_name='resource', target_id=None):
        """
        A decorator which restricts access for users with specific permissions only.

        This decorator puts together permissions restriction code with OpenAPI
        Specification documentation.

        Arguments:
            permission (Permission) - it can be a class or an instance of
                :class:``Permission``, which will be applied to a decorated
                function, and docstrings of which will be used in OpenAPI
                Specification.
            kwargs_on_request (func) - a function which should accept only one
                ``dict`` argument (all kwargs passed to the function), and
                must return a ``dict`` of arguments which will be passed to
                the ``permission`` object.

        Example:
        >>> @namespace.permission_required(
        ...     OwnerRolePermission,
        ...     kwargs_on_request=lambda kwargs: {'obj': kwargs['team']}
        ... )
        ... def get_team(team):
        ...     # This line will be reached only if OwnerRolePermission check
        ...     # is passed!
        ...     return team
        """
        if target_id:
            if type(target_id) is not list and type(target_id) is not tuple:
                target_ids = (target_id,)
            else:
                target_ids = target_id
        else:
            target_ids = None

        def decorator(func):
            """A helper wrapper."""
            if getattr(permission, '_partial', False):
                # We don't apply partial permissions, we only use them for
                # documentation purposes.
                protected_func = func
            else:
                if target_ids:
                    # TODO: make resolution optional
                    if target_ids[0] not in self._sqla_models.keys():
                        raise(
                            BaseException(
                                'Model for {} must be registered with @namespace.param before you can use it in permissions'.format(target_ids[0])))  # noqa
                    sqla_model = self._sqla_models[target_ids[0]]

                    def _permission_decorator(func):
                        @wraps(func)
                        @self.resolve_arg(target_ids)
                        def wrapper(*args, **kwargs):
                            with permission(obj=kwargs[sqla_model[1]]):
                                return func(*args, **kwargs)
                        return wrapper
                elif not kwargs_on_request:
                    _permission_decorator = permission()
                else:
                    def _permission_decorator(func):
                        @wraps(func)
                        def wrapper(*args, **kwargs):
                            with permission(**kwargs_on_request(kwargs)):
                                return func(*args, **kwargs)
                        return wrapper

                protected_func = _permission_decorator(func)
                self._register_access_restriction_decorator(protected_func, _permission_decorator)

            # Apply `_role_permission_applied` marker for Role Permissions,
            # so don't apply unnecessary permissions in `login_required`
            # decorator.
            #
            # TODO: Change this behaviour when implement advanced OPTIONS
            # method support
            # if (
            #         isinstance(permission, permissions.RolePermission)
            #         or
            #         (
            #             isinstance(permission, type)
            #             and
            #             issubclass(permission, permissions.RolePermission)
            #         )
            # ):
            #     protected_func._role_permission_applied = True  # pylint: disable=protected-access

            permission_description = permission.__doc__.strip()

            return self.doc(
                description='**Permissions: %s**\n\n' % permission_description
            )(
                self.response(
                    code=HTTPStatus.FORBIDDEN.value,
                    description=permission_description,
                )(protected_func)
            )
        return decorator

    def _register_access_restriction_decorator(self, func, decorator_to_register):
        # pylint: disable=invalid-name
        """
        Register decorator to perform checks in options method.
        """
        if not hasattr(func, '_access_restriction_decorators'):
            func._access_restriction_decorators = []  # pylint: disable=protected-access
        func._access_restriction_decorators.append(decorator_to_register)  # pylint: disable=protected-access

    @contextmanager
    def commit_or_abort(self, session, default_error_message='The operation failed to complete'):
        """
        Context manager to simplify a workflow in resources.

        Args:
            session: db.session instance
            default_error_message: Custom error message

        Exampple:
        >>> with api.commit_or_abort(db.session):
        ...     team = Team(**args)
        ...     db.session.add(team)
        ...     return team
        """
        try:
            with session.begin():
                yield
        except ValueError as exception:
            log.info('Database transaction was rolled back due to: %r', exception)
            http_exceptions.abort(code=HTTPStatus.CONFLICT, message=str(exception))
        except sqlalchemy.exc.IntegrityError as exception:
            log.info('Database transaction was rolled back due to: %r', exception)
            http_exceptions.abort(
                code=HTTPStatus.CONFLICT,
                message=default_error_message
            )
