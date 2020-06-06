# -*- coding: utf-8 -*-
"""Click commands."""
import os
from glob import glob
from subprocess import call

import click
from flask import current_app
from flask.cli import with_appcontext
from flask.helpers import get_debug_flag
from werkzeug.exceptions import MethodNotAllowed, NotFound


HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.join(HERE, os.pardir)
TEST_PATH = os.path.join(PROJECT_ROOT, 'tests')


@click.command()
@with_appcontext
def test_sql_queries():
    """Playground for SQL queries."""
    if not get_debug_flag():
        click.echo('You need to set FLASK_DEBUG=1 to run this command')
        exit(1)

    import logging
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    from wolfgang.cruise.models import Cruise

    c = Cruise.get(1)
    click.echo(c)
    click.echo(c.roles)
    click.echo(c.passengers)
    click.echo(c.captains)


@click.command()
@with_appcontext
def insert_dev_data():
    """Inserts test data in dev mode."""
    if not get_debug_flag():
        click.echo('You need to set FLASK_DEBUG=1 to run this command')
        exit(1)

    # from wolfgang.cruise.models import Test
    # t = Test.create(**{'junk': '12345'})
    # click.echo(t)
    from datetime import datetime
    from wolfgang.database import db
    from wolfgang.user.models import User, UserProfile
    from wolfgang.cruise.models import Cruise, ProfileRole
    from wolfgang.cruise.yacht.models import Yacht
    from wolfgang.cruise.waypoint.models import Waypoint
    from wolfgang.geo.models import Geoname

    click.echo('Delete all Cruises- and User- related rows…')
    for w in Waypoint.query.all():
        w.delete()
    for c in Cruise.query.all():
        c.delete()
    for u in User.query.all():
        u.delete()
    for b in Yacht.query.all():
        b.delete()
    db.session.commit()

    p = UserProfile(first_name='God', last_name='Admin', is_main=True)
    u = User.create(email='admin@admin.com', password='admin', main_profile=p, is_admin=True)
    click.echo('Created admin user:')
    click.echo(u)

    u = User.create(email='arsene@lupin.com', password='test')
    p1 = UserProfile(first_name='Raoul', last_name="d'Andresy", date_of_birth=datetime(1874, 7, 14), is_main=True)
    u.profiles.append(p1)
    u.save()
    click.echo(u)
    click.echo(u.profiles)
    p1.new_version()
    p1.first_name = 'Arsène'
    p1.last_name = 'Lupin'
    p1.save()
    p2 = UserProfile(first_name='Paul', last_name='Sernine', is_main=False)
    u.profiles.append(p2)
    u.save()
    click.echo(u)
    click.echo(u.profiles)

    u = User.create(email='sherlock@holmes.com', password='test')
    p1 = UserProfile(first_name='Sherlock', last_name='Holmes')
    u.profiles.append(p1)
    u.save()
    click.echo(u)
    click.echo(u.profiles)
    p1.new_version()
    p1.update(first_name='Herlock', last_name='Sholmès')  # automatically calls save()
    u = User.get(u.id)
    click.echo(u)
    click.echo(u.profiles)

    u = User.create(email='stake@holder.com', password='test')
    p3 = UserProfile(first_name='John', last_name='Stakeholder')
    u.profiles.append(p3)
    u.save()

    u1 = User.get(2)
    u2 = User.get(3)
    u3 = User.get(4)

    # Create contacts for u1
    anon_p = UserProfile(first_name='Robert', last_name='Neverconnected')
    User.create(email='not@connected.com', main_profile=anon_p)
    u1.main_profile.add_contact(anon_p).save()
    u1.main_profile.add_contact(u2.main_profile).save()

    loc = Geoname.get(6447142)
    if loc is None:
        click.echo('********\nGeoname data has not been loaded in the DB. Aborting.\n')
        return

    b1 = Yacht.create(name="L'As de Pique", creator=u1, port_of_registry=loc, type=Yacht.Type.SAIL)
    loc = Geoname.get(2993457)
    b2 = Yacht.create(name='Le Sept-de-coeur', creator=u1, port_of_registry=loc)
    c = Cruise.create(creator=u1)
    Waypoint.create(cruise=c, is_call=True, latitude=loc.latitude, longitude=loc.longitude, geoname=loc,
                    arr_date=datetime(2018, 5, 15, 20, 00, 00), dep_date=datetime(2018, 5, 15, 20, 00, 00))
    Waypoint.create(cruise=c, is_call=False, latitude=loc.latitude + 0.01, longitude=loc.longitude + 0.01,
                    arr_date=datetime(2018, 5, 16, 20, 00, 00), dep_date=datetime(2018, 5, 16, 20, 00, 00))
    Waypoint.create(cruise=c, is_call=True, latitude=loc.latitude + 0.02, longitude=loc.longitude - 0.01,
                    arr_date=datetime(2018, 5, 17, 10, 00, 00), dep_date=datetime(2018, 5, 17, 20, 00, 00))
    Waypoint.create(cruise=c, is_call=True, latitude=loc.latitude, longitude=loc.longitude,
                    geoname=loc, arr_date=datetime(2018, 5, 18, 14, 00, 00),
                    dep_date=datetime(2018, 5, 18, 14, 00, 00))  # out of chronological order
    Waypoint.create(cruise=c, is_call=False, latitude=loc.latitude + 0.01, longitude=loc.longitude - 0.01,
                    arr_date=datetime(2018, 5, 18, 10, 00, 00), dep_date=datetime(2018, 5, 18, 10, 00, 00))

    # Different ways of adding roles:
    # r = ProfileRole.create(cruise_id=c.id, profile_id=p1.id, profile_version=p1.version, role=Cruise.Role.PASSENGER)
    r = ProfileRole.create(cruise_id=c.id, profile=u1.main_profile, role=Cruise.Role.BROKER)
    c.roles.append(r)

    c.stakeholders.append(u3.main_profile)

    c.passengers.append(u2.main_profile)
    c.passengers.append(p2)
    c.yacht = b1
    c.save()
    click.echo(c)
    click.echo('Captains:')
    click.echo(c.captains)
    click.echo('Passengers:')
    click.echo(c.passengers)
    click.echo('Stakeholders:')
    click.echo(c.stakeholders)
    click.echo(c.yacht)
    click.echo('Cruise waypoints')
    click.echo(c.waypoints)

    c = Cruise.create(creator=u1, yacht=b2)  # Second cruise


@click.command()
def test():
    """Run the tests."""
    import pytest
    rv = pytest.main([TEST_PATH, '--verbose'])
    exit(rv)


@click.command()
@click.option('-f', '--fix-imports', default=False, is_flag=True,
              help='Fix imports using isort, before linting')
def lint(fix_imports):
    """Lint and check code style with flake8 and isort."""
    skip = ['node_modules', 'requirements']
    root_files = glob('*.py')
    root_directories = [
        name for name in next(os.walk('.'))[1] if not name.startswith('.')]
    files_and_directories = [
        arg for arg in root_files + root_directories if arg not in skip]

    def execute_tool(description, *args):
        """Execute a checking tool with its arguments."""
        command_line = list(args) + files_and_directories
        click.echo('{}: {}'.format(description, ' '.join(command_line)))
        rv = call(command_line)
        if rv != 0:
            exit(rv)

    if fix_imports:
        execute_tool('Fixing import order', 'isort', '-rc')
    execute_tool('Checking code style', 'flake8')


@click.command()
def clean():
    """Remove *.pyc and *.pyo files recursively starting at current directory.

    Borrowed from Flask-Script, converted to use Click.
    """
    for dirpath, dirnames, filenames in os.walk('.'):
        for filename in filenames:
            if filename.endswith('.pyc') or filename.endswith('.pyo'):
                full_pathname = os.path.join(dirpath, filename)
                click.echo('Removing {}'.format(full_pathname))
                os.remove(full_pathname)


@click.command()
@click.option('--url', default=None,
              help='Url to test (ex. /static/image.png)')
@click.option('--order', default='rule',
              help='Property on Rule to order by (default: rule)')
@with_appcontext
def urls(url, order):
    """Display all of the url matching routes for the project.

    Borrowed from Flask-Script, converted to use Click.
    """
    rows = []
    column_length = 0
    column_headers = ('Rule', 'Endpoint', 'Arguments')

    if url:
        try:
            rule, arguments = (
                current_app.url_map
                           .bind('localhost')
                           .match(url, return_rule=True))
            rows.append((rule.rule, rule.endpoint, arguments))
            column_length = 3
        except (NotFound, MethodNotAllowed) as e:
            rows.append(('<{}>'.format(e), None, None))
            column_length = 1
    else:
        rules = sorted(
            current_app.url_map.iter_rules(),
            key=lambda rule: getattr(rule, order))
        for rule in rules:
            rows.append((rule.rule, rule.endpoint, None))
        column_length = 2

    str_template = ''
    table_width = 0

    if column_length >= 1:
        max_rule_length = max(len(r[0]) for r in rows)
        max_rule_length = max_rule_length if max_rule_length > 4 else 4
        str_template += '{:' + str(max_rule_length) + '}'
        table_width += max_rule_length

    if column_length >= 2:
        max_endpoint_length = max(len(str(r[1])) for r in rows)
        # max_endpoint_length = max(rows, key=len)
        max_endpoint_length = (
            max_endpoint_length if max_endpoint_length > 8 else 8)
        str_template += '  {:' + str(max_endpoint_length) + '}'
        table_width += 2 + max_endpoint_length

    if column_length >= 3:
        max_arguments_length = max(len(str(r[2])) for r in rows)
        max_arguments_length = (
            max_arguments_length if max_arguments_length > 9 else 9)
        str_template += '  {:' + str(max_arguments_length) + '}'
        table_width += 2 + max_arguments_length

    click.echo(str_template.format(*column_headers[:column_length]))
    click.echo('-' * table_width)

    for row in rows:
        click.echo(str_template.format(*row[:column_length]))
