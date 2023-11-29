import copy, json, os, mock
from django.contrib.auth.models import User
from django.core import mail
from utils.test_utils import SpecTestCase
from . import conf_resources as conf
from . import spec_resources as spec

# TODO: test created pdf with PyPDF2 https://www.geeksforgeeks.org/working-with-pdf-files-in-python/
# Test page order, content, file not selected not in pdf

# TODO: To change setttings for specific test, use: https://docs.djangoproject.com/en/4.1/topics/testing/tools/#overriding-settings

class RouteTest(SpecTestCase):

    @mock.patch('spec.services.jira.submit')
    @mock.patch('spec.services.jira.active')
    @mock.patch('spec.services.jira.reject')
    def test_submit(self, mocked_submit, mocked_active, mocked_reject):
        mocked_submit.return_value = None
        mocked_active.return_value = None
        mocked_reject.return_value = None

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

        # Post spec with no AM
        response = self.post_request('/spec/', spec.spec_post_2, auth_lvl='USER')
        self.assertEqual(response.status_code, 201)
        resp = json.loads(response.content)
        no_am_spec_num = resp['num']

        # Revise spec while in draft state
        response = self.post_request(f'/spec/{no_am_spec_num}/A', {"reason": "test revision"}, auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('error', resp)
        self.assertEqual(resp['error'], "Version A is in state Draft. Cannot start a new revision.")

        # Add file to spec
        with open('spec/tests/test_files/Text1.docx', 'rb') as fp:
            response = self.post_binary_request(f'/file/{no_am_spec_num}/A', {'file': (fp, 'Text1.docx')}, auth_lvl='USER')
        self.assertEqual(response.status_code, 200)

        # Submit spec with no signatures:
        response = self.post_request(f'/submit/{no_am_spec_num}/A', auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('error', resp)
        self.assertEqual(resp['error'], "Spec must be have at least one signature.")

        # Load spec for submission
        spec_ids = []
        response = self.post_request('/spec/', spec.spec_post_1, auth_lvl='USER')
        self.assertEqual(response.status_code, 201)
        resp = json.loads(response.content)
        spec_ids.append(resp['num'])

        # Submit with no files:
        response = self.post_request(f'/submit/{spec_ids[0]}/A', auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('error', resp)
        self.assertEqual(resp['error'], "Spec must be have at least one attached file.")

        # Add two files
        with open('spec/tests/test_files/Text1.docx', 'rb') as fp:
            response = self.post_binary_request(f'/file/{spec_ids[0]}/A', {'file':(fp, 'Text1.docx')},  auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        with open('spec/tests/test_files/file_one.txt', 'rb') as fp:
            response = self.post_binary_request(f'/file/{spec_ids[0]}/A', {'file':(fp, 'file_one.txt')},  auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        with open('spec/tests/test_files/small_pdf.pdf', 'rb') as fp:
            response = self.post_binary_request(f'/file/{spec_ids[0]}/A', {'file':(fp, 'small_pdf.pdf')},  auth_lvl='USER')
        self.assertEqual(response.status_code, 200)

        # Set email on account, so the email check below will work
        user = User.objects.get(username=os.getenv('USER_USER'))
        user.email = 'user@test.com'
        user.save()

        # Set email on account, so the email check below will work
        user = User.objects.get(username=os.getenv('ADMIN_USER'))
        user.email = 'admin@test.com'
        user.save()

        # Update spec - Add signers. Set file order and incl_pdf
        response = self.put_request(f'/spec/{spec_ids[0]}/A', spec.spec_put_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        # Sign QUAL sig in draft state
        response = self.post_request(f'/sign/{spec_ids[0]}/A', spec.sign_post_1, auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('error', resp)
        self.assertEqual(resp['error'], 'Spec must be in Signoff state to accept signatures')

        # Submit with no auth:
        response = self.post_request(f'/submit/{spec_ids[0]}/A')
        self.assert_auth_error(response, 'NO_AUTH')

        # Submit:
        response = self.post_request(f'/submit/{spec_ids[0]}/A', auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('error', resp)
        self.assertEqual(resp['error'], 'Signer must be specified for Role(s): Op_Line1')

        # Specify signer for op_line1
        # Update spec - Add signers. Set file order and incl_pdf
        spec_put = copy.deepcopy(spec.spec_put_2)
        spec_put['sigs'][-1]['signer'] = os.getenv('ADMIN_USER')
        response = self.put_request(f'/spec/{spec_ids[0]}/A', spec_put, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        # Empty the test outbox
        mail.outbox = []

        # Submit:
        response = self.post_request(f'/submit/{spec_ids[0]}/A', auth_lvl='USER')
        self.assertEqual(response.status_code, 200)

        # Verify spec is in signoff state
        response = self.get_request(f'/spec/{spec_ids[0]}/A', auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertIn('state', resp)
        self.assertEqual(resp['state'], 'Signoff')

        # Check email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('user@test.com', mail.outbox[0].to)
        self.assertIn('admin@test.com', mail.outbox[0].to)
        self.assertEqual(mail.outbox[0].subject, f'[From Test] Spec {spec_ids[0]} "SOP, Spec Creation" needs your review')

        # Sign spec with no credentials
        response = self.post_request(f'/sign/{spec_ids[0]}/A', spec.sign_post_1)
        self.assert_auth_error(response, 'NO_AUTH')

        # Sign spec with no role
        response = self.post_request(f'/sign/{spec_ids[0]}/A', {"signer": os.getenv('USER_USER')}, auth_lvl='USER')
        self.assert_schema_err(response.content, 'role')

        # Sign QUAL sig
        response = self.post_request(f'/sign/{spec_ids[0]}/A', spec.sign_post_1, auth_lvl='USER')
        self.assertEqual(response.status_code, 200)

        # Re-sign QUAL sig
        response = self.post_request(f'/sign/{spec_ids[0]}/A', spec.sign_post_1, auth_lvl='USER')
        self.assertEqual(response.status_code, 200)

        # Re-submit:
        response = self.post_request(f'/submit/{spec_ids[0]}/A', auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('error', resp)
        self.assertEqual(resp['error'], "Spec must be in Draft state to submit for signatures")

        # Empty the test outbox
        mail.outbox = []

        # Reject the spec with no comment
        response = self.post_request(f'/reject/{spec_ids[0]}/A', {}, auth_lvl='USER')
        self.assert_schema_err(response.content, 'comment')

        # Reject the spec
        response = self.post_request(f'/reject/{spec_ids[0]}/A', {'comment': 'test reject'}, auth_lvl='USER')
        self.assertEqual(response.status_code, 200)

        # Verify spec back is in draft state
        response = self.get_request(f'/spec/{spec_ids[0]}/A', auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertIn('state', resp)
        self.assertEqual(resp['state'], 'Draft')

        # Check email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('user@test.com', mail.outbox[0].to)
        self.assertNotIn('admin@test.com', mail.outbox[0].to)
        self.assertEqual(f'[From Test] Spec {spec_ids[0]}/A "SOP, Spec Creation" has been rejected by {os.getenv("USER_USER")}', mail.outbox[0].subject)
        self.assertIn(f'[From Test] Spec {spec_ids[0]}/A "SOP, Spec Creation" has been rejected by {os.getenv("USER_USER")}', mail.outbox[0].body)
        self.assertIn(f'Reason: test reject', mail.outbox[0].body)

        # re-Submit:
        response = self.post_request(f'/submit/{spec_ids[0]}/A', auth_lvl='USER')
        self.assertEqual(response.status_code, 200)

        # Sign dummy sig
        response = self.post_request(f'/sign/{spec_ids[0]}/A', {"role": "dummy", "user": os.getenv('USER_USER')},
                                     auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('error', resp)
        self.assertEqual(resp['error'], "Spec does not have Role dummy / Signer None entry.")

        # Sign QUAL sig
        response = self.post_request(f'/sign/{spec_ids[0]}/A', spec.sign_post_1, auth_lvl='USER')
        self.assertEqual(response.status_code, 200)

        # Sign OP sig as user
        response = self.post_request(f'/sign/{spec_ids[0]}/A', spec.sign_post_2, auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('error', resp)
        self.assertEqual(resp['error'], "Current user SPEC-Test-User is not a delegate for SPEC-Admin-Test-User")

        # List filtered to same spec
        response = self.get_request(f'/spec/?num={spec_ids[0]}&ver=A')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertEqual(1, resp["count"])
        self.assertIsNotNone(resp["results"][0]["first_submit_dt"])
        self.assertIsNotNone(resp["results"][0]["last_submit_dt"])
        self.assertGreater(resp["results"][0]["last_submit_dt"], resp["results"][0]["first_submit_dt"])
        self.assertEqual(1, resp["results"][0]["reject_cnt"])
        self.assertEqual(0, resp["results"][0]["admin_upd_cnt"])
        self.assertEqual(resp["results"][0]["missing_sigs"], f"Op_Line1:{os.getenv('ADMIN_USER')}, Op:{os.getenv('ADMIN_USER')}")

        # Sign OP sig
        response = self.post_request(f'/sign/{spec_ids[0]}/A', spec.sign_post_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        # Add watch, self
        response = self.post_request(f'/user/watch/{os.getenv("USER_USER")}/{spec_ids[0]}', {}, auth_lvl="USER")
        self.assertEqual(response.status_code, 200)

        # Empty the test outbox
        mail.outbox = []

        # Sign op_line1 sig
        response = self.post_request(f'/sign/{spec_ids[0]}/A', spec.sign_post_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        # Verify spec is in active state
        response = self.get_request(f'/spec/{spec_ids[0]}/A', auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertIn('state', resp)
        self.assertEqual(resp['state'], 'Active')

        # Check email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('user@test.com', mail.outbox[0].to)
        self.assertNotIn('admin@test.com', mail.outbox[0].to)
        self.assertEqual(mail.outbox[0].subject, f'[From Test] A new version of Spec {spec_ids[0]} "SOP, Spec Creation" you are watching has been activated.')


        # Reject the active spec
        response = self.post_request(f'/reject/{spec_ids[0]}/A', {'comment': 'test reject'}, auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('error', resp)
        self.assertEqual(resp['error'], "Spec must be in Signoff state to reject")

        # Add watch, self
        response = self.post_request(f'/user/watch/{os.getenv("USER_USER")}/{spec_ids[0]}', {}, auth_lvl="USER")
        self.assertEqual(response.status_code, 200)

        # Set email on account, so the email check below will work
        user = User.objects.get(username=os.getenv('USER_USER'))
        user.email = 'test@test.com'
        user.save()

        # Empty the test outbox
        mail.outbox = []

        # Revise spec
        response = self.post_request(f'/spec/{spec_ids[0]}/A', {"reason": "test revision"}, auth_lvl='USER')
        self.assertEqual(response.status_code, 201)

        # Check email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'[From Test] Spec {spec_ids[0]} "SOP, Spec Creation" you are watching is being revised by {os.getenv("USER_USER")}')

        # Add two files to new spec revision
        with open('spec/tests/test_files/Text1.docx', 'rb') as fp:
            response = self.post_binary_request(f'/file/{spec_ids[0]}/B', {'file':(fp, 'Text1.docx')},  auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        with open('spec/tests/test_files/file_one.txt', 'rb') as fp:
            response = self.post_binary_request(f'/file/{spec_ids[0]}/B', {'file':(fp, 'file_one.txt')},  auth_lvl='USER')
        self.assertEqual(response.status_code, 200)

        # Specify spec-user as signer for op_line1
        # Error: not valid for role
        spec_put = copy.deepcopy(spec.spec_put_3)
        spec_put['sigs'][-1]['signer'] = os.getenv('USER_USER')
        response = self.put_request(f'/spec/{spec_ids[0]}/B', spec_put, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('error', resp)
        self.assertEqual(resp['error'], "Signer SPEC-Test-User for Role Op_Line1 needs to be in list: ['SPEC-Admin-Test-User']")

        # Update spec - Add signers. Set file order and incl_pdf
        response = self.put_request(f'/spec/{spec_ids[0]}/B', spec.spec_put_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        # Submit:
        response = self.post_request(f'/submit/{spec_ids[0]}/B', auth_lvl='USER')
        self.assertEqual(response.status_code, 200)

        # Sign qual sig
        response = self.post_request(f'/sign/{spec_ids[0]}/B', spec.sign_post_1, auth_lvl='USER')
        self.assertEqual(response.status_code, 200)

        # Make spec-user a delegate of spec-admin-user
        response = self.put_request(f'/user/{os.getenv("ADMIN_USER")}', {"delegates": os.getenv('USER_USER')}, auth_lvl="ADMIN")
        self.assertEqual(response.status_code, 200)

        # Sign op_line1 sig
        response = self.post_request(f'/sign/{spec_ids[0]}/B', spec.sign_post_3, auth_lvl='USER')
        self.assertEqual(response.status_code, 200)

        # Verify spec is in active state
        response = self.get_request(f'/spec/{spec_ids[0]}/B', auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertIn('state', resp)
        self.assertEqual(resp['state'], 'Active')

        # Verify old spec is obsolete state
        response = self.get_request(f'/spec/{spec_ids[0]}/A', auth_lvl='USER')
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        self.assertIn('state', resp)
        self.assertEqual(resp['state'], 'Obsolete')

    def test_signCheck(self):
        # Load needed roles
        response = self.post_request('/role/', conf.role_post_1a, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        # Load needed Departments
        response = self.post_request('/dept/', conf.dept_post_1a, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        # Load needed Doc Types
        response = self.post_request('/doctype/', conf.doctype_post_2, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)
        # Load needed Approval Matricies
        response = self.post_request('/approvalmatrix/', conf.approvalmatrix_post_1a, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        # Import new spec
        response = self.post_request('/importSpec/', spec.spec_import_post_3, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 201)

        # Add file to spec
        with open('spec/tests/test_files/Text1.docx', 'rb') as fp:
            response = self.post_binary_request(f'/file/{spec.spec_import_post_3["num"]}/{spec.spec_import_post_3["ver"]}', {'file': (fp, 'Text1.docx')}, auth_lvl='USER')
        self.assertEqual(response.status_code, 200)

        # Update spec - Add signers.
        response = self.put_request(f'/spec/{spec.spec_import_post_3["num"]}/{spec.spec_import_post_3["ver"]}', spec.spec_put_5, auth_lvl='ADMIN')
        self.assertEqual(response.status_code, 200)

        # Submit:
        response = self.post_request(f'/submit/{spec.spec_import_post_3["num"]}/{spec.spec_import_post_3["ver"]}', auth_lvl='USER')
        self.assertEqual(response.status_code, 200)

        # Sign QUAL sig in draft state
        response = self.post_request(f'/sign/{spec.spec_import_post_3["num"]}/{spec.spec_import_post_3["ver"]}', spec.sign_post_4, auth_lvl='USER')
        self.assertEqual(response.status_code, 400)
        resp = json.loads(response.content)
        self.assertIn('error', resp)
        self.assertEqual(resp['error'], f"Current user {os.getenv('USER_USER')} is not valid for role. Options are: ['{os.getenv('ADMIN_USER')}']")
