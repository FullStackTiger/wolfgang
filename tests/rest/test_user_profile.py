# -*- coding: utf-8 -*-
"""REST Endpoint integration tests for UserProfile."""

from http import HTTPStatus
import pytest

class TestProfile:
    """User profile tests."""

    profile_namespace_url = '/api/user/profile/{}'
    user_namespace_url = '/api/user/{}/profile/'

    def test_post_user_profile(self, auth_rest_client, populated_db):
        """Add profile to user."""
        endpoint_url = self.user_namespace_url.format(populated_db.main_user.id)
        data = {'first_name':'Alter', 'last_name':'Ego'}
        response = auth_rest_client.post_test_auth(endpoint_url, data)
        print(response.dict)
        print(response.dict['id'])
        assert response.status_code == HTTPStatus.OK
        assert 'id' in response.dict
        assert response.dict['id'] is not None

        # TODO
        # check details of the response
        # test POST with more complete profile


    def test_get_user_profiles(self, auth_rest_client, populated_db):
        """Get all user profiles."""

        endpoint_url = self.user_namespace_url.format(populated_db.main_user.id)
        response = auth_rest_client.get_test_auth(endpoint_url)
        print(response.dict)
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.dict, list)
        assert len(response.dict) == len(populated_db.main_user.profiles)
        # TODO
        # Load all profiles for user
        # make sure self.profile_id is in it
        # check that one profile is main

    def test_get_profile(self, auth_rest_client, populated_db):
        """Get profile details."""
        profile = populated_db.main_user.main_profile
        endpoint_url = self.profile_namespace_url.format(profile.id)
        response = auth_rest_client.get_test_auth(endpoint_url)
        print(response.dict)

        assert response.status_code == HTTPStatus.OK

        # Load profile and look at details
        # TODO

    def test_put_profile(self, auth_rest_client, populated_db):
        """Update profile details."""
        profile = populated_db.main_user.main_profile
        endpoint_url = self.profile_namespace_url.format(profile.id)
        data = {'first_name': 'Changed'}
        response = auth_rest_client.put_test_auth(endpoint_url, data)
        print(response.dict)

        assert response.status_code == HTTPStatus.OK

        # test what happens when setting is_main to False
        # test automatic profile naming
        # TODO

    def test_delete_profile(self, auth_rest_client, populated_db):
        """Delete profile."""
        # TODO: figure out a way to for test_auth to work after repeated calls (app seems to cache state of token/current_user)
        for profile in populated_db.main_user.profiles:

            can_delete = (profile.roles is None or len(profile.roles) == 0)
            print(can_delete)
            endpoint_url = self.profile_namespace_url.format(profile.id)
            response = auth_rest_client.delete(endpoint_url)
            assert response.status_code == (HTTPStatus.NO_CONTENT if can_delete else HTTPStatus.CONFLICT)

        # TODO
