# -*- coding: utf-8 -*-
"""REST Endpoint integration tests for full cruise workflow."""

from http import HTTPStatus
import pytest

class TestApprovalWorkflow:
    """Full cruise approval workflow tests."""

    user_ns_url = '/api/user/'
    user_by_id_ns_url = '/api/user/{}'
    profile_ns_url = '/api/user/profile/{}'
    profile_by_user_ns_url = '/api/user/{}/profile/'
    cruise_by_user_ns_url = '/api/cruise/by_user/{}/'
    cruise_ns_url = '/api/cruise/{}'
    yacht_by_user_ns_url = '/api/yacht/by_user/{}/'
    yacht_ns_url = '/api/yacht/{}'
    approval_ns_url = '/api/cruise/{}/approval/'

    def test_cruise_approval_workflow_1_empty_db(self, rest_client, generate_pwd, db):
        """Testing with empty DB."""
        self._cruise_approval_workflow_1(rest_client, generate_pwd, db)

    def test_cruise_approval_workflow_1_populated_db(self, rest_client, generate_pwd, populated_db):
        """Testing with populated DB."""
        self._cruise_approval_workflow_1(rest_client, generate_pwd, populated_db)

    def test_cruise_approval_workflow_2_empty_db(self, rest_client, generate_pwd, db):
        """Testing with empty DB."""
        self._cruise_approval_workflow_2(rest_client, generate_pwd, db)

    def test_cruise_approval_workflow_2_populated_db(self, rest_client, generate_pwd, populated_db):
        """Testing with populated DB."""
        self._cruise_approval_workflow_2(rest_client, generate_pwd, populated_db)

    def _prepare_users(self, rest_client, generate_pwd, db):
        """Common code for all tests."""

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

        # get cruise (check access as creator)
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['locked'] is False
        assert response.dict['write_access'] is True

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

        return (user_1, email_1, password_1, user_2, email_2, password_2, contact, yacht, cruise)

    def _cruise_approval_workflow_1(self, rest_client, generate_pwd, db):
        """
        Add 2 approvals and remove both. Check approval, role_status, locked,
        and write_access each step of the way.

        Using non-preauthorised rest_client (not auth_rest_client) and must work regardless of DB content.
        """

        user_1, email_1, password_1, user_2, email_2, password_2, contact, yacht, cruise = self._prepare_users(rest_client, generate_pwd, db)

        ######################## Log in as user_2:
        rest_client.authenticate(email_2, password_2)
        ################################################

        endpoint_url = self.user_ns_url + 'me'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['email'] == email_2
        assert len(response.dict['profiles']) == 2

        # check that user_1 is in user_2's contacts:
        endpoint_url = self.user_by_id_ns_url.format(user_2['id']) + '/contact/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict[0]['contacts']) == 1
        assert response.dict[0]['contacts'][0]['id'] == user_1['main_profile']['id']

        # attempt to modify user_1 profile info:
        endpoint_url = self.profile_ns_url.format(user_1['main_profile']['id'])
        data = {'passport_num': 'Something is broken'}
        response = rest_client.put(endpoint_url, data)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

        # check that no cruise is tied to user:
        endpoint_url = self.cruise_by_user_ns_url.format(user_2['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 0

        # attempt to get/rename yacht:
        endpoint_url = self.yacht_ns_url.format(yacht['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        response = rest_client.put(endpoint_url, {'name': "Something is broken"})
        assert response.status_code == HTTPStatus.UNAUTHORIZED

        # attempt reading/writing to cruise before having a role (should fail):
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        response = rest_client.put(endpoint_url, {'yacht_id': 123})
        assert response.status_code == HTTPStatus.UNAUTHORIZED

        ######################## Log back in as user_1:
        rest_client.authenticate(email_1, password_1)
        ################################################

        # Assign user_2 as passenger:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/passengers/'
        data = {'profile_id':contact['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        assert response.dict[0]['id'] == contact['id']

        # list of passengers should show updated info:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/passengers/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict[0]['id'] == contact['id']

        # modify contact/passenger profile info:
        endpoint_url = self.profile_ns_url.format(contact['id'])
        passport_num_2 = 'FR007X1234'
        data = {'passport_num': passport_num_2}
        response = rest_client.put(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK

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

        # Get approvals:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 1

        # Get roles status:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/role_status/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 1
        my_response = next(x for x in response.dict if x['profile']['id'] == user_1['main_profile']['id'])
        assert my_response is not None
        assert my_response['past_approval'] is False
        assert my_response['current_approval'] is True
        assert my_response['has_signed'] is False

        # Get cruise (check access)
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['locked'] is True
        assert response.dict['write_access'] is True
        assert response.dict['version'] == 0

        # Attempt to assign user 2 as captain (locked):
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/captains/'
        data = {'profile_id':contact['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.LOCKED

        ######################## Log in as user_2:
        rest_client.authenticate(email_2, password_2)
        ################################################

        # attempt to modify user_1 profile info:
        endpoint_url = self.profile_ns_url.format(user_1['main_profile']['id'])
        data = {'passport_num': 'this is broken'}
        response = rest_client.put(endpoint_url, data)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

        # check that profile has been updated by user_1:
        endpoint_url = self.user_ns_url + 'me'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['email'] == email_2
        assert len(response.dict['profiles']) == 2
        check_pass = [p['passport_num'] for p in response.dict['profiles'] if p['passport_num'] is not None][0]
        assert check_pass == passport_num_2
        profiles_2 = response.dict['profiles']

        # check that cruise is now listed in available cruises:
        endpoint_url = self.cruise_by_user_ns_url.format(user_2['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 1

        # Get cruise (check access and version)
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['locked'] is True
        assert response.dict['write_access'] is False
        assert response.dict['version'] == 0

        # Attempt to add approval on behalf of user 1:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        data = {'user_id':user_1['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

        # attempt to add approval (passenger role does not have access):
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        data = {'user_id':user_2['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

        # Get approvals:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 1

        ######################## Log back in as user_1:
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
        assert len(response.dict) == 0

        # Get cruise (check version)
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['locked'] is False
        assert response.dict['version'] == 1

        # Add user_2 role as client:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/clients/'
        data = {'profile_id':contact['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        assert response.dict[0]['id'] == contact['id']

        # list of clients should show updated info:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/clients/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict[0]['id'] == contact['id']

        # Add approval (lock cruise):
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        data = {'user_id':user_1['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK

        # Get approvals:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 1

        # Get roles status:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/role_status/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        print(response.dict)
        assert len(response.dict) == 2
        my_response = next(x for x in response.dict if x['profile']['id'] == user_1['main_profile']['id'])
        assert my_response is not None
        assert my_response['role'] == 'BROKER'
        assert my_response['past_approval'] is False
        assert my_response['current_approval'] is True
        assert my_response['has_signed'] is False

        # Get cruise (check access)
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['locked'] is True
        assert response.dict['write_access'] is True
        assert response.dict['version'] == 1

        ######################## Log in as user_2:
        rest_client.authenticate(email_2, password_2)
        ################################################

        # Get cruise (check access and version)
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['locked'] is True
        assert response.dict['write_access'] is True
        assert response.dict['version'] == 1

        # Get approvals:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        print(response.dict)
        assert len(response.dict) == 1

        # add approval:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        data = {'user_id':user_2['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK

        # Get approvals:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        print(response.dict)
        assert len(response.dict) == 2

        # Get roles status:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/role_status/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 2
        my_response = next(x for x in response.dict if x['profile']['id'] == contact['id'])
        assert my_response is not None
        assert my_response['role'] == 'CLIENT'
        assert my_response['past_approval'] is False
        assert my_response['current_approval'] is True
        assert my_response['has_signed'] is False

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

        # Get roles status:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/role_status/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 2
        my_response = next(x for x in response.dict if x['profile']['id'] == user_1['main_profile']['id'])
        assert my_response is not None
        assert my_response['role'] == 'BROKER'
        assert my_response['past_approval'] is False
        assert my_response['current_approval'] is False
        assert my_response['has_signed'] is False

        # Get cruise (check access and version)
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['locked'] is True
        assert response.dict['write_access'] is True
        assert response.dict['version'] == 1

        # create new yacht:
        endpoint_url = self.yacht_by_user_ns_url.format(user_1['id'])
        data = {'name': "Jack's Better Yacht"}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        yacht_2 = response.dict

        # attempt to edit cruise to use new yacht:
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        data = {'yacht_id': yacht_2['id']}
        response = rest_client.put(endpoint_url, data)
        assert response.status_code == HTTPStatus.LOCKED

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

        # Get roles status:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/role_status/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 2
        my_response = next(x for x in response.dict if x['profile']['id'] == contact['id'])
        assert my_response is not None
        assert my_response['role'] == 'CLIENT'
        assert my_response['past_approval'] is False
        assert my_response['current_approval'] is False
        assert my_response['has_signed'] is False

        # Get cruise (check access, version)
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['locked'] is False
        assert response.dict['write_access'] is True
        assert response.dict['version'] == 2


    def _cruise_approval_workflow_2(self, rest_client, generate_pwd, db):
        """
        Add 1 approval and unlock by another user.
        Check approval, role_status, locked, and write_access each step of the way.

        Using non-preauthorised rest_client (not auth_rest_client) and must work regardless of DB content.
        """

        user_1, email_1, password_1, user_2, email_2, password_2, contact, yacht, cruise = self._prepare_users(rest_client, generate_pwd, db)

        ######################## Log in as user_1:
        rest_client.authenticate(email_1, password_1)
        ################################################

        # Assign user_2 as client:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/clients/'
        data = {'profile_id':contact['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        assert response.dict[0]['id'] == contact['id']

        # list of clients should show updated info:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/clients/'
        response = rest_client.get(endpoint_url)
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

        # Get approvals:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 1

        # Get roles status:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/role_status/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 2
        my_response = next(x for x in response.dict if x['profile']['id'] == user_1['main_profile']['id'])
        assert my_response is not None
        assert my_response['role'] == 'BROKER'
        assert my_response['past_approval'] is False
        assert my_response['current_approval'] is True
        assert my_response['has_signed'] is False
        u2_response = next(x for x in response.dict if x['profile']['id'] == contact['id'])
        assert u2_response is not None
        assert u2_response['role'] == 'CLIENT'
        assert u2_response['past_approval'] is False
        assert u2_response['current_approval'] is False
        assert u2_response['has_signed'] is False

        # Get cruise (check access)
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['locked'] is True
        assert response.dict['write_access'] is True
        assert response.dict['version'] == 0

        ######################## Log in as user_2:
        rest_client.authenticate(email_2, password_2)
        ################################################

        # check that cruise is now listed in available cruises:
        endpoint_url = self.cruise_by_user_ns_url.format(user_2['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 1

        # Get cruise (check access and version)
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['locked'] is True
        assert response.dict['write_access'] is True
        assert response.dict['version'] == 0

        # Get approvals:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 1

        # Attempt to assign self as passenger:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/passengers/'
        data = {'profile_id':user_2['main_profile']['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.LOCKED

        # Attempt to remove approval:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval_by/{}'.format(user_1['id'])
        response = rest_client.delete(endpoint_url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

        # Unlock:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/lock'
        response = rest_client.delete(endpoint_url)
        assert response.status_code == HTTPStatus.NO_CONTENT

        # Get approvals:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 0

        # Get cruise (check access and version)
        endpoint_url = self.cruise_ns_url.format(cruise['id'])
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict['locked'] is False
        assert response.dict['write_access'] is True
        assert response.dict['version'] == 1

        # Assign self as stakeholder:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/stakeholders/'
        data = {'profile_id':user_2['main_profile']['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK
        assert response.dict[0]['id'] == user_2['main_profile']['id']

        # list of stakeholders should show updated info:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/stakeholders/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert response.dict[0]['id'] == user_2['main_profile']['id']

        # Get roles status:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/role_status/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 3
        u1_response = next(x for x in response.dict if x['profile']['id'] == user_1['main_profile']['id'])
        assert u1_response is not None
        assert u1_response['past_approval'] is True
        assert u1_response['current_approval'] is False
        assert u1_response['has_signed'] is False
        assert u1_response['role'] == 'BROKER'
        u2_cap_response = next(x for x in response.dict if x['profile']['id'] == contact['id'])
        assert u2_cap_response is not None
        assert u2_cap_response['past_approval'] is False
        assert u2_cap_response['current_approval'] is False
        assert u2_cap_response['has_signed'] is False
        assert u2_cap_response['role'] == 'CLIENT'
        u2_pass_response = next(x for x in response.dict if x['profile']['id'] == user_2['main_profile']['id'])
        assert u2_pass_response is not None
        assert u2_pass_response['past_approval'] is False
        assert u2_pass_response['current_approval'] is False
        assert u2_pass_response['has_signed'] is False
        assert u2_pass_response['role'] == 'STAKEHOLDER'

        # Add approval (lock cruise):
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        data = {'user_id':user_2['id']}
        response = rest_client.post(endpoint_url, data)
        assert response.status_code == HTTPStatus.OK

        # Get approvals (2 roles for 1 user):
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/approval/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 2

        # Get roles status:
        endpoint_url = self.cruise_ns_url.format(cruise['id']) + '/role_status/'
        response = rest_client.get(endpoint_url)
        assert response.status_code == HTTPStatus.OK
        assert len(response.dict) == 3
        u1_response = next(x for x in response.dict if x['profile']['id'] == user_1['main_profile']['id'])
        assert u1_response is not None
        assert u1_response['past_approval'] is True
        assert u1_response['current_approval'] is False
        assert u1_response['has_signed'] is False
        assert u1_response['role'] == 'BROKER'
        u2_cap_response = next(x for x in response.dict if x['profile']['id'] == contact['id'])
        assert u2_cap_response is not None
        assert u2_cap_response['past_approval'] is False
        assert u2_cap_response['current_approval'] is True
        assert u2_cap_response['has_signed'] is False
        assert u2_cap_response['role'] == 'CLIENT'
        u2_pass_response = next(x for x in response.dict if x['profile']['id'] == user_2['main_profile']['id'])
        assert u2_pass_response is not None
        assert u2_pass_response['past_approval'] is False
        assert u2_pass_response['current_approval'] is True
        assert u2_pass_response['has_signed'] is False
        assert u2_pass_response['role'] == 'STAKEHOLDER'
