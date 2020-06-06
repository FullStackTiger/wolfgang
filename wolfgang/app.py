# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
import os

from flask import Flask, render_template
from jinja2 import StrictUndefined

from wolfgang import client, commands, contract, user
from wolfgang.cruise import yacht
from wolfgang.api import api, api_blueprint
from wolfgang.cruise.resources import ns as cruise_ns  # noqa - Ensure file is loaded and endpoint added
from wolfgang.cruise.yacht.resources import ns as yacht_ns  # noqa - Ensure file is loaded and endpoint added
from wolfgang.extensions import bcrypt, cache, db, debug_toolbar, jwt, login_manager, ma, migrate, mail
from wolfgang.geo.resources import ns as geo_ns  # noqa - Ensure file is loaded and endpoint added
from wolfgang.user.resources import ns as user_ns  # noqa - Ensure file is loaded and endpoint added
from wolfgang.user.resources import user_loader_callback


def create_app(config_object=None):
    """
    An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    if config_object is None:
        raise('Config must be specified')

    # This is a workaround for Alpine Linux (musl libc) quirk:
    # https://github.com/docker-library/python/issues/211
    # import threading
    # threading.stack_size(2*1024*1024)
    app = Flask(__name__.split('.')[0])
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app)

    if app.config['DEBUG']:
        app.jinja_env.undefined = StrictUndefined  # Throw errors if missing variables

    return app


def register_extensions(app):
    """Register Flask extensions."""
    bcrypt.init_app(app)
    cache.init_app(app)
    db.init_app(app)
    ma.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    debug_toolbar.init_app(app)
    migrate.init_app(app, db)

    app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']
    jwt.init_app(app)
    jwt._set_error_handler_callbacks(api)
    # Currently, we're automatically loading User object on all token calls:
    jwt.user_loader_callback_loader(user_loader_callback)
    if app.config['DEBUG']:
        if app.config['JWT_FAKE_TOKEN']:
            import warnings
            warnings.warn('Simulating token for user: {}'.format(app.config['JWT_FAKE_TOKEN']))

            @jwt.fake_token
            def my_fake_token(request_type):
                return {'identity': app.config['JWT_FAKE_TOKEN'], 'user_claims': []}

    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    app.config['RESTPLUS_VALIDATE'] = True

    if app.config['DEBUG']:
        app.config['ERROR_404_HELP'] = True  # Appends tips to 404 messages
        if os.environ.get('WOLFGANG_CORS', False):
            @api_blueprint.after_request
            def apply_cors(response):
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Headers'] = 'content-type, authorization'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
                return response
    else:
        app.config['ERROR_404_HELP'] = False

    app.register_blueprint(api_blueprint)
    app.register_blueprint(contract.contract_bp)
    app.register_blueprint(yacht.image_bp)

    # Client Blueprint registration comes last because it includes a catch-all route on /
    app.register_blueprint(client.client_bp)

    return None


def register_errorhandlers(app):
    """Register error handlers."""
    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template('{0}.html'.format(error_code)), error_code
    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)

    return None


def register_shellcontext(app):
    """Register shell context objects."""
    def shell_context():
        """Shell context objects."""
        return {
            'db': db,
            'User': user.models.User,
        }

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)
    app.cli.add_command(commands.clean)
    app.cli.add_command(commands.urls)
    app.cli.add_command(commands.insert_dev_data)
    app.cli.add_command(commands.test_sql_queries)
