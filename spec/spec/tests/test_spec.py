import copy, json, os, html, time
from django.conf import settings
from spec.models import Spec
from spec.services import revletter
from utils.test_utils import SpecTestCase
from . import conf_resources as conf
from . import spec_resources as spec

class SpecTest(SpecTestCase):

    def post_conf(self):
        # Load needed roles
        response = self.post_request('/role/', conf.role_post_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        response = self.post_request('/role/', conf.role_post_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        response = self.post_request('/role/', conf.role_post_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        # Load needed Departments
        response = self.post_request('/dept/', conf.dept_post_0, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        response = self.post_request('/dept/', conf.dept_post_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        response = self.post_request('/dept/', conf.dept_post_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        # Load needed Doc Types
        response = self.post_request('/doctype/', conf.doctype_post_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        response = self.post_request('/doctype/', conf.doctype_post_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        response = self.post_request('/doctype/', conf.doctype_post_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        # Load needed Approval Matricies
        response = self.post_request('/approvalmatrix/', conf.approvalmatrix_post_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        response = self.post_request('/approvalmatrix/', conf.approvalmatrix_post_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        # Load needed Locations
        response = self.post_request('/loc/', conf.loc_post_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

    def test_spec(self):
        self.post_conf()

        spec_ids = []

        response = self.post_request('/spec/', spec.spec_post_1, auth_lvl='USER')
        self.assertEqual(response.status_code, 201)
        resp = json.loads(response.content)
        resp_post_1 = resp
        spec_ids.append(resp['num'])

        response = self.post_request('/spec/', spec.spec_post_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        resp = json.loads(response.content)
        spec_ids.append(resp['num'])

        # List all specs with first number
        response = self.get_request(f'/spec/?num={spec_ids[0]}')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        spec_resp_get_1 = copy.deepcopy(resp["results"][0])
        resp['results'] = self.delete_list_attribs(resp['results'], ['create_dt', 'mod_ts', ])
        spec_get_1 = copy.deepcopy(spec.spec_get_list_1)
        spec_get_1['num'] = spec_ids[0]
        self.assertEqual(resp, self.paginate_results([spec_get_1]))

        # List all specs with first number
        response = self.get_request(f'/spec/{spec_ids[0]}')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        resp['results'] = self.delete_list_attribs(resp['results'], ['create_dt', 'mod_ts', ])
        self.assertEqual(resp, self.paginate_results([spec_get_1]))

        # List all specs with 'Spec Creation' in title'
        response = self.get_request(f'/spec/?title=Spec%20Creation')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        resp['results'] = self.delete_list_attribs(resp['results'], ['create_dt', 'mod_ts', ])
        self.assertEqual(resp, self.paginate_results([spec_get_1]))

        # List all specs with 'two' in keywords'
        response = self.get_request(f'/spec/?keywords=two')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        spec_resp_get_2 = copy.deepcopy(resp["results"][0])
        resp['results'] = self.delete_list_attribs(resp['results'], ['create_dt', 'mod_ts'])
        spec_get_2 = copy.deepcopy(spec.spec_get_list_2)
        spec_get_2['num'] = spec_ids[1]
        self.assertEqual(resp, self.paginate_results([spec_get_2]))

        # List all specs with 'Draft' in state
        response = self.get_request(f'/spec/?state=Draft')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        resp['results'] = self.delete_list_attribs(resp['results'], ['create_dt', 'mod_ts'])
        self.assertEqual(resp, self.paginate_results([spec_get_1, spec_get_2]))

        # Download specs with 'Draft' in state to a csv
        expected=f'''num,ver,title,doc_type,department,keywords,state,created_by,create_dt,mod_ts,jira,anon_access,reason,approved_dt,sunset_extended_dt,sunset_dt,sunset_warn_dt,location,first_submit_dt,last_submit_dt,reject_cnt,admin_upd_cnt,missing_sigs,watched
{spec_resp_get_1["num"]},A,"SOP, Spec Creation",SOP,Ops:Line1,keyword one,Draft,SPEC-Test-User,{spec_resp_get_1["create_dt"]},{spec_resp_get_1["mod_ts"]},,False,Initial Version,,,,,Corporate,,,0,0,,False
{spec_resp_get_2["num"]},A,"WI, Route Spec",WI,Ops,keyword two,Draft,SPEC-Admin-Test-User,{spec_resp_get_2["create_dt"]},{spec_resp_get_2["mod_ts"]},,False,Initial Version,,,,,,,,0,0,,False
'''
        response = self.get_request(f'/spec/?state=Draft&output_csv=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.filename,  'spec_list.csv')
        stream = b''.join(response.streaming_content)
        self.assertEqual(expected,  stream.decode().replace('\r',''))

        # List all specs created by spec user
        response = self.get_request(f'/spec/?created_by={os.getenv("USER_USER")}')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        resp['results'] = self.delete_list_attribs(resp['results'], ['create_dt', 'mod_ts'])
        self.assertEqual(resp, self.paginate_results([spec_get_1]))

        # Error: Not logged in
        response = self.get_request(f'/spec/{spec_ids[0]}/A')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], f"spec {spec_ids[0]}-A cannot read without logging in.")

        # Get first spec
        response = self.get_request(f'/spec/{spec_ids[0]}/A', auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        resp = self.delete_attribs(resp, ['create_dt', 'mod_ts'])
        spec_get_1 = copy.deepcopy(spec.spec_get_detail_1)
        spec_get_1['num'] = spec_ids[0]
        self.assertEqual(resp, spec_get_1)

        # Error: Update spec with title an object (not a string)
        response = self.put_request(f'/spec/{spec_ids[0]}/A', spec.spec_put_err_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        self.assert_schema_err(response.content, 'title')

        # Add a valid reference to the put body
        spec.spec_put_1['refs'] = [{'num':spec_ids[1], 'ver':'A'}]

        # Error: Update spec - change state w/o admin
        response = self.put_request(f'/spec/{spec_ids[0]}/A', spec.spec_put_1, auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], 'State changes via update can only be done by an administrator.')

        # Error: Update spec - change created_by w/o admin
        response = self.put_request(f'/spec/{spec_ids[0]}/A', spec.spec_put_err_3, auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], 'Created By changes via update can only be done by an administrator.')

        # Error: Update spec - change state w/o comment
        response = self.put_request(f'/spec/{spec_ids[0]}/A', spec.spec_put_err_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], 'State changes updates require a comment.')

        # Add two files for reposition on update
        with open('spec/tests/test_files/Text1.docx', 'rb') as fp:
            response = self.post_binary_request(f'/file/{spec_ids[0]}/A', {'file':(fp, 'Text1.docx')},  auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        with open('spec/tests/test_files/torch.jpg', 'rb') as fp:
            response = self.post_binary_request(f'/file/{spec_ids[0]}/A', {'file':(fp, 'torch.jpg')},  auth_lvl='USER')
        self.assertEqual(response.status_code, 200)

        # Update spec - change state to Active
        response = self.put_request(f'/spec/{spec_ids[0]}/A', spec.spec_put_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(resp['state'], 'Active')
        self.assertEqual(resp['create_dt'], resp_post_1['create_dt'])
        self.assertEqual(resp['created_by'], spec.spec_put_1['created_by'])
        self.assertNotEqual(resp['mod_ts'], resp_post_1['mod_ts'])
        self.assertEqual(len(resp['hist']), 3)
        self.assertEqual(resp['hist'][2]['upd_by'], os.getenv("ADMIN_USER"))
        self.assertEqual(resp['hist'][2]['change_type'], 'Admin Update')
        self.assertEqual(resp['hist'][2]['comment'], f'Created By changed from {resp_post_1["created_by"]} to {spec.spec_put_1["created_by"]}', spec.spec_put_1['comment'])
        self.assertEqual(resp['hist'][1]['upd_by'], os.getenv("ADMIN_USER"))
        self.assertEqual(resp['hist'][1]['change_type'], 'Admin Update')
        self.assertEqual(resp['hist'][1]['comment'], 'Admin update made while spec in state: Active', spec.spec_put_1['comment'])
        self.assertEqual(resp['hist'][0]['upd_by'], os.getenv("ADMIN_USER"))
        self.assertEqual(resp['hist'][0]['change_type'], 'Update')
        self.assertEqual(resp['hist'][0]['comment'], spec.spec_put_1['comment'])
        self.assertEqual(len(resp['files']), 2)
        self.assertEqual(resp['files'][0]['seq'], 1)
        self.assertEqual(resp['files'][0]['filename'], 'torch.jpg')
        self.assertEqual(resp['files'][0]['incl_pdf'], False)
        self.assertEqual(resp['files'][1]['seq'], 2)
        self.assertEqual(resp['files'][1]['filename'], 'Text1.docx')
        self.assertEqual(resp['files'][1]['incl_pdf'], True)
        self.assertEqual(resp['refs'], [{'num': spec_ids[1], 'ver': 'A'}])

        # List filtered to same spec
        response = self.get_request(f'/spec/?num={spec_ids[0]}&ver=A')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(1, resp["count"])
        self.assertEqual(2, resp["results"][0]["admin_upd_cnt"])

        # Update spec - change state back to Draft to catch signer changes
        response = self.put_request(f'/spec/{spec_ids[0]}/A', spec.spec_put_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(resp['state'], 'Draft')
        self.assertEqual(len(resp['hist']), 4)
        self.assertEqual(resp['hist'][0]['upd_by'], os.getenv("ADMIN_USER"))
        self.assertEqual(resp['hist'][0]['change_type'], 'Update')
        self.assertEqual(resp['hist'][0]['comment'], spec.spec_put_2['comment'])
        self.assertEqual(resp['hist'][1]['upd_by'], os.getenv("ADMIN_USER"))
        self.assertEqual(resp['hist'][1]['change_type'], 'Update')
        self.assertEqual(resp['hist'][1]['comment'], spec.spec_put_1['comment'])
        self.assertEqual(len(resp['files']), 2)
        self.assertEqual(resp['refs'], [])
        self.assertEqual(resp['sigs'],
            [{'role': conf.role_post_3['role'], 'signed_dt': None, 'from_am': True, 'spec_one': True, 'signer': None, 'delegate': None},
            {'role': conf.role_post_1['role'], 'signed_dt': None, 'from_am': True, 'spec_one': False, 'signer': os.getenv("USER_USER"), 'delegate': None},
            {'role': conf.role_post_2['role'], 'signed_dt': None, 'from_am': False, 'spec_one': True, 'signer': os.getenv("ADMIN_USER"), 'delegate': None}]
        )
        self.assertEqual(resp['jira'], "TEST-1")
        self.assertEqual(resp['jira_url'], f'{settings.JIRA_URI}/browse/TEST-1')

        # Update spec - change state to Active
        response = self.put_request(f'/spec/{spec_ids[0]}/A', spec.spec_put_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        # Error: Update spec - change state w/o admin
        response = self.put_request(f'/spec/{spec_ids[0]}/A', spec.spec_put_1, auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], 'Spec is not in Draft state, it cannot be edited.')

        # Error: permissions
        response = self.delete_request(f'/spec/{spec_ids[0]}/A')
        self.assert_auth_error(response, 'NO_AUTH')
        response = self.delete_request(f'/spec/{spec_ids[0]}/A', auth_lvl='USER')
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], 'Spec is not in Draft state. Cannot delete.')

        # Error: Create new revision - no reason
        response = self.post_request(f'/spec/{spec_ids[0]}/A', {}, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        self.assert_schema_err(response.content, 'reason')

        # Create new revision
        response = self.post_request(f'/spec/{spec_ids[0]}/A', spec.spec_revise_post_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        resp = json.loads(response.content)
        self.assertEqual(resp['ver'], 'B')
        self.assertEqual(resp['state'], 'Draft')
        self.assertEqual(resp['reason'], spec.spec_revise_post_1['reason'])
        self.assertNotEqual(resp['create_dt'], resp_post_1['create_dt'])
        self.assertNotEqual(resp['created_by'], resp_post_1['created_by'])
        self.assertNotEqual(resp['mod_ts'], resp_post_1['mod_ts'])

        # Delete updated spec
        response = self.delete_request(f'/spec/{spec_ids[0]}/B', auth_lvl='USER')
        self.assertEqual(response.status_code, 204)

        # Get deleted spec
        response = self.get_request(f'/spec/{spec_ids[0]}/B', auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], f'Spec ({spec_ids[0]}/B) does not exist.')

        # Import spec as user
        response = self.post_request('/importSpec/', spec.spec_import_post_1, auth_lvl='USER')
        self.assert_auth_error(response, 'PERM_DENIED')

        # Remove spec num
        spec_err_post = copy.deepcopy(spec.spec_import_post_1)
        spec_err_post.pop('num')
        response = self.post_request('/importSpec/', spec_err_post, auth_lvl='ADMIN')
        self.assert_schema_err(response.content, 'num')

        # Bad revision
        spec_err_post = copy.deepcopy(spec.spec_import_post_1)
        spec_err_post['ver'] = '01'
        response = self.post_request('/importSpec/', spec_err_post, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], "Ver can only contain uppercase letters.")

        self.assertFalse(revletter.valid_rev({}))

        # Import new spec
        response = self.post_request('/importSpec/', spec.spec_import_post_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        # Import new spec - second time to hit Document.lookupOrCreate (doctype exists)
        response = self.post_request('/importSpec/', spec.spec_import_post_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        # Get imported spec
        response = self.get_request(f'/spec/400000/B', auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        for key, value in spec.spec_import_post_1.items():
            self.assertIn(key, resp)
            self.assertEqual(resp[key], value)
        self.assertEqual(resp['created_by'], os.getenv('ADMIN_USER'))
        self.assertEqual(resp['hist'][0]['change_type'], 'Import')
        self.assertEqual(resp['hist'][0]['comment'], 'Initial Load')

        # Try and get Draft spec without specifying revision
        response = self.get_request(f'/spec/400000/*', auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], 'No active version of Spec (400000).')

        # Import existing spec
        spec_import = copy.deepcopy(spec.spec_import_post_2)
        spec_import['num'] = spec_ids[1]
        spec_import['jira_create'] = True
        spec_import['created_by'] = os.getenv('USER_USER')
        response = self.post_request('/importSpec/', spec_import, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        # Get imported spec
        response = self.get_request(f'/spec/{spec_ids[1]}/A', auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        for key, value in spec.spec_import_post_2.items():
            self.assertIn(key, resp)
            self.assertEqual(resp[key], value)
        self.assertEqual(resp['created_by'], os.getenv('USER_USER'))
        self.assertEqual(resp['hist'][0]['change_type'], 'Import')
        self.assertEqual(resp['hist'][0]['comment'], 'Initial Load')

        # Get Active spec without specifying revision
        response = self.get_request(f'/spec/{spec_ids[1]}/*', auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(resp['created_by'], os.getenv('USER_USER'))
        self.assertEqual(resp['hist'][0]['change_type'], 'Import')
        self.assertEqual(resp['hist'][0]['comment'], 'Initial Load')

        # Remove user from Read Role
        response = self.put_request(f'/role/{conf.role_put_1["role"]}', conf.role_put_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        response = self.get_request(f'/spec/{spec_ids[1]}/A', auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], f'User {os.getenv("USER_USER")} cannot read confidential specs in department HR.')

        # Update doc_type to WI. With an Active spec will trigger sunset
        spec_import['doc_type'] = 'WI'
        response = self.post_request('/importSpec/', spec_import, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        resp = json.loads(response.content)
        self.assertEqual(resp['state'], 'Obsolete')

        # Reset the state to Active to hit a specific branch of spec.models.lookup()
        specToUpdate = Spec.objects.get(num=spec_ids[1], ver='A')
        specToUpdate.state = 'Active'
        specToUpdate.save()

        response = self.get_request(f'/spec/{spec_ids[1]}/*', auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertEqual(resp['error'], f'No active version of Spec ({spec_ids[1]}).')

    def test_spec_create(self):
        self.post_conf()

        # Post spec with no auth
        response = self.post_request('/spec/', spec.spec_post_1)
        self.assert_auth_error(response, 'NO_AUTH')

        # Error - title missing
        err_body = copy.deepcopy(spec.spec_post_1)
        err_body['title'] = None
        response = self.post_request('/spec/', err_body, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        self.assert_schema_err(response.content, 'title')

        # Post spec with num as user
        spec_post = copy.deepcopy(spec.spec_post_1)
        spec_post['num'] = 1
        response = self.post_request('/spec/', spec_post, auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('error', resp)
        self.assertEqual(resp['error'], "Only Admins can create a spec with a specific number")

        # Post spec with num and no version
        response = self.post_request('/spec/', spec_post, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('error', resp)
        self.assertEqual(resp['error'], "Ver must be specified, when Num is specified")

        # Post spec with numeric version
        spec_post['ver'] = '01'
        response = self.post_request('/spec/', spec_post, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('error', resp)
        self.assertEqual(resp['error'], "Ver can only contain uppercase letters.")

        # Re-add version
        spec_post['ver'] = 'A'
        response = self.post_request('/spec/', spec_post, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        # Post spec with same number
        response = self.post_request('/spec/', spec_post, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('error', resp)
        self.assertEqual(resp['error'], "Num 1 is already used in the system.")

        response = self.get_request(f'/spec/1/A', auth_lvl='USER')
        spec_get_1 = copy.deepcopy(spec.spec_get_detail_1)
        spec_get_1['num'] = 1
        spec_get_1['created_by'] = 'SPEC-Admin-Test-User'
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        resp = self.delete_attribs(resp, ['create_dt', 'mod_ts', ])
        self.assertEqual(resp, spec_get_1)

    def test_file(self):
        self.post_conf()

        #Create Specs
        spec_ids = []
        response = self.post_request('/spec/', spec.spec_post_1, auth_lvl='USER')
        self.assertEqual(response.status_code, 201)
        resp = json.loads(response.content)

        spec_ids.append(resp['num'])
        response = self.post_request('/spec/', spec.spec_post_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        resp = json.loads(response.content)
        spec_ids.append(resp['num'])

        # Error: Not logged in
        response = self.post_request(f'/file/{spec_ids[0]}/A', {})
        self.assert_auth_error(response, 'NO_AUTH')

        # Error: Missing file
        response = self.post_request(f'/file/{spec_ids[0]}/A', {},auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        self.assert_schema_err(response.content, 'file')

        # Upload Word file
        with open('spec/tests/test_files/Text1.docx', 'rb') as fp:
            response = self.post_binary_request(f'/file/{spec_ids[0]}/A', {'file':(fp, 'Text1.docx')},  auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(len(resp['files']), 1)
        self.assertEqual(resp['files'][0]['seq'], 1)
        self.assertEqual(resp['files'][0]['filename'], 'Text1.docx')
        self.assertEqual(resp['files'][0]['incl_pdf'], False)

        # Upload jpg file
        with open('spec/tests/test_files/torch.jpg', 'rb') as fp:
            response = self.post_binary_request(f'/file/{spec_ids[0]}/A', {'file':(fp, 'torch.jpg')},  auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(len(resp['files']), 2)
        self.assertEqual(resp['files'][0]['seq'], 1)
        self.assertEqual(resp['files'][0]['filename'], 'Text1.docx')
        self.assertEqual(resp['files'][0]['incl_pdf'], False)
        self.assertEqual(resp['files'][1]['seq'], 2)
        self.assertEqual(resp['files'][1]['filename'], 'torch.jpg')
        self.assertEqual(resp['files'][1]['incl_pdf'], False)

        # Upload txt file
        with open('spec/tests/test_files/file_one.txt', 'rb') as fp:
            response = self.post_binary_request(f'/file/{spec_ids[0]}/A', {'file':(fp, 'file_one.txt')},  auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(len(resp['files']), 3)
        self.assertEqual(resp['files'][0]['seq'], 1)
        self.assertEqual(resp['files'][0]['filename'], 'Text1.docx')
        self.assertEqual(resp['files'][0]['incl_pdf'], False)
        self.assertEqual(resp['files'][1]['seq'], 2)
        self.assertEqual(resp['files'][1]['filename'], 'torch.jpg')
        self.assertEqual(resp['files'][1]['incl_pdf'], False)
        self.assertEqual(resp['files'][2]['seq'], 3)
        self.assertEqual(resp['files'][2]['filename'], 'file_one.txt')
        self.assertEqual(resp['files'][2]['incl_pdf'], False)

        # Delete file
        response = self.delete_request(f'/file/{spec_ids[0]}/A/torch.jpg', auth_lvl='USER')
        self.assertEqual(response.status_code, 204)

        # Error: get deleted file
        response = self.get_request(f'/file/{spec_ids[0]}/A/torch.jpg?state=Draft', auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        self.assertIn(f"File torch.jpg is not attached to spec ({spec_ids[0]}/A).", response.content.decode())

        # Get first file on spec
        response = self.get_request(f'/file/{spec_ids[0]}/A?state=Active', auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        self.assertIn(f"Spec ({spec_ids[0]}/A) is Draft, not in Active state.", response.content.decode())

        # Get first file on spec
        response = self.get_request(f'/file/{spec_ids[0]}/A?state=Draft', auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.filename,  'Text1.docx')

        # Get file by name
        with open('spec/tests/test_files/file_one.txt', 'rb') as fp:
            file_content = fp.read()
        response = self.get_request(f'/file/{spec_ids[0]}/A/file_one.txt?state=Draft', auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.filename,  'file_one.txt')
        stream = b''.join(response.streaming_content)
        self.assertEqual(stream,  file_content)

        # Update spec - change state to Active
        response = self.put_request(f'/spec/{spec_ids[0]}/A', spec.spec_put_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        # Add jpg file to active spec
        with open('spec/tests/test_files/torch.jpg', 'rb') as fp:
            response = self.post_binary_request(f'/file/{spec_ids[0]}/A', {'file': (fp, 'torch.jpg')}, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        # Verify admin history comment
        response = self.get_request(f'/spec/{spec_ids[0]}/A', auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertIn('state', resp)
        self.assertEqual(resp['hist'][0]['change_type'], 'Admin Update')
        self.assertEqual(resp['hist'][0]['comment'], 'File torch.jpg added while spec in state: Active')

        # Delete file
        response = self.delete_request(f'/file/{spec_ids[0]}/A/torch.jpg', auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 204)

        # Verify admin history comment
        response = self.get_request(f'/spec/{spec_ids[0]}/A', auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertIn('state', resp)
        self.assertEqual(resp['state'], 'Active')
        self.assertEqual(resp['hist'][0]['change_type'], 'Admin Update')
        self.assertEqual(resp['hist'][0]['comment'], 'File torch.jpg deleted while spec in state: Active')

    def test_sunset(self):
        self.post_conf()

        # Create Spec
        response = self.post_request('/spec/', spec.spec_post_1, auth_lvl='USER')
        self.assertEqual(response.status_code, 201)
        resp = json.loads(response.content)
        spec_num = resp['num']

        # Upload Word file
        with open('spec/tests/test_files/Text1.docx', 'rb') as fp:
            response = self.post_binary_request(f'/file/{spec_num}/A', {'file': (fp, 'Text1.docx')}, auth_lvl='USER')
        self.assertEqual(response.status_code, 200)

        # Update spec - change state to Active
        response = self.put_request(f'/spec/{spec_num}/A', spec.spec_put_1, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        # Update doctype for longer sunset warn interval
        # Set to warn after two seconds
        response = self.put_request(f'/doctype/{spec.spec_post_1["doc_type"]}', conf.doctype_put_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)
        time.sleep(2)

        # Get sunset list
        response = self.get_request(f'/sunset/')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(len(resp), 1)
        self.assertEqual(resp[0]['num'], spec_num)
        self.assertEqual(resp[0]['state'], 'Active')

        # Get sunset list to a csv
        s = resp[0]
        expected=f'''num,ver,title,doc_type,department,keywords,state,created_by,create_dt,mod_ts,jira,anon_access,reason,approved_dt,sunset_extended_dt,sunset_dt,sunset_warn_dt,location,first_submit_dt,last_submit_dt,reject_cnt,admin_upd_cnt,missing_sigs,watched
{s["num"]},{s["ver"]},"{s["title"]}",{s["doc_type"]},{s["department"]},{s["keywords"]},{s["state"]},{s["created_by"]},{s["create_dt"]},{s["mod_ts"]},,False,,{s["approved_dt"]},,{s["sunset_dt"]},{s["sunset_warn_dt"]},,,,0,2,,False
'''
        response = self.get_request(f'/sunset/?output_csv=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.filename,  'sunset_list.csv')
        stream = b''.join(response.streaming_content)
        self.assertEqual(expected,  stream.decode().replace('\r',''))

        # Extend sunset with no auth
        response = self.post_request(f'/extend/{spec_num}/A')
        self.assert_auth_error(response, 'NO_AUTH')

        # Extend sunset with no comment
        response = self.post_request(f'/extend/{spec_num}/A', {}, auth_lvl='USER')
        self.assert_schema_err(response.content, 'comment')

        # Extend sunset
        response = self.post_request(f'/extend/{spec_num}/A', {'comment': 'test sunset extension'}, auth_lvl='USER')
        self.assertEqual(response.status_code, 200)

        # Get sunset list
        response = self.get_request(f'/sunset/')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(len(resp), 0)

        # Re-extend sunset
        response = self.post_request(f'/extend/{spec_num}/A', {'comment': 'test sunset extension'}, auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('error', resp)
        self.assertEqual(resp['error'], "Spec sunset date can only be extended once. Create a new revision.")

        # Update doctype for small sunset interval
        # (Zero sunset interval does not work)
        spec_put = copy.deepcopy(conf.doctype_put_2)
        spec_put['sunset_interval'] = '00:00:00.01'
        response = self.put_request(f'/doctype/{spec.spec_post_1["doc_type"]}', spec_put, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)
        time.sleep(.01)

        # Get sunset list
        response = self.get_request(f'/sunset/')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(len(resp), 1)
        self.assertEqual(resp[0]['num'], spec_num)
        self.assertEqual(resp[0]['state'], 'Obsolete')

        # Extend sunset on obsolete doc
        response = self.post_request(f'/extend/{spec_num}/A', {'comment': 'test sunset extension'}, auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('error', resp)
        self.assertEqual(resp['error'], "Spec must be in Active state to extend sunset period")

    def test_help_file(self):
        response = self.get_request(f'/help/dummy')
        self.assertEqual(response.status_code, 400)
        self.assertIn("Valid help choices are: 'user' for the User Guide, 'admin' for the "
                      "Admin Guide and 'design' for the High Level Design", html.unescape(response.content.decode()))

        response = self.get_request(f'/help/user')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.filename, 'user_guide.pdf')

        response = self.get_request(f'/help/admin')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.filename, 'admin_guide.pdf')

        response = self.get_request(f'/help/design')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.filename, 'high_level_design.pdf')

    def test_user(self):
        response = self.get_request('/user/')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)['results']
        resp = self.delete_list_attribs(resp, ['id'])
        self.assertCountEqual(resp, [spec.user_get_1, spec.user_get_2])

        response = self.get_request(f'/user/?search={os.getenv("ADMIN_USER")}')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)['results']
        resp = self.delete_list_attribs(resp, ['id'])
        self.assertCountEqual(resp, [spec.user_get_1])

        response = self.get_request(f'/user/{os.getenv("ADMIN_USER")}')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        del resp['id']
        self.assertCountEqual(resp, spec.user_get_1)

        # Make spec-user a delegate of spec-admin-user
        response = self.put_request(f'/user/{os.getenv("ADMIN_USER")}', {"delegates": os.getenv('USER_USER')}, auth_lvl='')
        self.assert_auth_error(response, 'NO_AUTH')

        # Make spec-user a delegate of spec-admin-user
        response = self.put_request(f'/user/{os.getenv("ADMIN_USER")}', {"delegates": os.getenv('USER_USER')}, auth_lvl="ADMIN")
        self.assertEqual(response.status_code, 200)

        # Verify spec-user is a delegate of spec-admin-user
        response = self.get_request(f'/user/{os.getenv("ADMIN_USER")}')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(resp['delegates'], os.getenv('USER_USER'))

        # Verify spec-user is a delegate of spec-admin-user
        # TODO: Why is delegates a string and delegates_for a list?
        response = self.get_request(f'/user/{os.getenv("USER_USER")}')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(resp['delegates_for'], [os.getenv('ADMIN_USER')])

        # Add a specs to watch
        self.post_conf()

        spec_ids = []

        response = self.post_request('/spec/', spec.spec_post_1, auth_lvl='USER')
        self.assertEqual(response.status_code, 201)
        resp = json.loads(response.content)
        resp_post_1 = resp
        spec_ids.append(resp['num'])

        response = self.post_request('/spec/', spec.spec_post_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        resp = json.loads(response.content)
        spec_ids.append(resp['num'])

        # Add watch: different user, not admin
        response = self.post_request(f'/user/watch/{os.getenv("ADMIN_USER")}/{spec_ids[0]}', {}, auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn("Only admins can change other's settings.", resp['error'])

        # Add watch, self
        response = self.post_request(f'/user/watch/{os.getenv("USER_USER")}/{spec_ids[0]}', {}, auth_lvl="USER")
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertIn(spec_ids[0], resp['watches'])

        # Add watch, invalid spec
        response = self.post_request(f'/user/watch/{os.getenv("USER_USER")}/000', {}, auth_lvl="USER")
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn("Spec 0 does not exist.", resp['error'])

        # Add watch, as admin
        response = self.post_request(f'/user/watch/{os.getenv("USER_USER")}/{spec_ids[1]}', {}, auth_lvl="ADMIN")
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertIn(spec_ids[0], resp['watches'])
        self.assertIn(spec_ids[1], resp['watches'])

        # Delete watch: different user, not admin
        response = self.delete_request(f'/user/watch/{os.getenv("ADMIN_USER")}/{spec_ids[0]}', {}, auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn("Only admins can change other's settings.", resp['error'])

        # Delete watch, self
        response = self.delete_request(f'/user/watch/{os.getenv("USER_USER")}/{spec_ids[0]}', {}, auth_lvl="USER")
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertNotIn(spec_ids[0], resp['watches'])
        self.assertIn(spec_ids[1], resp['watches'])

        # Delete watch, as admin
        response = self.delete_request(f'/user/watch/{os.getenv("USER_USER")}/{spec_ids[1]}', {}, auth_lvl="ADMIN")
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertNotIn(spec_ids[0], resp['watches'])
        self.assertNotIn(spec_ids[1], resp['watches'])
