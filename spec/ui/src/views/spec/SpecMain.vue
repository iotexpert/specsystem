<template>
  <q-page>
    <div>
      <q-table dense ref="tableRef" :rows="rows" :columns="columns" :rows-per-page-options="[5, 10, 15, 20, 50, 100, 250]"
        selection="single" v-model:pagination="pagination" :loading="loading" :filter="filter" binary-state-sort
        :visible-columns="visibleColumns" @request="qTableOnRequest"  >
        <template v-slot:top-left>
          <div>
            <q-btn dense color="primary" round icon="filter_alt" @click="filterShow = !filterShow">
              <q-tooltip>Toggle Filter Row</q-tooltip>
            </q-btn>
            &nbsp;
            <q-btn dense color="primary" round @click="filter = {}; filter_state=[]" icon="filter_alt_off" data-cy="data-clear-filter-btn">
              <q-tooltip>Clear Filters</q-tooltip>
            </q-btn>
          </div>
        </template>

        <template v-slot:top-right>
          <q-btn dense v-show="isAuthenticated" color="primary" @click="add_spec = true" icon="add" data-cy="add-row" label="Add Spec" no-caps/>
          &nbsp;
          <q-btn dense color="primary" @click=" toCSV() " target="_blank" icon="file_download" data-cy="open-file">
            <q-tooltip>Download to CSV</q-tooltip>
          </q-btn>
        </template>

        <template v-slot:top-row>
          <q-tr v-show=" filterShow ">
            <q-td />
            <q-td dense v-for=" col  in  columns " v-bind:value=" col.name " :key=" col.name ">
                <q-select
                v-if="col.name === 'state'"
                    v-model="filter_state"
                    data-cy="spec-detail-filter-state"
                    :options="[
                    { label: 'Draft', value: 'draft' },
                    { label: 'Signoff', value: 'signoff' },
                    { label: 'Active', value: 'active' },
                    { label: 'Obsolete', value: 'obsolete' },
                    ]"
                    multiple
                    dense
                    @blur="applyFilter()"
                    class="inline-block"
                />
                <q-input v-else-if="!col.skip_filter" dense v-model.trim="filter[col.name]" :label="col.label" debounce="500" data_cy="filter-field"/>
            </q-td>
          </q-tr>
        </template>
        <template v-slot:body-cell-num=" props ">
          <q-td>
            <q-btn v-if="!props.row['watched']" round color="primary" @click="setWatch(props.row['num'].toString())"
                    icon="visibility_off" size="xs" data-cy="set-watch" >
                <q-tooltip>Toggle Watch</q-tooltip>
            </q-btn>
            <q-btn v-if="props.row['watched']" round color="primary" @click="clearWatch(props.row['num'].toString())"
                    icon="visibility" size="xs" data-cy="clear-watch" >
                <q-tooltip>Toggle Watch</q-tooltip>
            </q-btn>
            &nbsp;
            <router-link :to="'/ui-spec/' + props.row['num'] + '/' + props.row['ver']">
                {{ props.row["num"] }}/{{ props.row["ver"] }}
            </router-link>
            &nbsp;
            <q-btn v-if="props.row['state'] === 'Active'" round color="primary"
                :href="apiServerHost + '/file/' + props.row['num'] + '/' + props.row['ver'] + '?state=Active'"
                target="_blank" icon="description" size="xs" data-cy="open-file" >
                <q-tooltip>View first file</q-tooltip>
            </q-btn>
          </q-td>
        </template>

        <template v-slot:body-cell-sunset_dt=" props ">
          <q-td>
            {{ props.row['sunset_dt'] ? props.row['sunset_dt'].substring(0, 10) : "" }}
          </q-td>
        </template>

        <template v-slot:body-cell-state=" props ">
          <q-td>
            <span v-if="props.row['state'] === 'Signoff'">
                {{ props.row['state'] }}
                <br> Submitted: {{ dispDate(props.row['last_submit_dt']) }}
                <br> {{ props.row['missing_sigs'] }}
            </span>
            <span v-else>{{ props.row['state'] }}</span>
          </q-td>
        </template>
      </q-table>

      <q-dialog v-model="add_spec">
        <create-spec-dialog
          :createMode="true"
          @updateTable=" onCloseDialog() "
        />
      </q-dialog>
    </div>
  </q-page>
</template>

<script>
import { qtCsvLink, qtOnRequest } from "@/qtable-incl.js"
import { apiServerHost, deleteData, postData } from "@/utils.js";

import { ref, onMounted, computed, } from "vue";
import { useStore } from "vuex";
import CreateSpecDialog from "@/views/spec/CreateSpec.vue";

export default {
  name: "SpecPage",
  components: {
    CreateSpecDialog,
  },
};
</script>

<script setup>
// Variables required for qtable-incl.js functions and table behavior
const filter = ref({});
const filterShow = ref(true);
const loading = ref(false);
const pagination = ref({
  sortBy: 'null',
  descending: false,
  page: 1,
  rowsPerPage: 10,
  rowsNumber: 0,
});
const rows = ref([]);
const row_key = 'name';
const tableRef = ref();
const url = 'spec/';
const store = useStore();

const add_spec = ref(false);
const filter_state = ref([]);
const upd_spec = ref(false);

const isAuthenticated = ref(computed(() => store.getters.authenticated));
const username = ref(computed(() => store.getters.username));

onMounted(() => {
  pagination.value.sortBy = columns[0].field;  // Default sort to first column
  filter.value = {};
  tableRef.value.requestServerInteraction();
});

function onCloseDialog() {
  add_spec.value = false;
  upd_spec.value = false;
  tableRef.value.requestServerInteraction();
}

async function setWatch(num) {
  let res = await postData(
    `user/watch/${username.value}/${num}`,
    "{}",
    `Set watch on: ${num} successfully.`
  );
  if (res.__resp_status < 300) {
  tableRef.value.requestServerInteraction();
  }
}

async function clearWatch(num) {
  let res = await deleteData(
    `user/watch/${username.value}/${num}`,
    "{}",
    `Deleted watch on: ${num} successfully.`
  );
  if (res.__resp_status < 300) {
  tableRef.value.requestServerInteraction();
  }
}

function applyFilter() {
  delete filter.value.incl_obsolete;
  delete filter.value.state;
  if (filter_state.value.length > 0) {
    filter.value.incl_obsolete="true";
    filter.value.state = filter_state.value.map(function (s) {return s["value"];}).join();
  }
}

// Wrappers for qtable-incl functions
async function toCSV() {
  window.open(qtCsvLink(filter, pagination, url), '_blank', 'noreferrer');
}
async function qTableOnRequest(props) {
  qtOnRequest(props, loading, filter, rows, pagination, url, row_key);
}

// visibleColumns is used to keep incl_obsolete from being displayed
const visibleColumns = [ "num",  "title", "doc_type", "department", "location", "keywords", "created_by", "state", "sunset_dt",  ];

const columns = [
  {
    name: "num",
    align: "left",
    label: "Spec",
    field: "num",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: true,
  },
  {
    name: "title",
    align: "left",
    label: "Title",
    field: "title",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: true,
  },
  {
    name: "doc_type",
    align: "left",
    label: "Doc Type",
    field: "doc_type",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: true,
  },
  {
    name: "department",
    align: "left",
    label: "Department",
    field: "department",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: true,
  },
  {
    name: "location",
    align: "left",
    label: "Location",
    field: "location",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: true,
  },
  {
    name: "keywords",
    align: "left",
    label: "Keywords",
    field: "keywords",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: true,
  },
  {
    name: "created_by",
    align: "left",
    label: "Created By",
    field: "created_by",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: true,
  },
  {
    name: "state",
    align: "left",
    label: "State",
    field: "state",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: true,
  },
  {
    name: "sunset_dt",
    align: "left",
    label: "Sunset Date",
    field: "sunset_dt",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: false,
  },
  {
    // This is required, so it will be used in the GET parameters on the search
    name: "incl_obsolete",
    field: "incl_obsolete",
  },
];</script>