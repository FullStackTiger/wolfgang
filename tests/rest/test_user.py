# -*- coding: utf-8 -*-
"""REST Endpoint integration tests for User."""

from http import HTTPStatus
import pytest


class TestUser:
    """User tests."""

    namespace_url = '/api/user/'

    def test_create(self, rest_client, populated_db, generate_pwd):
        """Create user."""
        endpoint_url = self.namespace_url

        password = generate_pwd()
        data = {'email':'temp@forgetme.com', 'password':password, 'first_name':'Jack', 'last_name':'Shortlived'}
        response = rest_client.post(endpoint_url, data)

        assert response.status_code == HTTPStatus.OK
        assert response.dict['email'] == data['email']
        assert 'password' not in response.dict
        assert 'main_profile' in response.dict
        assert 'full_name' in response.dict['main_profile']
        assert len(response.dict['main_profile']['full_name']) > 0

    def test_login(self, rest_client, populated_db):
        """Login by email."""
        endpoint_url = self.namespace_url + 'login'

        data = {'email':populated_db.main_email, 'password':populated_db.main_password}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        assert 'access_token' in response.dict

        data = {'email':populated_db.main_email, 'password':'bad_password'}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert 'access_token' not in response.dict

        data = {'email':'bad_email', 'password':populated_db.main_password}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert 'access_token' not in response.dict

    def test_get_me(self, auth_rest_client, populated_db):
        """Get logged-in user."""
        endpoint_url = self.namespace_url + 'me'

        # Test with and without token
        response = auth_rest_client.get_test_auth(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        print(response.dict)
        assert response.dict['email'] == populated_db.main_email
        assert 'main_profile' in response.dict
        assert 'full_name' in response.dict['main_profile']
        assert len(response.dict['main_profile']['full_name']) > 0

    def test_get_id(self, auth_rest_client, populated_db):
        """Get logged-in user by id."""
        endpoint_url = self.namespace_url + '{}'

        # Get own ID (test with and without token)
        response = auth_rest_client.get_test_auth(endpoint_url.format(populated_db.main_user.id))
        assert response.status_code == HTTPStatus.OK
        assert response.dict['email'] == populated_db.main_email

        # Get non-existent user ID with token
        response = auth_rest_client.get(endpoint_url.format(100))
        assert response.status_code == HTTPStatus.NOT_FOUND
