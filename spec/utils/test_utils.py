from django.conf import settings
from django.contrib.auth.models import User
from django.test import TransactionTestCase
import json
import os

AUTH_ERRS = {
                'NO_AUTH': {
                                'msg': 'Authentication credentials were not provided.',
                                'status': 401
                            },
                'BAD_AUTH': {
                                'msg': 'Invalid username/password.',
                                'status': 403
                            },
                'BAD_TOK': {
                                'msg': 'Invalid Token',
                                'status': 401
                            },
                'EXP_TOK': {
                                'msg': 'The Token is expired',
                                'status': 401
                            },
                'PERM_DENIED': {
                                'msg': 'You do not have permission to perform this action.',
                                'status': 403
                            }
             }


class SpecTestCase(TransactionTestCase):

    def setUp(self):
        self.level_tokens = self.get_all_tokens()

    def get_auth_str(self, auth_lvl):
        if auth_lvl:
            return f'token {self.level_tokens[auth_lvl]}'
        return ''

    def post_binary_request(self, url, body=None, auth_lvl=''):
        return self.client.post(url, body,HTTP_AUTHORIZATION=self.get_auth_str(auth_lvl))

    def post_request(self, url, body=None, auth_lvl=''):
        return self.client.post(url, body, 'application/json', HTTP_AUTHORIZATION=self.get_auth_str(auth_lvl))

    def put_request(self, url, body, auth_lvl='ADMIN'):
        return self.client.put(url, body, 'application/json', HTTP_AUTHORIZATION=self.get_auth_str(auth_lvl))

    def get_request(self, url, auth_lvl=''):
        return self.client.get(url, HTTP_AUTHORIZATION=self.get_auth_str(auth_lvl))

    def delete_request(self, url, body=None, auth_lvl=''):
        return self.client.delete(url, body, content_type='application/json',
                                  HTTP_AUTHORIZATION=self.get_auth_str(auth_lvl))

    def delete_list_attribs(self, item_list, attrib_list):
        for i, item in enumerate(item_list):
            item_list[i] = self.delete_attribs(item, attrib_list)
        return item_list

    def delete_attribs(self, item, attrib_list):
        if item:
            for attrib in attrib_list:
                if attrib in item.keys():
                    item.pop(attrib)
        return item

    def data_to_list(self, data, id_col='lot_id', add_row_num=False): #pragma nocover
        doc_type = data['doc_type']

        ret_list = []
        for d in data['data']:
            ret_list.append({'doc_type': doc_type, '_id': d[id_col], 'data': d})
        if add_row_num:
            ret_list = self.add_row_num(ret_list)
        return ret_list

    def assert_schema_err(self, response, err_field):
        resp = json.loads(response)
        self.assertIn("schemaErrors", resp)
        self.assertIn(err_field, resp['schemaErrors'])
        self.assertGreaterEqual(len(resp['schemaErrors'][err_field]), 1)

    def add_row_num(self, data): #pragma nocover
        for idx, d in enumerate(data):
            d['row_num'] = idx + 2
        return data

    def load_page(self, data): #pragma nocover
        data = json.loads(data)
        return data['results']

    def get_all_tokens(self):
        # get csrf token
        resp = self.client.get('/accounts/login/')
        tok = resp.cookies['csrftoken'].value

        settings.AUTH_LDAP_SERVER_URI = None # Turn off LDAP
        settings.AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend",]
        my_admin = User.objects.create_superuser(username=os.getenv('ADMIN_USER'), password=os.getenv('ADMIN_PASSWD'))
        my_admin.first_name = 'SPEC-Admin'
        my_admin.last_name = 'Test User'
        my_admin.save()
        my_opr = User.objects.create_user(username=os.getenv('USER_USER'))
        my_opr.first_name = 'SPEC-User'
        my_opr.last_name = 'Test'
        my_opr.save()

        # Login via csrf token + djagno LDAP
        auth_body = {'username': os.getenv('ADMIN_USER'), 'password': os.getenv('ADMIN_PASSWD')}
        response = self.client.post('/accounts/login/', auth_body)
        self.assertEqual(response.status_code, 302)

        # Set token
        headers = {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': tok,
                }

        response = self.client.post(f'/auth/token/{os.getenv(f"ADMIN_USER")}', **headers)
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        admin_tok = resp['Authorization']

        response = self.client.post(f'/auth/token/{os.getenv(f"USER_USER")}', **headers)
        self.assertEqual(response.status_code, 200)
        resp = json.loads(response.content)
        user_tok = resp['Authorization']

        response = self.client.post('/accounts/logout/', auth_body)
        self.assertEqual(response.status_code, 200)

        return {'USER': user_tok, 'ADMIN': admin_tok}

    def assert_auth_error(self, response, err_type):
        exp_response = AUTH_ERRS[err_type]
        self.assertEqual(response.status_code, exp_response['status'])
        resp = json.loads(response.content)
        self.assertEqual(resp['detail'], exp_response['msg'])

    def paginate_results(self, res_list):
        page = {}
        page['count'] = len(res_list)
        page['results'] = res_list
        page['next'] = None
        page['previous'] = None
        return page

    def add_list_attribs(self, item_list, attribs): #pragma nocover
        for i, item in enumerate(item_list):
            item.update(attribs)
        return item_list

    def diff_keys(self, d1, d2): #pragma nocover
        comm_keys = list(set(d1.keys() & set(d2.keys())))
        only_d1 = list(set(comm_keys) ^ set(d1.keys()))
        only_d2 = list(set(comm_keys) ^ set(d2.keys()))
        return sorted(only_d1), sorted(only_d2)

    def diff_dicts(self, d1, d2): #pragma nocover
        only_d1, only_d2 = self.diff_keys(d1, d2)
        if len(only_d1) > 0:
            print('only in d1: ' + str(only_d1))
        if len(only_d2) > 0:
            print('only in d2: ' + str(only_d2))
        comm_keys = list(set(d1.keys() & set(d2.keys())))
        for key in comm_keys:
            if d1[key] != d2[key]:
                print('Different value for ' + key + ":")
                print("d1 value: " + str(d1[key]))
                print("d2 value: " + str(d2[key]))

    def dictfetchall(self, cursor): #pragma nocover
        "Return all rows from a cursor as a dict"
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]