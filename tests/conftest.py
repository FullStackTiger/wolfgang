# -*- coding: utf-8 -*-
"""Defines fixtures available to all tests."""

from http import HTTPStatus
import pytest
import json
import requests
import secrets
import string

from flask_jwt_extended import current_user

from wolfgang.app import create_app
from wolfgang.database import db as _db
from wolfgang.settings import TestConfig

from .factories import UserFactory

from wolfgang.user.models import User, UserProfile

@pytest.fixture
def app():
    """An application for the tests."""
    _app = create_app(TestConfig)
    ctx = _app.test_request_context()
    ctx.push()
    print('Creating App')
    yield _app
    ctx.pop()


@pytest.fixture
def db(app):
    """A database for the tests."""
    _db.app = app
    with app.app_context():
        _db.create_all()
        _db.session.commit()
    print('Creating Test DB')

    yield _db

    print('Destroying Test DB')
    # Explicitly close DB connection
    _db.session.close()
    _db.drop_all()

@pytest.fixture
def rest_client(client, db):
    """A fixture that return a usable rest client."""
    class RestClient:
        access_token = None
        authenticated_email = None

        def __init__(self, client, db):
            # self.server_url = 'http://127.0.0.1:5000'
            self._client = client
            self._db = db

        def get_headers(self, use_auth):
            headers = {'Content-type': 'application/json'}
            if use_auth and self.access_token:
                # print("Using token")
                headers['Authorization'] = 'Bearer ' + self.access_token
            return headers

        def logout(self):
            self.access_token = None
            self.authenticated_email = None

        def authenticate(self, email, password, force=False):
            if email == self.authenticated_email and not force:
                return
            data = {'email':email, 'password':password}
            response = self.post('/api/user/login', data)
            assert response.status_code == HTTPStatus.OK
            self.access_token = response.dict['access_token']
            self.authenticated_email = email
            return response

        def rest_call(self, method, url, data = None, decode_json_response = True, use_auth=True):
            print(method + ' ' + url)
            self._db.session.expunge_all()
            headers = self.get_headers(use_auth)
            response = self._client.open(path=url, method=method, headers=headers, data=json.dumps(data))
            if decode_json_response:
                response.dict = self.json_of_response(response, url)
            return response

        def rest_call_test_auth(self, cmd, *pargs, **kwargs):
            """Checks that endpoint requires authentication"""
            response = self.rest_call(cmd, *pargs, **kwargs, use_auth=False)
            assert response.status_code == HTTPStatus.UNAUTHORIZED
            return self.rest_call(cmd, *pargs, **kwargs, use_auth=True)

        def post_test_auth(self, *pargs, **kwargs):
            return self.rest_call_test_auth('POST', *pargs, **kwargs)

        def post(self, *pargs, **kwargs):
            return self.rest_call('POST', *pargs, **kwargs)

        def get_test_auth(self, *pargs, **kwargs):
            return self.rest_call_test_auth('GET', *pargs, **kwargs)

        def get(self, *pargs, **kwargs):
            return self.rest_call('GET', *pargs, **kwargs)

        def put_test_auth(self, *pargs, **kwargs):
            return self.rest_call_test_auth('PUT', *pargs, **kwargs)

        def put(self, *pargs, **kwargs):
            return self.rest_call('PUT', *pargs, **kwargs)

        def delete_test_auth(self, *pargs, **kwargs):
            return self.rest_call_test_auth('DELETE', *pargs,  decode_json_response = False, **kwargs)

        def delete(self, *pargs, **kwargs):
            return self.rest_call('DELETE', *pargs, decode_json_response = False, **kwargs)

        def json_of_response(self, response, url):
            """Decode json from response"""
            try:
                dict = json.loads(response.data.decode('utf8'))
            except ValueError:
                print(response.data.decode('utf8'))
                print('Query did not return JSON (endpoint URL <{}> might not be valid)'.format(url))
                dict = None
            assert dict is not None
            return dict
    print("Creating restclient")
    return(RestClient(client, db))

@pytest.fixture
def auth_rest_client(populated_db, rest_client):
    print("Authenticating")
    rest_client.authenticate(populated_db.main_email, populated_db.main_password)
    return(rest_client)


# @pytest.fixture
# def test_user(db):
#     """A fixture that returns info for a specially created user (with clear password)."""
#
#     password = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(20)) # for a 20-character password
#     email = 'test@test.com'
#     endpoint_url = '/api/user/'
#     first_name = 'John'
#     last_name = 'Tester'
#
#     data = {'email':email, 'password':password, 'first_name':first_name, 'last_name':last_name}
#     # response = rest_client.post(endpoint_url, data)
#     u = User.create(email=data['email'], password=data['password'])
#     p = UserProfile.create(first_name=data['first_name'], last_name=data['last_name'], is_main=True, user=u)
#
#     yield Bunch(**data, id=u.id, user=u)
#
#     u.delete()

@pytest.fixture
def generate_pwd():
    def fn():
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(20)) # for a 20-character password
    return fn

@pytest.fixture
def populated_db(db, generate_pwd):
    objects = populate_db(db, generate_pwd, print_fn=lambda x:x)
    print("Populating DB")
    yield objects

def populate_db(db, generate_pwd, print_fn = print):
    from wolfgang.user.models import User, UserProfile
    from wolfgang.cruise.models import Cruise, ProfileRole
    from wolfgang.cruise.yacht.models import Yacht
    import datetime

    p = UserProfile(first_name='God', last_name='Admin', is_main=True)
    u = User.create(email="admin@admin.com", password='admin', main_profile=p, is_admin=True)
    print_fn("Created admin user:")
    print_fn(u)

    main_password = generate_pwd()
    main_email = 'arsene@lupin.com'
    u = User.create(email=main_email, password=main_password)
    main_user = u
    p1 = UserProfile(first_name='Arsène', last_name='Lupin', is_main=True)
    u.profiles.append(p1)
    u.save()
    print_fn(u)
    print_fn(u.profiles)
    p1.new_version()
    p1.last_name = 'Dupont'
    p1.save()
    p2 = UserProfile(first_name='Raoul', last_name="d'Andresy", is_main=False)
    u.profiles.append(p2)
    u.save()
    print_fn(u)
    print_fn(u.profiles)

    u = User.create(email="sherlock@holmes.com", password='test')
    p1 = UserProfile(first_name='Sherlock', last_name='Holmes')
    u.profiles.append(p1)
    u.save()
    print_fn(u)
    print_fn(u.profiles)
    p1.new_version()
    p1.update(first_name='Herlock', last_name='Sholmès') # automatically calls save()
    u = User.get(u.id)
    print_fn(u)
    print_fn(u.profiles)

    u1 = User.get(2)
    u2 = User.get(3)

    st = datetime.datetime.utcnow()
    b = Yacht.create(name="Le Sept-de-coeur", creator=u2)
    c = Cruise.create(creator=u1)

    ##Different ways of adding roles:
    # r = ProfileRole.create(cruise_id=c.id, profile_id=p1.id, profile_version=p1.version, role=Cruise.Role.PASSENGER)
    r = ProfileRole.create(cruise_id=c.id, profile=u1.main_profile, role=Cruise.Role.CAPTAIN)
    c.roles.append(r)
    c.passengers.append(u2.main_profile)
    c.passengers.append(p2)
    c.yacht = b
    c.save()

    main_user.profiles = list(main_user.profiles)
    users = User.query.all()
    for u in users:
        id = u.main_profile.id # force load
        u.profiles = list(u.profiles)
        for p in u.profiles:
            p.roles = list(p.roles)
    cruises = Cruise.query.all()
    for c in cruises:
        c.roles = list(c.roles)
    return Bunch(**{'main_user':main_user, 'main_password':main_password, 'main_email':main_email, 'users':users, 'profiles':UserProfile.query.all(), 'yachts':Yacht.query.all(), 'cruises':cruises})

@pytest.fixture
def user(db):
    """A user for the tests."""
    user = UserFactory(password='myprecious')
    db.session.commit()
    return user

class Bunch(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
    def __eq__(self, other):
        return self.__dict__ == other.__dict__
