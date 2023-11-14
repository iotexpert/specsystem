<template>
  <q-layout view="lHh lpr lff">
    <q-header elevated :class="env_color">
      <q-toolbar>
        <q-btn-dropdown flat round dense icon="menu" class="q-mr-sm">
          <q-list>
            <q-item
              clickable
              @click="router.push('/ui-sunset/')"
              data-cy="app-sunset-btn"
            >
              Sunset List
            </q-item>
            <q-item clickable @click="router.push('/ui-doctype/')" data-cy="app-doctype-btn">
              Document Types
            </q-item>
            <q-item clickable @click="router.push('/ui-role/')" data-cy="app-role-btn">
              Roles
            </q-item>
            <q-item clickable @click="router.push('/ui-dept/')" data-cy="app-dept-btn">
              Departments
            </q-item>
            <q-item clickable @click="router.push('/ui-loc/')" data-cy="app-loc-btn">
              Locations
            </q-item>
            <q-item clickable @click="router.push('/ui-apvl-mt/')" data-cy="app-apvl-mt-btn" >
              Approval Matrix
            </q-item>
            <q-item clickable v-show="isAdmin" @click="router.push('/ui-token/')" data-cy="app-token-btn" >
              API Tokens
            </q-item>
          </q-list>
        </q-btn-dropdown>
        <q-separator dark vertical inset />
        <q-toolbar-title>
          <q-btn no-caps @click="router.push('/')">
            <header class="page-header" data-cy="app-title">
              {{ env_title_prefix }}{{ route.name }}
            </header>
          </q-btn>
        </q-toolbar-title>

        <div>
          <q-btn
            label="Specs"
            @click="router.push('/ui-spec/')"
            flat
            icon="description"
            data-cy="app-spec-btn"
          >
          </q-btn>
        </div>
        <div v-show="username !== null">
          <q-btn
            label="User"
            @click="router.push('/ui-user/' + username)"
            flat
            icon="account_box"
            data-cy="app-user-btn"
          >
          </q-btn>
        </div>
        <div v-show="!authenticated">
          <q-btn
            label="Login"
            @click="login = true"
            flat
            icon="login"
            data-cy="app-login-btn"
          >
          </q-btn>
        </div>
        <div v-show="authenticated">
          <q-btn
            label="Logout"
            @click="logout()"
            flat
            icon="logout"
            data-cy="app-logout-btn"
          >
          </q-btn>
        </div>
        <div>
          <q-btn-dropdown label="Help" flat icon="help_outline" data-cy="app-help-btn">
            <q-list>
              <q-item
                clickable
                :href="apiServerHost + '/help/user'"
                target="_blank"
                data-cy="app-help-user"
              >
                User Guide
              </q-item>
              <q-item
                clickable
                :href="apiServerHost + '/help/admin'"
                target="_blank"
                data-cy="app-help-admin"
              >
                Admin Guide
              </q-item>
              <q-item
                clickable
                :href="apiServerHost + '/help/design'"
                target="_blank"
                data-cy="app-help-design"
              >
                High Level Design
              </q-item>
            </q-list>
          </q-btn-dropdown>
        </div>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view :key="route.fullPath"> </router-view>

      <q-dialog v-model="login">
        <login-popup-page @close="login = false" />
      </q-dialog>
    </q-page-container>
  </q-layout>
</template>

<script>
import LoginPopupPage from "@/components/LoginPopup.vue";
import { apiServerHost, retrieveData } from "./utils";
import { ref, onMounted, watch, computed } from "vue";
import { useStore } from "vuex";
import { useRouter, useRoute } from "vue-router";

export default {
  name: "LayoutDefault",
  components: {
    LoginPopupPage,
  },
};
</script>

<script setup>
const router = useRouter();
const route = useRoute();

const store = useStore();

const login = ref(false);

const data_page = ref();

const env_color = ref();
const env_title_prefix = ref("");

const authenticated = ref(computed(() => store.getters.authenticated));
const isAdmin = ref(computed(() => store.getters.isAdmin));
const username = ref(computed(() => store.getters.username));

if (!env_color.value) {
  set_app_color();
}

onMounted(() => {
  if (authenticated.value) {
    store.dispatch("getPermission");
  }
  if (route.params.doc_type) {
    data_page.value = route.params.doc_type;
  }
});

watch(
  () => route.path,
  (new_param, old_param) => {
    data_page.value = null;
  }
);

watch(authenticated, (newVal, oldVal) => {
  if (newVal) {
    store.dispatch("getPermission");
  }
});

async function set_app_color() {
  let resp = await retrieveData("env/");
  env_color.value = resp === "Testx" ? "glossy bg-purple" : "glossy bg-primary";
  env_title_prefix.value = resp === "Testx" ? "Test Environment: " : "";
}

async function logout() {
  logout.value = false;
  store.dispatch("logout");
  router.push("/ui-spec/");
}
</script>

<style lang="scss">
.page-select {
  padding: 5px 10px;
  background-color: "white";
}

.page-header {
  font-size: 2vw;
  padding: 0.5em;
}

.select-text {
  font-size: 20px;
}

.tool-btn {
  font-size: 2vw;
  padding: 1em;
}

.inline {
  display: inline;
}
</style>
