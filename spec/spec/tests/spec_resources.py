import os
from . import conf_resources as conf

spec_post_1 = {
    "title": "SOP, Spec Creation",
    "keywords": "keyword one",
    "doc_type": "SOP",
    "department": "Ops:Line1",
    "sigs": [],
    "files": [],
    "refs": [],
    "state":"Draft"
}

spec_get_1 = {
    "title": "SOP, Spec Creation",
    "keywords": "keyword one",
    "doc_type": "SOP",
    "department": "Ops:Line1",
    'sigs': [
        {'role': 'Op_Line1', 'signed_dt': None, 'from_am': True, 'spec_one': True, 'signer': None, 'delegate': None},
        {'role': 'Qual', 'signed_dt': None, 'from_am': True, 'spec_one': False, 'signer': None, 'delegate': None}],
    "files": [],
    "refs": [],
    "state":"Draft",
    "ver": "A",
    'reason': 'Initial Version',
    'approved_dt': None,
    'sunset_extended_dt':None
}

spec_post_2 = {
    "title": "WI, Route Spec",
    "keywords": "keyword two",
    "doc_type": "WI",
    "department": "Ops",
    "sigs": [],
    "files": [],
    "refs": [],
    "state":"Draft"
}

spec_revise_post_1 = {
    "reason": "Creating Rev B"
}

spec_put_1 = {
    "title": "SOP, Spec Creation",
    "keywords": "keyword one",
    "doc_type": "SOP",
    "department": "Ops:Line1",
    "sigs": [],
    "files": [{"filename":"torch.jpg", "incl_pdf":False}, {"filename":"Text1.docx", "incl_pdf":True}],
    "refs": [],
    "state":"Active",
    "comment": "Change state for testing"
}

spec_put_2 = {
    "title": "SOP, Spec Creation",
    "keywords": "keyword one",
    "doc_type": "SOP",
    "department": "Ops:Line1",
    "jira": "TEST-1",
    "sigs": [{'role':conf.role_post_1['role'],'signer':os.getenv("USER_USER"), 'from_am':True}, 
             {'role':conf.role_post_2['role'],'signer':os.getenv("ADMIN_USER"), 'from_am':False},
             {'role':conf.role_post_3['role'],'signer':None, 'from_am':True}],
    "files": [{"filename":"torch.jpg", "incl_pdf":False}, {"filename":"Text1.docx", "incl_pdf":True}],
    "refs": [],
    "state":"Draft",
    "comment": "Change state back to Draft for testing"
}

spec_put_3 = {
    "title": "SOP, Spec Creation",
    "keywords": "keyword one",
    "doc_type": "SOP",
    "department": "Ops:Line1",
    "jira": "TEST-1",
    "sigs": [{'role':conf.role_post_1['role'],'signer':os.getenv("USER_USER"), 'from_am':True},
             {'role':conf.role_post_3['role'],'signer':os.getenv("ADMIN_USER"), 'from_am':True}],
    "files": [{"filename":"torch.jpg", "incl_pdf":False}, {"filename":"Text1.docx", "incl_pdf":True}],
    "refs": [],
    "state":"Draft",
    "comment": "Change state back to Draft for testing"
}

spec_put_4 = {
    "title": "SOP, Spec Creation",
    "keywords": "keyword one",
    "doc_type": "SOP",
    "department": "Ops:Line1",
    "sigs": [],
    "files": [{"filename":"Text1.docx", "incl_pdf":True}],
    "refs": [],
    "state":"Active",
    'sunset_extended_dt': "5 00:00:00",
    "comment": "Change state for testing"
}

spec_put_err_1 = {
    "title": {},
    "keywords": "SPEC",
    "doc_type": "WI",
    "department": "Quality",
    "sigs": [],
    "files": [],
    "refs": []
}

spec_put_err_2 = {
    "title": "SOP, Spec Creation",
    "keywords": "keyword one",
    "doc_type": "SOP",
    "department": "Ops:Line1",
    "sigs": [],
    "files": [],
    "refs": [],
    "state":"Active"
}

spec_import_post_1 = {
    "num": 400000,
    "ver": 'B',
    "title": "SOP, Spec Import",
    "keywords": "keyword one import",
    "doc_type": "SOP",
    "reason": "import for test",
    "department": "Ops:Line1",
    'create_dt': '2022-08-28T00:00:00Z',
    'approved_dt': '2022-08-29T00:00:00Z',
    'mod_ts': '2022-08-29T00:00:00Z',
    "state":"Draft"
}

spec_import_post_2 = {
    "title": "WI, Route Spec Import",
    "ver": 'A',
    "keywords": "keyword two",
    "doc_type": "WI",
    "department": "Ops",
    'create_dt': '2022-08-28T00:00:00Z',
    'approved_dt': '2022-08-29T00:00:00Z',
    'mod_ts': '2022-08-29T00:00:00Z',
    "state":"Draft",
}


sign_post_1 = {
    "role": "Qual",
    "signer": os.getenv('USER_USER')
}

sign_post_2 = {
    "role": "Op",
    "signer": os.getenv('ADMIN_USER')
}

sign_post_3 = {
    "role": "Op_Line1",
    "signer": os.getenv('ADMIN_USER')
}

user_get_1 = {
                 'username': 'SPEC-Admin-Test-User',
                 'first_name': 'SPEC-Admin',
                 'last_name': 'Test User',
                 'is_superuser': True,
                 'is_staff': True,
                 'is_active': True,
                 'email': '',
                 'delegates': '',
                 'delegates_for': [],
                 'watches': [],
                 'req_sig': [],
                 'req_sig_delegate': [],
                 'req_sig_role': [],
                 'in_process': []
             }

user_get_2 = {
                'username': 'SPEC-Test-User',
                'first_name': 'SPEC-User',
                'last_name': 'Test',
                'is_superuser': False,
                'is_staff': False,
                'is_active': True,
                'email': '',
                'delegates': '',
                'delegates_for': [],
                'watches': [],
                'req_sig': [],
                'req_sig_delegate': [],
                'req_sig_role': [],
                'in_process': []
            }
