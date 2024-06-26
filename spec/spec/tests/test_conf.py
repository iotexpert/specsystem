import copy
import json
import os
from time import sleep
from django.conf import settings
from django.conf import settings
from utils.test_utils import SpecTestCase
from . import conf_resources as tr

class ConfTest(SpecTestCase):

    def test_role(self):
        response = self.post_request('/role/', tr.role_post_1, auth_lvl='USER')
        self.assert_auth_error(response, 'PERM_DENIED')

        response = self.post_request('/role/', tr.role_post_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        response = self.post_request('/role/', tr.role_post_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        response = self.post_request('/role/', tr.role_post_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        # Duplicate - Updates existing record
        response = self.post_request('/role/', tr.role_post_1a, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        response = self.get_request(f'/role/{tr.role_post_1a["role"]}')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        resp['users'] = resp['user_arr'][0]['username']
        resp.pop('user_arr')
        self.assertEqual(resp, tr.role_post_1a)

        # Error - invalid character in role name
        err_body = copy.deepcopy(tr.role_post_1)
        err_body['role'] = 'Name with Space'
        response = self.post_request('/role/', err_body, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('Role names cannot contain special characters', resp['error'])

        # Error - role name missing
        err_body['role'] = None
        response = self.post_request('/role/', err_body, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        self.assert_schema_err(response.content, 'role')

        # List all roles with 'Op' in name
        response = self.get_request('/role/?role=Op')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(len(resp['results'][0]['user_arr']), 2)
        self.assertEqual(len(resp['results'][1]['user_arr']), 1)
        del resp['results'][0]['user_arr']
        del resp['results'][1]['user_arr']
        self.assertEqual(resp, self.paginate_results([tr.role_post_2, tr.role_post_3]))

        # List all roles with 'Op' in name to a csv
        r1 = tr.role_post_2
        r2 = tr.role_post_3
        expected=f'''role,descr,spec_one,users,active,user_arr
{r1["role"]},{r1["descr"]},{r1["spec_one"]},"{r1["users"]}",{r1["active"]},"[{{'username': 'SPEC-Admin-Test-User', 'email': '', 'first_name': 'SPEC-Admin', 'last_name': 'Test User', 'descr': None}}, {{'username': 'SPEC-Test-User', 'email': '', 'first_name': 'SPEC-User', 'last_name': 'Test', 'descr': None}}]"
{r2["role"]},{r2["descr"]},{r2["spec_one"]},{r2["users"]},{r2["active"]},"[{{'username': 'SPEC-Admin-Test-User', 'email': '', 'first_name': 'SPEC-Admin', 'last_name': 'Test User', 'descr': None}}]"
'''
        response = self.get_request('/role/?role=Op&output_csv=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.filename,  'role_list.csv')
        stream = b''.join(response.streaming_content)
        self.assertEqual(expected,  stream.decode().replace('\r',''))

        # Error: Update role with spec_one a number (not a boolean)
        response = self.put_request(f'/role/{tr.role_put_1["role"]}', tr.role_put_err_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        self.assert_schema_err(response.content, 'spec_one')

        # Update role
        response = self.put_request(f'/role/{tr.role_put_1["role"]}', tr.role_put_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        # Get updated role
        response = self.get_request(f'/role/{tr.role_put_1["role"]}')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(len(resp['user_arr']), 1)
        self.assertEqual(resp['user_arr'][0]['descr'], 'Corporate')
        del resp['user_arr']
        self.assertEqual(resp, tr.role_put_1)

        # Error: permissions
        response = self.delete_request(f'/role/{tr.role_put_1["role"]}')
        self.assert_auth_error(response, 'NO_AUTH')
        response = self.delete_request(f'/role/{tr.role_put_1["role"]}', auth_lvl='USER')
        self.assert_auth_error(response, 'PERM_DENIED')

        # Delete updated role
        response = self.delete_request(f'/role/{tr.role_put_1["role"]}', auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 204)

        # Get deleted role
        response = self.get_request(f'/role/{tr.role_put_1["role"]}')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], f"Role ({tr.role_put_1['role']}) does not exist.")


    def test_dept(self):
        # Load needed roles
        response = self.post_request('/role/', tr.role_post_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        response = self.post_request('/role/', tr.role_post_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        response = self.post_request('/role/', tr.role_post_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        response = self.post_request('/dept/', tr.dept_post_1, auth_lvl='USER')
        self.assert_auth_error(response, 'PERM_DENIED')

        response = self.post_request('/dept/', tr.dept_post_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        response = self.post_request('/dept/', tr.dept_post_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        response = self.post_request('/dept/', tr.dept_post_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        # Duplicate - Treats as an update
        response = self.post_request('/dept/', tr.dept_post_1a, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        # Get updated dept
        response = self.get_request(f'/dept/{tr.dept_post_1a["name"]}')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(resp, tr.dept_post_1a)

        # Error - invalid character in dept name
        err_body = copy.deepcopy(tr.dept_post_1)
        err_body['name'] = 'Name with Space'
        response = self.post_request('/dept/', err_body, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('Department names cannot contain special characters', resp['error'])

        # Error - dept name missing
        err_body['name'] = None
        response = self.post_request('/dept/', err_body, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        self.assert_schema_err(response.content, 'name')

        # List all depts with 'Op' in name
        response = self.get_request('/dept/?name=Op')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(resp, self.paginate_results([tr.dept_post_2, tr.dept_post_3]))

        # Get sunset list to a csv
        r1 = tr.dept_post_2
        r2 = tr.dept_post_3
        expected=f'''name,readRoles,active
{r1["name"]},{r1["readRoles"]},{r1["active"]}
{r2["name"]},{r2["readRoles"]},{r2["active"]}
'''
        response = self.get_request('/dept/?name=Op&output_csv=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.filename,  'dept_list.csv')
        stream = b''.join(response.streaming_content)
        self.assertEqual(expected,  stream.decode().replace('\r',''))

        # Error: Update dept with readRoles as number (not a str)
        response = self.put_request(f'/dept/{tr.dept_put_1["name"]}', tr.dept_put_err_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        self.assert_schema_err(response.content, 'readRoles')

        # Error: Update dept with readRoles incl BadRole
        response = self.put_request(f'/dept/{tr.dept_put_1["name"]}', tr.dept_put_err_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('Role: BadRole does not exist.', resp['error'])

        # Update dept
        response = self.put_request(f'/dept/{tr.dept_put_1["name"]}', tr.dept_put_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        # Get updated dept
        response = self.get_request(f'/dept/{tr.dept_put_1["name"]}')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(resp, tr.dept_put_1)

        # Error: permissions
        response = self.delete_request(f'/dept/{tr.dept_put_1["name"]}')
        self.assert_auth_error(response, 'NO_AUTH')
        response = self.delete_request(f'/dept/{tr.dept_put_1["name"]}', auth_lvl='USER')
        self.assert_auth_error(response, 'PERM_DENIED')

        # Delete updated dept
        response = self.delete_request(f'/dept/{tr.dept_put_1["name"]}', auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 204)

        # Get deleted dept
        response = self.get_request(f'/dept/{tr.dept_put_1["name"]}')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], f"Department ({tr.dept_put_1['name']}) does not exist.")

    def test_doctype(self):
        response = self.post_request('/doctype/', tr.doctype_post_1, auth_lvl='USER')
        self.assert_auth_error(response, 'PERM_DENIED')

        response = self.post_request('/doctype/', tr.doctype_post_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        response = self.post_request('/doctype/', tr.doctype_post_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        response = self.post_request('/doctype/', tr.doctype_post_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        # Duplicate - Treats as an update
        response = self.post_request('/doctype/', tr.doctype_post_1a, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        response = self.get_request(f'/doctype/{tr.doctype_post_1a["name"]}')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        resp.pop('jira_temp_url_base', None)
        self.assertEqual(resp, tr.doctype_post_1a)

        # Error - invalid character in doctype name
        err_body = copy.deepcopy(tr.doctype_post_1)
        err_body['name'] = 'Name with Space'
        response = self.post_request('/doctype/', err_body, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('Document Type names cannot contain special characters', resp['error'])

        # Error - doctype name missing
        err_body['name'] = None
        response = self.post_request('/doctype/', err_body, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        self.assert_schema_err(response.content, 'name')

        # List all doctypes with 'Op' in descr
        response = self.get_request('/doctype/?descr=Op')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        expected = self.paginate_results([tr.doctype_post_1a, tr.doctype_post_2])
        for e in expected['results']:
            if e['jira_temp'] is not None and len(e['jira_temp']) > 0 \
                and settings.JIRA_URI is not None and len(settings.JIRA_URI) > 0:
                e['jira_temp_url'] = f'{settings.JIRA_URI}/browse/{e["jira_temp"]}'
            if settings.JIRA_URI is not None or len(settings.JIRA_URI) > 0:
                e['jira_temp_url_base'] = f'{settings.JIRA_URI}/browse/'
        self.assertEqual(resp, expected)

        # List all doctypes with 'Op' in descr to a csv
        r1 = expected['results'][0]
        r2 = expected['results'][1]
        expected=f'''name,descr,confidential,jira_temp,sunset_interval,sunset_warn,active,jira_temp_url_base
{r1["name"]},{r1["descr"]},{r1["confidential"]},{r1["jira_temp"]},{r1["sunset_interval"] if r1["sunset_interval"] else ''},{r1["sunset_warn"] if r1["sunset_warn"] else ''},{r1["active"]},{settings.JIRA_URI}/browse/
{r2["name"]},{r2["descr"]},{r2["confidential"]},{r2["jira_temp"]},{r2["sunset_interval"] if r2["sunset_interval"] else ''},{r2["sunset_warn"] if r2["sunset_warn"] else ''},{r2["active"]},{settings.JIRA_URI}/browse/
'''
        response = self.get_request('/doctype/?descr=Op&output_csv=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.filename,  'doc_type_list.csv')
        stream = b''.join(response.streaming_content)
        self.assertEqual(expected,  stream.decode().replace('\r',''))

        # Error: Update doctype with readRoles as number (not a str)
        response = self.put_request(f'/doctype/{tr.doctype_put_1["name"]}', tr.doctype_put_err_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        self.assert_schema_err(response.content, 'confidential')

        # Update doctype
        response = self.put_request(f'/doctype/{tr.doctype_put_1["name"]}', tr.doctype_put_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        # Get updated doctype
        response = self.get_request(f'/doctype/{tr.doctype_put_1["name"]}')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        expected = copy.deepcopy(tr.doctype_put_1)
        if expected['jira_temp'] is not None and len(expected['jira_temp']) > 0 \
            and settings.JIRA_URI is not None and len(settings.JIRA_URI) > 0:
            expected['jira_temp_url'] = f'{settings.JIRA_URI}/browse/{expected["jira_temp"]}'
        if settings.JIRA_URI is not None or len(settings.JIRA_URI) > 0:
            expected['jira_temp_url_base'] = f'{settings.JIRA_URI}/browse/'
        self.assertEqual(resp, expected)

        # Update doctype (sunset values are 0)
        response = self.put_request(f'/doctype/{tr.doctype_put_3["name"]}', tr.doctype_put_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        # Get updated doctype
        response = self.get_request(f'/doctype/{tr.doctype_put_3["name"]}')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(resp['sunset_interval'], None)
        self.assertEqual(resp['sunset_warn'], None)

        # Update doctype SOP to not be confidential
        response = self.put_request(f'/doctype/{tr.doctype_put_2["name"]}', tr.doctype_put_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        # Test qsFilter filter calls
        response = self.get_request('/doctype/?name=obsolete')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(len(resp['results']), 0)

        response = self.get_request('/doctype/?name=!')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(len(resp['results']), 0)

        response = self.get_request('/doctype/?name=*&confidential=true')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(len(resp['results']), 2)

        response = self.get_request('/doctype/?name=!!')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(len(resp['results']), 3)

        response = self.get_request('/doctype/?name=^')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(len(resp['results']), 3)

        response = self.get_request('/doctype/?name=^$')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(len(resp['results']), 3)

        response = self.get_request('/doctype/?name=^HR-Confidential$&orderBy=name')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(len(resp['results']), 1)

        response = self.get_request('/doctype/?name=')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(len(resp['results']), 3)

        # Error: permissions
        response = self.delete_request(f'/doctype/{tr.doctype_put_1["name"]}')
        self.assert_auth_error(response, 'NO_AUTH')
        response = self.delete_request(f'/doctype/{tr.doctype_put_1["name"]}', auth_lvl='USER')
        self.assert_auth_error(response, 'PERM_DENIED')

        # Delete updated doctype
        response = self.delete_request(f'/doctype/{tr.doctype_put_1["name"]}', auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 204)

        # Get deleted doctype
        response = self.get_request(f'/doctype/{tr.doctype_put_1["name"]}')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], f"DocType ({tr.doctype_put_1['name']}) does not exist.")


    def test_approvalmatrix(self):
        # Load needed roles
        response = self.post_request('/role/', tr.role_post_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        response = self.post_request('/role/', tr.role_post_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        response = self.post_request('/role/', tr.role_post_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        # Load needed Departments
        response = self.post_request('/dept/', tr.dept_post_0, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        response = self.post_request('/dept/', tr.dept_post_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        response = self.post_request('/dept/', tr.dept_post_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        # Load needed Doc Types
        response = self.post_request('/doctype/', tr.doctype_post_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        response = self.post_request('/doctype/', tr.doctype_post_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        response = self.post_request('/doctype/', tr.doctype_post_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        response = self.post_request('/approvalmatrix/', tr.approvalmatrix_post_1, auth_lvl='USER')
        self.assert_auth_error(response, 'PERM_DENIED')

        response = self.post_request('/approvalmatrix/', tr.approvalmatrix_post_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        response = self.get_request('/approvalmatrix/?department=__Generic__')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        r0_id = copy.deepcopy(resp['results'][0]["id"])

        response = self.post_request('/approvalmatrix/', tr.approvalmatrix_post_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        response = self.post_request('/approvalmatrix/', tr.approvalmatrix_post_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        # Duplicate - Treats as an update
        response = self.post_request('/approvalmatrix/', tr.approvalmatrix_post_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        # Error: Update approvalmatrix with signRoles as an object (not a str)
        response = self.post_request(f'/approvalmatrix/', tr.approvalmatrix_put_err_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        self.assert_schema_err(response.content, 'signRoles')

        # List all approvalmatrixs with 'Op' in dept
        response = self.get_request('/approvalmatrix/?department=Ops')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        r1 = copy.deepcopy(resp['results'][0])
        r2 = copy.deepcopy(resp['results'][1])
        resp['results'] = self.delete_list_attribs(resp['results'], ['id'])
        expected = self.paginate_results([tr.approvalmatrix_post_2, tr.approvalmatrix_post_3])
        self.assertEqual(resp, expected)

        # Get sunset list to a csv
        expected=f'''id,doc_type,department,signRoles
{r1["id"]},{r1["doc_type"]},{r1["department"]},{r1["signRoles"]}
{r2["id"]},{r2["doc_type"]},{r2["department"]},{r2["signRoles"]}
'''
        response = self.get_request('/approvalmatrix/?department=Ops&output_csv=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.filename,  'approvalmatrix.csv')
        stream = b''.join(response.streaming_content)
        self.assertEqual(expected,  stream.decode().replace('\r',''))

        # Delete with post
        response = self.post_request(f'/approvalmatrix/', tr.approvalmatrix_post_3_delete, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        # List all approvalmatrixs with 'Op' in dept
        response = self.get_request('/approvalmatrix/?department=Ops')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        resp['results'] = self.delete_list_attribs(resp['results'], ['id'])
        expected = self.paginate_results([tr.approvalmatrix_post_2])
        self.assertEqual(resp, expected)

        # Error: Update approvalmatrix with signRoles as an object (not a str)
        response = self.put_request(f'/approvalmatrix/{r0_id}', tr.approvalmatrix_put_err_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        self.assert_schema_err(response.content, 'signRoles')

        # Error: Update approvalmatrix with BadDocType
        response = self.put_request(f'/approvalmatrix/{r0_id}', tr.approvalmatrix_put_err_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], 'Document Type: BadDocType does not exist.')

        # Error: Update approvalmatrix with BadDept
        response = self.put_request(f'/approvalmatrix/{r0_id}', tr.approvalmatrix_put_err_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], 'Department: BadDept does not exist.')

        # Error: Update approvalmatrix with BadRole
        response = self.put_request(f'/approvalmatrix/{r0_id}', tr.approvalmatrix_put_err_4, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], 'Role: BadRole does not exist.')

        # Update approvalmatrix
        response = self.put_request(f'/approvalmatrix/{r0_id}', tr.approvalmatrix_put_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        # Get updated approvalmatrix
        response = self.get_request(f'/approvalmatrix/{r0_id}')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        resp = self.delete_attribs(resp, ['id'])
        self.assertEqual(resp, tr.approvalmatrix_put_1)

        # Error: permissions
        response = self.delete_request(f'/approvalmatrix/{r0_id}')
        self.assert_auth_error(response, 'NO_AUTH')
        response = self.delete_request(f'/approvalmatrix/{r0_id}', auth_lvl='USER')
        self.assert_auth_error(response, 'PERM_DENIED')

        # Delete updated approvalmatrix
        response = self.delete_request(f'/approvalmatrix/{r0_id}', auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 204)

        # Get deleted approvalmatrix
        response = self.get_request(f'/approvalmatrix/{r0_id}')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], f'ApprovalMatrix ({r0_id}) does not exist.')

    def test_roleSpecOne(self):
        response = self.post_request('/role/', tr.role_post_4, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        response = self.get_request(f'/role/{tr.role_post_4["role"]}', auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(resp['spec_one'], True)

        response = self.put_request(f'/role/{tr.role_post_4["role"]}', tr.role_post_4, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(resp['spec_one'], True)


    def test_location(self):
        response = self.post_request('/loc/', tr.loc_post_1, auth_lvl='USER')
        self.assert_auth_error(response, 'PERM_DENIED')

        response = self.post_request('/loc/', tr.loc_post_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        response = self.post_request('/loc/', tr.loc_post_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        response = self.post_request('/loc/', tr.loc_post_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        # Duplicate - Performs an update
        response = self.post_request('/loc/', tr.loc_post_2a, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        # Get location detail
        response = self.get_request(f'/loc/{tr.loc_post_1["name"]}')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(resp, tr.loc_post_1)

        # Error - invalid character in loc name
        err_body = copy.deepcopy(tr.loc_post_1)
        err_body['name'] = 'Name with dollar ($)'
        response = self.post_request('/loc/', err_body, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('Location names cannot contain special characters', resp['error'])

        # Error - loc name missing
        err_body['name'] = None
        response = self.post_request('/loc/', err_body, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        self.assert_schema_err(response.content, 'name')

        # List all locs with 'Corporate' in name
        response = self.get_request('/loc/?name=Corporate')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        expected = self.paginate_results([tr.loc_post_1, tr.loc_post_2a])
        self.assertEqual(resp, expected)

        # List all locs with 'Corporate' in name to a csv
        r1 = expected['results'][0]
        r2 = expected['results'][1]
        expected=f'''name,active
{r1["name"]},{r1["active"]}
{r2["name"]},{r2["active"]}
'''
        response = self.get_request('/loc/?name=Corporate&output_csv=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.filename,  'loc_list.csv')
        stream = b''.join(response.streaming_content)
        self.assertEqual(expected,  stream.decode().replace('\r',''))

        # Error: permissions
        response = self.delete_request(f'/loc/{tr.loc_post_1["name"]}')
        self.assert_auth_error(response, 'NO_AUTH')
        response = self.delete_request(f'/loc/{tr.loc_post_1["name"]}', auth_lvl='USER')
        self.assert_auth_error(response, 'PERM_DENIED')

        # Update location
        response = self.put_request(f'/loc/{tr.loc_put_1["name"]}', tr.loc_put_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        # Get location detail
        response = self.get_request(f'/loc/{tr.loc_put_1["name"]}')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(resp, tr.loc_put_1)

        # Error: Update doctype with active as a number
        response = self.put_request(f'/loc/{tr.loc_err_1["name"]}', tr.loc_err_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        self.assert_schema_err(response.content, 'active')

        # Delete updated loc
        response = self.delete_request(f'/loc/{tr.loc_post_1["name"]}', auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 204)

        # Get deleted loc
        response = self.get_request(f'/loc/{tr.loc_post_1["name"]}')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], f"Location: {tr.loc_post_1['name']} does not exist.")


    def test_session_timeout(self):
        """Test that session timeout is based on inactive time."""

        settings.SESSION_IDLE_TIMEOUT = 2 # Set session timeout to 2 seconds
        resp = self.client.get('/accounts/login/')
        tok = resp.cookies['csrftoken'].value
        # Login via csrf token + djagno LDAP
        auth_body = {'username': os.getenv('ADMIN_USER'), 'password': os.getenv('ADMIN_PASSWD')}
        response = self.client.post('/accounts/login/', auth_body)
        self.assertEqual(response.status_code, 302)

        # Set token
        headers = {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': tok,
                }

        response = self.post_request('/role/', tr.role_post_4, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        sleep(1)
        response = self.client.put(path=f'/role/{tr.role_post_4["role"]}', data=tr.role_post_4, content_type='application/json', **headers)
        self.assertEqual(response.status_code, 200)

        sleep(1)
        response = self.client.put(path=f'/role/{tr.role_post_4["role"]}', data=tr.role_post_4, content_type='application/json', **headers)
        self.assertEqual(response.status_code, 200)

        sleep(1)
        response = self.client.put(path=f'/role/{tr.role_post_4["role"]}', data=tr.role_post_4, content_type='application/json', **headers)
        self.assertEqual(response.status_code, 200)

        sleep(3)
        response = self.client.put(path=f'/role/{tr.role_post_4["role"]}', data=tr.role_post_4, content_type='application/json', **headers)
        self.assertEqual(response.status_code, 401)