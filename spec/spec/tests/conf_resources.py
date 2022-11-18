import os

role_post_1 = {
    'role':'Qual',
    'descr':'Quality',
    'spec_one':False,
    'users':f'{os.getenv("ADMIN_USER")}, {os.getenv("USER_USER")}'
}

role_post_2 = {
    'role':'Op',
    'descr':'Operations',
    'spec_one':True,
    'users':f'{os.getenv("ADMIN_USER")}, {os.getenv("USER_USER")}'
}

role_post_3 = {
    'role':'Op_Line1',
    'descr':'Operations Line 1',
    'spec_one':True,
    'users':f'{os.getenv("ADMIN_USER")}'
}

role_put_1 = {
    'role':'Qual',
    'descr':'Quality - Descr updated',
    'spec_one':True,
    'users':f'{os.getenv("USER_USER")}'
}

role_put_err_1 = {
    'descr':'Quality',
    'spec_one':10,
    'users':f'{os.getenv("USER_USER")}'
}


dept_post_0 = {
    'name':'__Generic__',
    'readRoles':role_post_1['role']
}

dept_post_1 = {
    'name':'Quality',
    'readRoles':role_post_1['role']
}

dept_post_2 = {
    'name':'Ops',
    'readRoles':role_post_2['role']
}

dept_post_3 = {
    'name':'Ops:Line1',
    'readRoles':role_post_3['role']
}

dept_put_1 = {
    'name':'Ops',
    'readRoles':f'{role_post_2["role"]}, {role_post_3["role"]}'
}

dept_put_err_1 = {
    'dept':'Quality',
    'readRoles':{}
}

dept_put_err_2 = {
    'dept':'Quality',
    'readRoles':f'{role_post_1["role"]}, BadRole'
}


doctype_post_1 = {
    'name':'SOP',
    'descr':'Standard Operating Procedure - Op',
    'confidential':False,
    'jira_temp':'',
    'sunset_interval': '1 00:00:00',
    'sunset_warn': '23:50:00'
}

doctype_post_2 = {
    'name':'WI',
    'descr':'Work Instruction - Op',
    'confidential':False,
    'jira_temp':'',
    'sunset_interval': '1 00:00:00',
    'sunset_warn': '23:50:00'
}

doctype_post_3 = {
    'name':'HR-Confidential',
    'descr':'Confidential HR policy',
    'confidential':True,
    'jira_temp':'SPEC-2'
}

doctype_put_1 = {
    'name':'WI',
    'descr':'Work Instruction - Updated',
    'confidential':True,
    'jira_temp':'New Jira Template',
    'sunset_interval': '2 00:00:00',
    'sunset_warn': '20:50:00'
}

doctype_put_2 = {
    'name':'SOP',
    'descr':'Standard Operating Procedure - Op',
    'confidential':False,
    'jira_temp':None,
    'sunset_interval': '2 00:00:00',
    'sunset_warn': '1 23:59:58'
}

doctype_put_err_1 = {
    'name':'WI',
    'descr':'Work Instruction',
    'confidential':10,
    'jira_temp':''
}


approvalmatrix_post_1 = {
    "doc_type": doctype_post_1['name'],
    "department": dept_post_0['name'],
    "signRoles": role_post_1['role']
}

approvalmatrix_post_2 = {
    "doc_type": doctype_post_1['name'],
    "department": dept_post_2['name'],
    "signRoles": role_post_2['role']
}

approvalmatrix_post_3 = {
    "doc_type": doctype_post_1['name'],
    "department": dept_post_3['name'],
    "signRoles": role_post_3['role']
}

approvalmatrix_put_1 = {
    "doc_type": doctype_post_1['name'],
    "department": dept_post_0['name'],
    "signRoles": f'{role_post_2["role"]}, {role_post_3["role"]}'
}

approvalmatrix_put_err_1 = {
    "doc_type": doctype_post_1['name'],
    "department": dept_post_0['name'],
    "signRoles": {}
}

approvalmatrix_put_err_2 = {
    "doc_type": "BadDocType",
    "department": dept_post_0['name'],
    "signRoles": f'{role_post_2["role"]}, {role_post_3["role"]}'
}

approvalmatrix_put_err_3 = {
    "doc_type": doctype_post_1['name'],
    "department": "BadDept",
    "signRoles": f'{role_post_2["role"]}, {role_post_3["role"]}'
}

approvalmatrix_put_err_4 = {
    "doc_type": doctype_post_1['name'],
    "department": dept_post_0['name'],
    "signRoles": f'{role_post_2["role"]}, BadRole'
}