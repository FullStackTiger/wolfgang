# -*- coding: utf-8 -*-
"""REST Endpoint integration tests for Cruise."""

from http import HTTPStatus
import pytest

class TestCruise:
    """Cruise tests."""

    cruise_by_user_ns_url = '/api/cruise/by_user/{}/'
    cruise_ns_url = '/api/cruise/{}'

    def test_post_cruise_by_user(self, auth_rest_client, populated_db):
        """Add cruise for user."""
        endpoint_url = self.cruise_by_user_ns_url.format(populated_db.main_user.id)

        # Test empty cruise:
        response = auth_rest_client.post_test_auth(endpoint_url, {})
        assert response.status_code == HTTPStatus.OK
        assert 'id' in response.dict
        assert response.dict['id'] is not None

        # Test with existing yacht
        data = {'yacht_id':1}
        response = auth_rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        assert 'id' in response.dict
        assert response.dict['id'] is not None
        assert response.dict['yacht']['id'] == 1

        # Test with more data
        data = {'yacht_id':1, 'cruise_areas':[], 'special_conditions':[],
            'fuel_price':{'base_price_litre':123}, 'trip_type':'OUTSIDE',
            'base_price_cruising':5.5, 'base_price_routing':2.3}
        response = auth_rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        assert 'id' in response.dict
        assert response.dict['id'] is not None
        assert response.dict['yacht']['id'] == 1

        # TODO
        # check details of the response
        # test POST with more complete info


    def test_get_cruise_by_user(self, auth_rest_client, populated_db):
        """Get all cruises for user."""

        num_preexisting_cruises = 1

        endpoint_url = self.cruise_by_user_ns_url.format(populated_db.main_user.id)
        response = auth_rest_client.get_test_auth(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.dict, list)
        assert len(response.dict) == num_preexisting_cruises
        print(response.dict)

        endpoint_url = self.cruise_by_user_ns_url.format(populated_db.main_user.id)
        res_cruise_1 = auth_rest_client.post(endpoint_url, {})
        assert res_cruise_1.status_code == HTTPStatus.OK
        assert 'id' in res_cruise_1.dict
        print(res_cruise_1.dict)

        endpoint_url = self.cruise_by_user_ns_url.format(populated_db.main_user.id)
        response = auth_rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.dict, list)
        print(response.dict)
        assert len(response.dict) == num_preexisting_cruises + 1
        assert res_cruise_1.dict['id'] in [x['id'] for x in response.dict]

        endpoint_url = self.cruise_by_user_ns_url.format(populated_db.main_user.id)
        res_cruise_2 = auth_rest_client.post(endpoint_url, {})
        assert res_cruise_2.status_code == HTTPStatus.OK
        assert res_cruise_2.dict['id'] != res_cruise_1.dict['id'] # Sanity check…

        endpoint_url = self.cruise_by_user_ns_url.format(populated_db.main_user.id)
        response = auth_rest_client.get(endpoint_url)
        print(response.dict)
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.dict, list)
        assert len(response.dict) == num_preexisting_cruises + 2
        print(response.dict)
        assert res_cruise_1.dict['id'] in [x['id'] for x in response.dict]
        assert res_cruise_2.dict['id'] in [x['id'] for x in response.dict]

        # TODO
        # More complex tests

    def test_get_cruise_by_id(self, auth_rest_client, populated_db):
        """Get cruise by ID."""

        endpoint_url = self.cruise_ns_url.format(1) # pre-existing cruise
        response = auth_rest_client.get_test_auth(endpoint_url)
        assert response.status_code == HTTPStatus.OK


        # TODO: more tests
