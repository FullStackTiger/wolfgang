# -*- coding: utf-8 -*-
"""REST Endpoint integration tests for full cruise workflow."""

from http import HTTPStatus
import pytest

class TestVersioningWorkflow:
    """Versioning workflow tests."""

    user_ns_url = '/api/user/'
    user_by_id_ns_url = '/api/user/{}'
    profile_ns_url = '/api/user/profile/{}'
    profile_by_user_ns_url = '/api/user/{}/profile/'
    cruise_by_user_ns_url = '/api/cruise/by_user/{}/'
    cruise_ns_url = '/api/cruise/{}'
    yacht_by_user_ns_url = '/api/yacht/by_user/{}/'
    yacht_ns_url = '/api/yacht/{}'
    approval_ns_url = '/api/cruise/{}/approval/'

    def test_versioning_workflow_empty_db(self, rest_client, generate_pwd, db):
        """Testing with empty DB"""

        self._versioning_workflow(rest_client, generate_pwd, db)

    def test_versioning_workflow_populated_db(self, rest_client, generate_pwd, populated_db):
        """Testing with populated DB"""
        self._versioning_workflow(rest_client, generate_pwd, populated_db)

    def _versioning_workflow(self, rest_client, generate_pwd, db):
        """
        Create user, authenticate, create cruise, create boat and assign, add passenger.

        Using non-preauthorised rest_client (not auth_rest_client) and must work regardless of DB content.
        """

        # Create new user and log in:
        password_1 = generate_pwd()
        email_1 = 'jack_workflow2@forgetme.com'
        data = {'email':email_1, 'password':password_1, 'first_name':'Jack', 'last_name':'Shortlived'}
        response = rest_client.post(self.user_ns_url, data)
        assert response.status_code == HTTPStatus.OK
        user_1 = response.dict

        password_2 = generate_pwd()
        email_2 = 'paul_workflow2@forgetme.com'
        data = {'email':email_2, 'password':password_2, 'first_name':'Paul', 'last_name':'Reallastname'}
        response = rest_client.post(self.user_ns_url, data)
        assert response.status_code == HTTPStatus.OK
        user_2 = response.dict

        ######################## Log in as user_1:
        rest_client.authenticate(email_1, password_1)
        ################################################

        # create new yacht:
        endpoint_url = self.yacht_by_user_ns_url.format(user_1['id'])
        data = {'name': "Jack's Yacht"}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        yacht = response.dict

        # Create cruise with yacht
        endpoint_url = self.cruise_by_user_ns_url.format(user_1['id'])
        response = rest_client.post(endpoint_url, {'yacht_id':yacht['id']})
        assert response.status_code == HTTPStatus.OK
        cruise = response.dict

        # Assign self as cruise broker:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/brokers/'
        data = {'profile_id':user_1['main_profile']['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        assert response.dict[0]['id'] == user_1['main_profile']['id']

        # Create contact (with same email as user_2):
        endpoint_url = self.user_by_id_ns_url.format(user_1['id']) + '/contact/'
        data = {'email':email_2, 'first_name':'Paulo', 'last_name':'Friendofjack'}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        contact = response.dict

        # Assign user 2 as client:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/clients/'
        data = {'profile_id':contact['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        assert response.dict[0]['id'] == contact['id']

        # Get approvals:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 0

        # Add approval (lock cruise):
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        data = {'user_id':user_1['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK

        ######################## Log in as user_2:
        rest_client.authenticate(email_2, password_2)
        ################################################

        # Get cruise (check access and version)
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['locked'] is True
        assert response.dict['write_access'] is True
        assert response.dict['version'] == 0

        # Attempt to add approval on behalf of user 1:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        data = {'user_id':user_1['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

        # Add approval:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        data = {'user_id':user_2['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK

        # Get approvals:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 2

        # Get cruise (check access and version)
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['locked'] is True
        assert response.dict['write_access'] is True
        assert response.dict['version'] == 0

        ######################## Log in as user_1:
        rest_client.authenticate(email_1, password_1)
        ################################################

        # Remove approval:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval_by/{}'.format(user_1['id'])
        response = rest_client.delete(endpoint_url)
        assert response.status_code == HTTPStatus.NO_CONTENT

        # Get approvals:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 1

        # Rename yacht (shouldn't appear in locked cruise):
        endpoint_url = self.yacht_ns_url.format(yacht['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        data = {'name': "Paul's Yacht"}
        response = rest_client.put(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['id'] == yacht['id']
        assert response.dict['name'] == data['name']
        assert response.dict['version'] == 1
        new_yacht_name = data['name']

        # Get cruise (check access, version)
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['locked'] is True
        assert response.dict['write_access'] is True
        assert response.dict['version'] == 0
        # Check that attached yacht info has not been touched:
        assert response.dict['yacht']['version'] == 0
        assert response.dict['yacht']['name'] != new_yacht_name
        assert response.dict['yacht']['name'] == yacht['name']

        ######################## Log in as user_2:
        rest_client.authenticate(email_2, password_2)
        ################################################

        # Remove approval (unlock cruise):
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval_by/{}'.format(user_2['id'])
        response = rest_client.delete(endpoint_url)
        assert response.status_code == HTTPStatus.NO_CONTENT

        # Get approvals:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 0

        # Get cruise (check access, version)
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['locked'] is False
        assert response.dict['write_access'] is True
        assert response.dict['version'] == 1
        # Check that attached yacht info has been updated:
        assert response.dict['yacht']['version'] == 1
        assert response.dict['yacht']['name'] == new_yacht_name

        ######################## Log in as user_1:
        rest_client.authenticate(email_1, password_1)
        ################################################

        # Get cruise (check access)
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['locked'] is False
        assert response.dict['write_access'] is True
        assert response.dict['version'] == 1

    #     # get cruise (check access)
    #     endpoint_url = self.cruise_ns_url.format(cruise['id'])
    #     response = rest_client.get(endpoint_url)
    #     assert response.status_code == HTTPStatus.OK
    #     assert response.dict['locked'] is True
    #     assert response.dict['write_access'] is True
    #
    #     # read user 1's profile
    #     endpoint_url = self.profile_ns_url.format(user_1['main_profile']['id'])
    #     response = rest_client.get(endpoint_url)
    #     assert response.status_code == HTTPStatus.OK
    #     assert response.dict['locked'] is True
    #     assert response.dict['write_access'] is True
    #     print(response.dict)
    #
    #     # modify user 1 profile info:
    #     endpoint_url = self.profile_ns_url.format(user_1['main_profile']['id'])
    #     passport_num_1 = 'EN1234#142'
    #     data = {'passport_num': passport_num_1}
    #     response = rest_client.put(endpoint_url, data)
    #     assert response.status_code == HTTPStatus.LOCKED
    #     print(response.dict)
    #     assert False
    #
    # #     ######################## Log in as user_2:
    # #     rest_client.authenticate(email_2, password_2)
    # #     ################################################
    # #
    # #     endpoint_url = self.user_ns_url + 'me'
    # #     response = rest_client.get(endpoint_url)
    # #     assert response.status_code == HTTPStatus.OK
    # #     assert response.dict['email'] == email_2
    # #     assert len(response.dict['profiles']) == 2
    # #
    # #     # check that user_1 is in user_2's contacts:
    # #     endpoint_url = self.user_by_id_ns_url.format(user_2['id']) + '/contact/'
    # #     response = rest_client.get(endpoint_url)
    # #     assert response.status_code == HTTPStatus.OK
    # #     assert len(response.dict[0]['contacts']) == 1
    # #     assert response.dict[0]['contacts'][0]['id'] == user_1['main_profile']['id']
    # #
    # #     # modify user_1 profile info:
    # #     # TODO: check that this no longer works when not associated through a cruise
    # #     endpoint_url = self.profile_ns_url.format(user_1['main_profile']['id'])
    # #     passport_num_1 = 'EN1234#142'
    # #     data = {'passport_num': passport_num_1}
    # #     response = rest_client.put(endpoint_url, data)
    # #     assert response.status_code == HTTPStatus.OK
    # #
    # #     # check that no cruise is tied to user:
    # #     endpoint_url = self.cruise_by_user_ns_url.format(user_2['id'])
    # #     response = rest_client.get(endpoint_url)
    # #     assert response.status_code == HTTPStatus.OK
    # #     assert len(response.dict) == 0
    # #
    # #     # attempt to get/rename yacht:
    # #     endpoint_url = self.yacht_ns_url.format(yacht['id'])
    # #     response = rest_client.get(endpoint_url)
    # #     assert response.status_code == HTTPStatus.UNAUTHORIZED
    # #
    # #     response = rest_client.put(endpoint_url, {'name': "Something is broken"})
    # #     assert response.status_code == HTTPStatus.UNAUTHORIZED
    # #
    # #     # attempt reading/writing to cruise before having a role (should fail):
    # #     endpoint_url = self.cruise_ns_url.format(cruise['id'])
    # #     response = rest_client.get(endpoint_url)
    # #     assert response.status_code == HTTPStatus.UNAUTHORIZED
    # #
    # #     response = rest_client.put(endpoint_url, {'yacht_id': 123})
    # #     assert response.status_code == HTTPStatus.UNAUTHORIZED
    # #
    # #     ######################## Log back in as user_1:
    # #     rest_client.authenticate(email_1, password_1)
    # #     ################################################
    # #
    # #     # check that passport num has been modified by user_2
    # #     endpoint_url = self.user_ns_url + 'me'
    # #     response = rest_client.get(endpoint_url)
    # #     assert response.status_code == HTTPStatus.OK
    # #     assert response.dict['email'] == email_1
    # #     check_pass = [p['passport_num'] for p in response.dict['profiles'] if p['passport_num'] is not None][0]
    # #     assert check_pass == passport_num_1
    # #
    # #     # Assign user_2 as captain:
    # #     endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/captains/'
    # #     data = {'profile_id':contact['id']}
    # #     response = rest_client.post(endpoint_url, data)
    # #     assert response.status_code == HTTPStatus.OK
    # #     assert response.dict[0]['id'] == contact['id']
    # #
    # #     # list of captains should show updated info:
    # #     endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/captains/'
    # #     response = rest_client.get(endpoint_url)
    # #     assert response.status_code == HTTPStatus.OK
    # #     assert response.dict[0]['id'] == contact['id']
    # #
    # #     # modify contact/captain profile info:
    # #     endpoint_url = self.profile_ns_url.format(contact['id'])
    # #     passport_num_2 = 'FR007X1234'
    # #     data = {'passport_num': passport_num_2}
    # #     response = rest_client.put(endpoint_url, data)
    # #     assert response.status_code == HTTPStatus.OK
    # #
    # #
    # #     ######################## Log back in as user_2:
    # #     rest_client.authenticate(email_2, password_2)
    # #     ################################################
    # #
    # #     # check that profile has been updated by user_1:
    # #     endpoint_url = self.user_ns_url + 'me'
    # #     response = rest_client.get(endpoint_url)
    # #     assert response.status_code == HTTPStatus.OK
    # #     assert response.dict['email'] == email_2
    # #     assert len(response.dict['profiles']) == 2
    # #     check_pass = [p['passport_num'] for p in response.dict['profiles'] if p['passport_num'] is not None][0]
    # #     assert check_pass == passport_num_2
    # #     profiles_2 = response.dict['profiles']
    # #
    # #     # check that cruise is now listed in available cruises:
    # #     endpoint_url = self.cruise_by_user_ns_url.format(user_2['id'])
    # #     response = rest_client.get(endpoint_url)
    # #     assert response.status_code == HTTPStatus.OK
    # #     assert len(response.dict) == 1
    # #
    # #     # read cruise and check we have write access:
    # #     endpoint_url = self.cruise_ns_url.format(cruise['id'])
    # #     response = rest_client.get(endpoint_url)
    # #     assert response.status_code == HTTPStatus.OK
    # #     assert response.dict['yacht']['id'] == yacht['id']
    # #     assert response.dict['yacht']['name'] == yacht['name']
    # #     assert response.dict['write_access']
    # #
    # #     # rename yacht:
    # #     endpoint_url = self.yacht_ns_url.format(yacht['id'])
    # #     response = rest_client.get(endpoint_url)
    # #     assert response.status_code == HTTPStatus.OK
    # #
    # #     data = {'name': "Paul's Yacht"}
    # #     response = rest_client.put(endpoint_url, data)
    # #     assert response.status_code == HTTPStatus.OK
    # #     assert response.dict['id'] == yacht['id']
    # #     assert response.dict['name'] == data['name']
    # #
    # #     # create new yacht:
    # #     endpoint_url = self.yacht_by_user_ns_url.format(user_2['id'])
    # #     data = {'name': "Paul's Better Yacht"}
    # #     response = rest_client.post(endpoint_url, data)
    # #     assert response.status_code == HTTPStatus.OK
    # #     yacht_2 = response.dict
    # #
    # #     # Edit cruise to use new yacht:
    # #     endpoint_url = self.cruise_ns_url.format(cruise['id'])
    # #     data = {'yacht_id': yacht_2['id']}
    # #     response = rest_client.put(endpoint_url, data)
    # #     assert response.status_code == HTTPStatus.OK
    # #     assert response.dict['yacht']['id'] == yacht_2['id']
    # #
    # #     # Give approval to cruise:
    # #     endpoint_url = self.approval_ns_url.format(cruise['id'])
    # #     data = {'user_id': user_2['id']}
    # #     response = rest_client.post(endpoint_url, data)
    # #     assert response.status_code == HTTPStatus.OK
    # #     assert response.dict[0]['id'] in [p['id'] for p in profiles_2]
    # #
    # #     # Check that cruise is locked:
    # #     endpoint_url = self.cruise_ns_url.format(cruise['id'])
    # #     response = rest_client.get(endpoint_url)
    # #     assert response.status_code == HTTPStatus.OK
    # #     assert response.dict['locked']
    # #     assert response.dict['write_access']
    # #
    # #     # Attempt to edit cruise to use old yacht:
    # #     endpoint_url = self.cruise_ns_url.format(cruise['id'])
    # #     data = {'yacht_id': yacht['id']}
    # #     response = rest_client.put(endpoint_url, data)
    # #     assert response.status_code == HTTPStatus.LOCKED
    # #
    # #     ######################## Log back in as user_1:
    # #     rest_client.authenticate(email_1, password_1)
    # #     ################################################
    # #
    # #     # Check that cruise is locked (but still have write access):
    # #     endpoint_url = self.cruise_ns_url.format(cruise['id'])
    # #     response = rest_client.get(endpoint_url)
    # #     assert response.status_code == HTTPStatus.OK
    # #     assert response.dict['locked']
    # #     assert response.dict['write_access']
    # #
    # #     # Attempt to edit cruise to use old yacht:
    # #     endpoint_url = self.cruise_ns_url.format(cruise['id'])
    # #     data = {'yacht_id': yacht['id']}
    # #     response = rest_client.put(endpoint_url, data)
    # #     assert response.status_code == HTTPStatus.LOCKED
    # #
    # #     # TODO: test unlock…
