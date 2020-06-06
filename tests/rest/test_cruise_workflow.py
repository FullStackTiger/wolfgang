# -*- coding: utf-8 -*-
"""REST Endpoint integration tests for full cruise workflow."""

from http import HTTPStatus
import pytest

class TestCruiseWorkflow:
    """Full cruise workflow tests."""

    profile_by_user_ns_url = '/api/user/{}/profile/'
    user_ns_url = '/api/user/'
    user_by_id_ns_url = '/api/user/{}'
    cruise_by_user_ns_url = '/api/cruise/by_user/{}/'
    cruise_ns_url = '/api/cruise/{}'
    yacht_by_user_ns_url = '/api/yacht/by_user/{}/'
    yacht_ns_url = '/api/yacht/{}'

    def test_cruise_creation_workflow_empty_db(self, rest_client, generate_pwd, db):
        """Testing with empty DB"""
        self._cruise_creation_workflow(rest_client, generate_pwd, db)

    def test_cruise_creation_workflow_populated_db(self, rest_client, generate_pwd, populated_db):
        """Testing with populated DB"""
        self._cruise_creation_workflow(rest_client, generate_pwd, populated_db)

    def _cruise_creation_workflow(self, rest_client, generate_pwd, db):
        """
        Create user, authenticate, create cruise, create boat and assign, add passenger.

        Using non-preauthorised rest_client (not auth_rest_client) and must work regardless of DB content.
        """

        # Create new user and log in:
        endpoint_url = self.user_ns_url
        password = generate_pwd()
        email = 'workflow1@forgetme.com'
        data = {'email':email, 'password':password, 'first_name':'Jack', 'last_name':'Shortlived'}
        response = rest_client.post(endpoint_url, data)

        assert response.status_code == HTTPStatus.OK
        assert response.dict['email'] == data['email']
        assert 'password' not in response.dict
        assert 'main_profile' in response.dict
        assert 'full_name' in response.dict['main_profile']
        assert len(response.dict['main_profile']['full_name']) > 0
        assert 'id' in response.dict['main_profile']
        user = response.dict

        rest_client.authenticate(email, password)

        endpoint_url = self.cruise_by_user_ns_url.format(user['id'])

        # New user has no existing cruises:
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.dict, list)
        assert len(response.dict) == 0

        # Create empty cruise
        response = rest_client.post(endpoint_url, {})
        assert response.status_code == HTTPStatus.OK
        assert response.dict['yacht'] == None
        cruise = response.dict
        print(cruise)

        # User now has 1 existing cruise:
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.dict, list)
        assert len(response.dict) == 1
        print(response.dict)
        assert cruise['id'] == response.dict[0]['id']
        assert response.dict[0]['yacht'] == None

        endpoint_url = self.yacht_by_user_ns_url.format(user['id'])

        # User should have no yachts:
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 0

        # create new yacht:
        data = {'name': "Jack's Yacht"}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        yacht = response.dict
        assert 'id' in yacht
        assert 'name' in yacht
        assert yacht['name'] == data['name']

        # User should have now have 1 yacht:
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 1
        assert response.dict[0]['id'] == yacht['id']
        assert response.dict[0]['name'] == yacht['name']

        # assign yacht to cruise
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        data = {'yacht_id':yacht['id']}
        response = rest_client.put(endpoint_url, data)
        assert response.dict['id'] == cruise['id']
        assert response.dict['yacht']['id'] == yacht['id']
        assert response.dict['yacht']['name'] == yacht['name']

        # cruise should now have a yacht
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.dict['id'] == cruise['id']
        assert response.dict['yacht']['id'] == yacht['id']
        assert response.dict['yacht']['name'] == yacht['name']

        # User should have no contacts:
        endpoint_url = self.user_by_id_ns_url.format(user['id']) + '/contact/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert 'contacts' in response.dict[0]
        assert len(response.dict[0]['contacts']) == 0

        # Add contact for user:
        data = {'email':'myfriend@test.com', 'first_name':'Robert', 'last_name':'Friendofjack'}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        assert 'id' in response.dict
        print(response.dict)
        assert response.dict['first_name'] == data['first_name']
        contact = response.dict

        # User should have now have 1 contact:
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert 'contacts' in response.dict[0]
        assert len(response.dict[0]['contacts']) == 1
        assert response.dict[0]['contacts'][0]['id'] == contact['id']
        print(response.dict[0]['contacts'][0])
        assert response.dict[0]['contacts'][0]['full_name'] == contact['first_name'] + ' ' + contact['last_name']

        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/brokers/'

        # new Cruise should have no brokers:
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 0

        # Assign self as cruise broker:
        data = {'profile_id':user['main_profile']['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 1
        assert 'id' in response.dict[0]
        assert response.dict[0]['id'] == user['main_profile']['id']

        # new Cruise should now have 1 broker:
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 1
        assert 'id' in response.dict[0]
        assert response.dict[0]['id'] == user['main_profile']['id']

        # Create separate profile
        endpoint_url = self.profile_by_user_ns_url.format(user['id'])
        data = {'profile_name':'Captain Profile', 'first_name':'Jackie', 'last_name':'Imacaptain'}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        print(response.dict)
        assert 'profiles' in response.dict
        assert len(response.dict['profiles']) == 2
        assert data['profile_name'] in [p['profile_name'] for p in response.dict['profiles']]

        profile = [p for p in response.dict['profiles'] if p['profile_name'] == data['profile_name']][0]

        # Assign self as captain:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/captains/'
        data = {'profile_id':profile['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 1
        assert 'id' in response.dict[0]
        assert response.dict[0]['id'] == profile['id']

        # Cruise should have no passengers:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/passengers/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 0

        # Assign contact as passenger:
        data = {'profile_id':contact['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 1
        assert 'id' in response.dict[0]
        assert response.dict[0]['id'] == contact['id']

        # new Cruise should now have 1 passenger:
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 1
        assert 'id' in response.dict[0]
        assert response.dict[0]['id'] == contact['id']
        assert response.dict[0]['full_name'] == contact['first_name'] + ' ' + contact['last_name']
