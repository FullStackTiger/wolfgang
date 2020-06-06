# -*- coding: utf-8 -*-
"""REST Endpoint integration tests for Yacht."""

from http import HTTPStatus
import pytest

class TestYacht:
    """Yacht tests."""

    yacht_by_user_ns_url = '/api/yacht/by_user/{}/'
    yacht_ns_url = '/api/yacht/{}'

    def test_post_yacht_by_user(self, auth_rest_client, populated_db):
        """Add yacht for user."""
        endpoint_url = self.yacht_by_user_ns_url.format(populated_db.main_user.id)
        data = {'name':'Boaty McBoatface'}
        response = auth_rest_client.post_test_auth(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        assert 'id' in response.dict
        assert response.dict['id'] is not None

        return response.dict['id']
        # TODO
        # check details of the response
        # test POST with more complete info


    def test_get_yacht_by_user(self, auth_rest_client, populated_db):
        """Get all yachts for user."""

        endpoint_url = self.yacht_by_user_ns_url.format(populated_db.main_user.id)
        response = auth_rest_client.get_test_auth(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.dict, list)
        print(response.dict)
        assert len(response.dict) == 0

        endpoint_url = self.yacht_by_user_ns_url.format(populated_db.main_user.id)
        data = {'name':'Boaty McBoatface'}
        res_yacht_1 = auth_rest_client.post(endpoint_url, data)
        assert res_yacht_1.status_code == HTTPStatus.OK
        assert 'id' in res_yacht_1.dict

        endpoint_url = self.yacht_by_user_ns_url.format(populated_db.main_user.id)
        response = auth_rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.dict, list)
        assert len(response.dict) == 1
        assert response.dict[0]['id'] == res_yacht_1.dict['id']
        assert response.dict[0]['name'] == res_yacht_1.dict['name']

        endpoint_url = self.yacht_by_user_ns_url.format(populated_db.main_user.id)
        data = {'name':'Yet Another Boat'}
        res_yacht_2 = auth_rest_client.post(endpoint_url, data)
        assert res_yacht_2.status_code == HTTPStatus.OK
        assert res_yacht_2.dict['id'] != res_yacht_1.dict['id'] # Sanity check…

        endpoint_url = self.yacht_by_user_ns_url.format(populated_db.main_user.id)
        response = auth_rest_client.get(endpoint_url)
        print(response.dict)
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.dict, list)
        assert len(response.dict) == 2
        print(response.dict)
        assert res_yacht_1.dict['id'] in [x['id'] for x in response.dict]
        assert res_yacht_2.dict['id'] in [x['id'] for x in response.dict]

        # TODO
        # More complex tests

    def test_get_yacht_by_id(self, auth_rest_client, populated_db):
        """Get yacht by ID."""

        endpoint_url = self.yacht_ns_url.format(1) # pre-existing boat
        response = auth_rest_client.get_test_auth(endpoint_url)
        assert response.status_code == HTTPStatus.OK

        # endpoint_url = self.yacht_by_user_ns_url.format(populated_db.main_user.id)
        # data = {'name':'Boaty McBoatface'}
        # response = auth_rest_client.post(endpoint_url, data)

        # TODO: more tests
