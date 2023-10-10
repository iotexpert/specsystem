<template>
  <q-card class="dialog-window">
    <q-card-section class="bg-primary text-white row">
      <div class="text-h5">{{ props.username }}</div>
    </q-card-section>

    <q-card-section class="q-pt-none row">
      <q-table
        :rows="req_sig"
        :columns="spec_columns"
        :hide-bottom="true"
        :rows-per-page-options="[0]"
        dense
        data-cy="spec-table"
      >
        <template v-slot:top> Assigned Pending Signatures </template>
        <template v-slot:header="props">
          <q-th v-for="col in props.cols" :key="col.name" :props="props">
            {{ col.label }}
          </q-th>
        </template>
        <template v-slot:body="props">
          <q-tr
            :props="props"
            @click="
              props.row._new_row && !props.selected
                ? (props.selected = true)
                : false
            "
          >
            <q-td
              v-for="col in props.cols"
              :key="col.name"
              :props="props"
              class="text-center"
            >
              <span v-if="col.name === 'num'">
                <router-link
                  :to="'/ui-spec/' + props.row['num'] + '/' + props.row['ver']"
                >
                  {{ props.row["num"] }}/{{ props.row["ver"] }}
                </router-link>
              </span>
              <span v-else-if="col.name === 'mod_ts'">{{
                dispDate(props.row[col.name])
              }}</span>
              <span v-else>{{ props.row[col.name] }}</span>
            </q-td>
          </q-tr>
        </template>
      </q-table>
    </q-card-section>

    <q-card-section class="q-pt-none row">
      <q-table
        :rows="req_sig_delegate"
        :columns="spec_columns"
        :hide-bottom="true"
        :rows-per-page-options="[0]"
        dense
        data-cy="spec-table"
      >
        <template v-slot:top> Delegated Pending Signatures </template>
        <template v-slot:header="props">
          <q-th v-for="col in props.cols" :key="col.name" :props="props">
            {{ col.label }}
          </q-th>
        </template>
        <template v-slot:body="props">
          <q-tr
            :props="props"
            @click="
              props.row._new_row && !props.selected
                ? (props.selected = true)
                : false
            "
          >
            <q-td
              v-for="col in props.cols"
              :key="col.name"
              :props="props"
              class="text-center"
            >
              <span v-if="col.name === 'num'">
                <router-link
                  :to="'/ui-spec/' + props.row['num'] + '/' + props.row['ver']"
                >
                  {{ props.row["num"] }}/{{ props.row["ver"] }}
                </router-link>
              </span>
              <span v-else-if="col.name === 'mod_ts'">{{
                dispDate(props.row[col.name])
              }}</span>
              <span v-else>{{ props.row[col.name] }}</span>
            </q-td>
          </q-tr>
        </template>
      </q-table>
    </q-card-section>

    <q-card-section class="q-pt-none row">
      <q-table
        :rows="req_sig_role"
        :columns="spec_columns"
        :hide-bottom="true"
        :rows-per-page-options="[0]"
        dense
        data-cy="spec-table"
      >
        <template v-slot:top> Role Assigned Pending Signatures </template>
        <template v-slot:header="props">
          <q-th v-for="col in props.cols" :key="col.name" :props="props">
            {{ col.label }}
          </q-th>
        </template>
        <template v-slot:body="props">
          <q-tr
            :props="props"
            @click="
              props.row._new_row && !props.selected
                ? (props.selected = true)
                : false
            "
          >
            <q-td
              v-for="col in props.cols"
              :key="col.name"
              :props="props"
              class="text-center"
            >
              <span v-if="col.name === 'num'">
                <router-link
                  :to="'/ui-spec/' + props.row['num'] + '/' + props.row['ver']"
                >
                  {{ props.row["num"] }}/{{ props.row["ver"] }}
                </router-link>
              </span>
              <span v-else-if="col.name === 'mod_ts'">{{
                dispDate(props.row[col.name])
              }}</span>
              <span v-else>{{ props.row[col.name] }}</span>
            </q-td>
          </q-tr>
        </template>
      </q-table>
    </q-card-section>

    <q-card-section class="q-pt-none row">
      <q-table
        :rows="in_process"
        :columns="spec_columns"
        :hide-bottom="true"
        :rows-per-page-options="[0]"
        dense
        data-cy="spec-table"
      >
        <template v-slot:top> User Created Specs Still In-Process </template>
        <template v-slot:header="props">
          <q-th v-for="col in props.cols" :key="col.name" :props="props">
            {{ col.label }}
          </q-th>
        </template>
        <template v-slot:body="props">
          <q-tr
            :props="props"
            @click="
              props.row._new_row && !props.selected
                ? (props.selected = true)
                : false
            "
          >
            <q-td
              v-for="col in props.cols"
              :key="col.name"
              :props="props"
              class="text-center"
            >
              <span v-if="col.name === 'num'">
                <router-link
                  :to="'/ui-spec/' + props.row['num'] + '/' + props.row['ver']"
                >
                  {{ props.row["num"] }}/{{ props.row["ver"] }}
                </router-link>
              </span>
              <span v-else-if="col.name === 'mod_ts'">{{
                dispDate(props.row[col.name])
              }}</span>
              <span v-else>{{ props.row[col.name] }}</span>
            </q-td>
          </q-tr>
        </template>
      </q-table>
    </q-card-section>

    <q-card-section class="q-pt-none row">
      <q-btn
        v-show="isAdmin || props.username === user_name"
        icon="save"
        color="primary"
        @click="saveUser()"
        data-cy="user-detail-delegate-update"
      />
      &nbsp;
      <q-input
        label="Delegates"
        v-model.trim="delegates"
        data-cy="user-detail-delegates"
        dense
      />
    </q-card-section>

    <q-card-section class="q-pt-none row">
      <q-table
        :rows="watches"
        :hide-bottom="true"
        :rows-per-page-options="[0]"
        dense
        data-cy="spec-table"
      >
        <template v-slot:header>
          <q-th style="text-align: left"> Specs Watched </q-th>
        </template>
        <template v-slot:body="props">
          <q-tr :props="props">
            <q-td
              v-for="col in props.cols"
              :key="col.name"
              :props="props"
              style="text-align: left"
            >
              <span v-if="col.name === 'num'">
                <router-link :to="'/ui-spec/' + props.row['num'] + '/*'">
                  {{ props.row["num"] }}
                </router-link>
                &nbsp;
                <q-btn
                  round
                  color="primary"
                  @click="clearWatch(props.row['num'].toString())"
                  icon="visibility"
                  size="xs"
                  data-cy="clear-watch"
                >
                </q-btn>
              </span>
              <span v-else>{{ props.row[col.name] }}</span>
            </q-td>
          </q-tr>
        </template>
        <template v-slot:bottom>
          <q-btn
            @click="getTableData(page_num - 1)"
            :disable="page_num == 1"
            data-cy="data-prev-btn"
          >
            {{ "&lt;" }}
          </q-btn>
          <q-input
            input-class="text-right"
            v-model="page_num"
            class="page-input"
            @keydown.enter.prevent="getTableData(page_num)"
            data-cy="data-page-input"
          />
          <div class="num-pages" data-cy="data-num-pages">
            &nbsp;/ {{ num_pages }}
          </div>
          <q-btn
            @click="getTableData(page_num + 1)"
            :disable="page_num == num_pages"
            data-cy="data-next-btn"
          >
            {{ ">" }}
          </q-btn>
        </template>
      </q-table>
      &nbsp;
      <q-table
        :rows="delegates_for"
        :hide-bottom="true"
        :rows-per-page-options="[0]"
        dense
        data-cy="delgate-table"
      >
        <template v-slot:header>
          <q-th style="text-align: left"> Delegates For </q-th>
        </template>
        <template v-slot:body="props">
          <q-tr :props="props">
            <q-td
              v-for="col in props.cols"
              :key="col.name"
              :props="props"
              style="text-align: left"
            >
              <router-link :to="'/ui-user/' + props.row['user']">
                {{ props.row["user"] }}
              </router-link>
            </q-td>
          </q-tr>
        </template>
        <template v-slot:bottom>
          <q-btn
            @click="getTableData(page_num - 1)"
            :disable="page_num == 1"
            data-cy="data-prev-btn"
          >
            {{ "&lt;" }}
          </q-btn>
          <q-input
            input-class="text-right"
            v-model="page_num"
            class="page-input"
            @keydown.enter.prevent="getTableData(page_num)"
            data-cy="data-page-input"
          />
          <div class="num-pages" data-cy="data-num-pages">
            &nbsp;/ {{ num_pages }}
          </div>
          <q-btn
            @click="getTableData(page_num + 1)"
            :disable="page_num == num_pages"
            data-cy="data-next-btn"
          >
            {{ ">" }}
          </q-btn>
        </template>
      </q-table>
    </q-card-section>
  </q-card>
</template>

<script>
import {
  defineProps,
  deleteData,
  dispDate,
  putData,
  retrieveData,
} from "@/utils.js";
import { computed, ref, onMounted } from "vue";
import { useStore } from "vuex";

export default {
  name: "UserDetailPage",
};
</script>

<script setup>
const props = defineProps({
  username: String,
});

const store = useStore();
const isAdmin = ref(computed(() => store.getters.isAdmin));
const user_name = ref(computed(() => store.getters.username));
const delegates = ref("");
const delegates_for = ref([]);
const in_process = ref([]);
const req_sig = ref([]);
const req_sig_delegate = ref([]);
const req_sig_role = ref([]);
const watches = ref([]);

async function saveUser() {
  const body = {
    delegates: delegates.value,
  };

  let res = await putData(
    `user/${props.username}`,
    body,
    "Successfully updated user " + props.username
  );
}

async function loadData() {
  let res = await retrieveData(`user/${props.username}`);
  delegates.value = res["delegates"];
  delegates_for.value = res["delegates_for"].map(function (user) {
    return { user: user };
  });
  watches.value = res["watches"].map(function (num) {
    return { num: num };
  });
  req_sig.value = res["req_sig"];
  req_sig_delegate.value = res["req_sig_delegate"];
  req_sig_role.value = res["req_sig_role"];
  in_process.value = res["in_process"];
}

onMounted(() => {
  loadData();
});

async function clearWatch(num) {
  let res = await deleteData(
    `user/watch/${props.username}/${num}`,
    "{}",
    `Deleted watch on: ${num} successfully.`
  );
  if (res.__resp_status < 300) {
    loadData();
  }
}
const spec_columns = [
  { name: "num", align: "left", label: "Spec", field: "num" },
  { name: "title", align: "left", label: "Title", field: "title" },
  { name: "doc_type", align: "left", label: "Doc Type", field: "doc_type" },
  {
    name: "department",
    align: "left",
    label: "Department",
    field: "department",
  },
  { name: "keywords", align: "left", label: "Keywords", field: "keywords" },
  { name: "state", align: "left", label: "State", field: "state" },
  {
    name: "created_by",
    align: "left",
    label: "Created By",
    field: "created_by",
  },
  { name: "mod_ts", align: "left", label: "Last Modified", field: "mod_ts" },
  {
    name: "anon_access",
    align: "left",
    label: "Anonymous Access",
    field: "anon_access",
  },
];
</script>

<style scoped>
.dialog_window {
  max-width: 50vw;
  width: 50vw;
}
</style>
