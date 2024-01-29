import { createWebHistory, createRouter } from "vue-router";
import ApprovalMatrixPage from "@/views/approvalMatrix/ApprovalMatrixMain.vue"
import DepartmentPage from "@/views/department/DepartmentMain.vue"
import DocTypePage from "@/views/doctype/DocTypeMain.vue"
import LocationPage from "@/views/location/LocationMain.vue"
import RolePage from "@/views/role/RoleMain.vue"
import SpecDetailPage from "@/views/spec/SpecDetail.vue"
import SpecPage from "@/views/spec/SpecMain.vue"
import SunsetList from "@/views/spec/SunsetList.vue"
import TokenPage from "@/views/token/TokenMain.vue"
import UserDetailPage from "@/views/user/UserDetail.vue"

const routes = [
  {
    path: "/",
    redirect: { name: 'Spec' },
  },
  {
    path: '/ui-apvl-mt',
    name: 'ApprovalMatrix',
    component: ApprovalMatrixPage
  },
  {
    path: '/ui-dept',
    name: 'Department',
    component: DepartmentPage
  },
  {
    path: '/ui-doctype',
    name: 'Document Type',
    component: DocTypePage
  },
  {
    path: '/ui-loc',
    name: 'Location',
    component: LocationPage
  },
  {
    path: '/ui-role',
    name: 'Role',
    component: RolePage
  },
  {
    path: '/ui-spec',
    name: 'Spec',
    component: SpecPage
  },
  {
    path: '/ui-spec/:num/:ver?',
    name: 'Spec Detail',
    component: SpecDetailPage,
    props: true,
  },
  {
    path: '/ui-sunset',
    name: 'Sunset List',
    component: SunsetList,
  },
  {
    path: '/ui-token',
    name: 'Token',
    component: TokenPage
  },
  {
    path: '/ui-user/:username',
    name: 'User Detail',
    component: UserDetailPage,
    props: true,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;