<template>
  <q-page>
    <div class="q-pa-md row">

    <q-table dense ref="tableRef" :rows="rows" :columns="columns" :rows-per-page-options="[5, 10, 15, 20, 50, 100, 250]"
        selection="single" v-model:pagination="pagination" :loading="loading" :filter="filter" binary-state-sort
        @request="qTableOnRequest">
        <template v-slot:top-left>
          <div>
            <q-btn dense icon="filter_alt" color="primary" round @click="filterShow = !filterShow">
              <q-tooltip>Toggle Filter Row</q-tooltip>
            </q-btn>
            &nbsp;
            <q-btn dense color="primary" round @click="filter = {}" icon="filter_alt_off" data-cy="data-clear-filter-btn">
              <q-tooltip>Clear Filters</q-tooltip>
            </q-btn>
            &nbsp;
            <i>{{ filterValue() }}</i>
          </div>
        </template>

        <template v-slot:top-right>
          <q-btn dense v-show="isAdmin" color="primary" @click="add_doctype = true" icon="add" data-cy="add-row" label="Add Doctype" no-caps/>
          &nbsp;
          <q-btn dense color="primary" @click=" toCSV() " target="_blank" icon="file_download" data-cy="open-file">
            <q-tooltip>Download to CSV</q-tooltip>
          </q-btn>
        </template>

        <template v-slot:top-row>
          <q-tr v-show=" filterShow ">
            <q-td />
            <q-td dense v-for=" col  in  columns " v-bind:value=" col.name " :key=" col.name ">
              <q-input v-if="!col.skip_filter" dense v-model.trim="filter[col.name]" :label="col.label" debounce="500" data_cy="filter-field"/>
            </q-td>
          </q-tr>
        </template>
        <template v-slot:body-selection=" props ">
          <q-btn v-if=" isAdmin " @click="deleteSelected(props.row['name'])" color="negative" round size="xs" icon="delete" data-cy="btn-delete_role">
            <q-tooltip>Delete</q-tooltip>
          </q-btn>
          &nbsp;
          <q-btn v-if=" isAdmin " @click="updateSelected(props.row)" color="primary" round size="xs" icon="edit"
            data-cy="btn-open_role_update">
            <q-tooltip>View / Edit</q-tooltip>
          </q-btn>
        </template>
      </q-table>
      <q-dialog v-model="add_doctype">
        <create-doctype-dialog
          :doctypeRow="{}"
          :createMode="true"
          @updateTable=" onCloseDialog() "
        />
      </q-dialog>
      <q-dialog v-model="upd_doctype">
        <create-doctype-dialog
          :doctypeRow="doctypeRow"
          :createMode="false"
          @updateTable=" onCloseDialog() "
        />
      </q-dialog>
    </div>
  </q-page>
</template>

<script>
import { qtCsvLink, qtFilterValue, qtOnRequest } from "@/qtable-incl.js"
import { deleteData } from "@/utils.js";

import { ref, onMounted, computed } from "vue";
import { useStore } from "vuex";
import CreateDoctypeDialog from "@/views/doctype/CreateDoctype.vue";

export default {
  name: "DoctypePage",
  components: {
    CreateDoctypeDialog,
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
const url = 'doctype/';

// Local page variables start here
const store = useStore();

const add_doctype = ref(false);
const doctypeRow = ref();
const upd_doctype = ref(false);

const isAdmin = ref(computed(() => store.getters.isAdmin));

onMounted(() => {
  pagination.value.sortBy = columns[0].field;  // Default sort to first column
  filter.value = {};
  tableRef.value.requestServerInteraction();
});

function onCloseDialog() {
  add_doctype.value = false;
  upd_doctype.value = false;
  tableRef.value.requestServerInteraction();
}

async function deleteSelected(doctype) {
  if (!window.confirm(`Delete doctype: ${doctype}?`)) {
    return;
  }

  let res = await deleteData(
    `doctype/${doctype}`,
    "{}",
    `Deleted doctype: ${doctype} successfully.`
  );
  if (res.__resp_status < 300) {
    tableRef.value.requestServerInteraction();
  }
}

async function updateSelected(row) {
  doctypeRow.value = row;
  upd_doctype.value = true;
}

// Wrappers for qtable-incl functions
function filterValue() {
  return qtFilterValue(filter, columns);
}
async function toCSV() {
  window.open(qtCsvLink(filter, pagination, url), '_blank', 'noreferrer');
}
async function qTableOnRequest(props) {
  qtOnRequest(props, loading, filter, rows, pagination, url, row_key);
}

const columns = [
  {
    name: "name",
    align: "center",
    label: "Name",
    field: "name",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: true,
  },
  {
    name: "descr",
    align: "center",
    label: "Description",
    field: "descr",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: true,
  },
  {
    name: "confidential",
    align: "center",
    label: "Confidential",
    field: "confidential",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: true,
  },
  {
    name: "jira_temp",
    align: "center",
    label: "Jira Template",
    field: "jira_temp",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: true,
  },
  {
    name: "sunset_interval",
    align: "center",
    label: "Sunset Interval",
    field: "sunset_interval",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: false,
    skip_filter: true,
  },
  {
    name: "sunset_warn",
    align: "center",
    label: "Sunset Warning",
    field: "sunset_warn",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: false,
    skip_filter: true,
  },
  {
    name: "active",
    align: "center",
    label: "Active",
    field: "active",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: true,
  },
];
</script>
