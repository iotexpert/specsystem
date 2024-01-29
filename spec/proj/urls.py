"""tests URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from spec.views.approvalMatrixViews import ApprovalMatrixDetail, ApprovalMatrixList
from spec.views.docTypeViews import DocTypeDetail, DocTypeList
from spec.views.departmentViews import DepartmentDetail, DepartmentList
from spec.views.locationViews import LocationDetail, LocationList
from spec.views.roleViews import RoleDetail, RoleList
from spec.views.specViews import HelpFile, ImportSpec, SpecDetail, SpecExtend, SpecFileDetail, SpecList, SpecReject, SpecSign, SpecSubmit, SunsetList
from spec.views.userViews import UserDetail, UserList, UserWatchView
from user.views import GetUser, AdminToken, UserToken
from . import views
from django.views.generic.base import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('approvalmatrix/', ApprovalMatrixList.as_view()),
    path('approvalmatrix/<id>', ApprovalMatrixDetail.as_view()),
    path('dept/', DepartmentList.as_view()),
    path('dept/<dept>', DepartmentDetail.as_view()),
    path('doctype/', DocTypeList.as_view()),
    path('doctype/<doctype>', DocTypeDetail.as_view()),
    path('extend/<num>/<ver>', SpecExtend.as_view()),
    path('file/<num>', SpecFileDetail.as_view()),
    path('file/<num>/<ver>', SpecFileDetail.as_view()),
    path('file/<num>/<ver>/<fileName>', SpecFileDetail.as_view()),
    path('help/<doc>', HelpFile.as_view()),
    path('importSpec/', ImportSpec.as_view()),
    path('loc/', LocationList.as_view()),
    path('loc/<loc>', LocationDetail.as_view()),
    path('reject/<num>/<ver>', SpecReject.as_view()),
    path('role/', RoleList.as_view()),
    path('role/<role>', RoleDetail.as_view()),
    path('sign/<num>/<ver>', SpecSign.as_view()),
    path('spec/', SpecList.as_view()),
    path('spec/<num>', SpecList.as_view()),
    path('spec/<num>/<ver>', SpecDetail.as_view()),
    path('submit/<num>/<ver>', SpecSubmit.as_view()),
    path('sunset/', SunsetList.as_view()),

    path('db/qa/delete/', views.QaDbReset.as_view()),
    path('auth/info', GetUser.as_view()),
    path('auth/token/<username>', AdminToken.as_view()),
    path('auth/token', UserToken.as_view()),
    path('env/', views.Env.as_view()),
    path('user/', UserList.as_view()),
    path('user/<username>', UserDetail.as_view()),
    path('user/watch/<username>/<spec_num>', UserWatchView.as_view()),
    path('accounts/', include('django.contrib.auth.urls')),
    re_path(r'^.*$', TemplateView.as_view(template_name="index.html"), name='home'),
]
