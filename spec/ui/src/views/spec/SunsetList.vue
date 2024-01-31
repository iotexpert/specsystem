<template>
  <q-page>
    <div>

      <q-table dense ref="tableRef" :rows="rows" :columns="columns" :rows-per-page-options="[5, 10, 15, 20, 50, 100, 250]"
        v-model:pagination="pagination" :loading="loading" binary-state-sort
        @request="qTableOnRequest">

        <template v-slot:top-right>
          <q-btn dense color="primary" @click=" toCSV() " target="_blank" icon="file_download" data-cy="open-file">
            <q-tooltip>Download to CSV</q-tooltip>
          </q-btn>
        </template>

        <template v-slot:body-cell-num=" props ">
            <router-link
                    :to="'/ui-spec/' + props.row['num'] + '/' + props.row['ver']"
                >
                    {{ props.row["num"] }}/{{ props.row["ver"] }}
                </router-link>
        </template>
      </q-table>
    </div>
  </q-page>
</template>

<script>
import { qtCsvLink, qtOnRequest } from "@/qtable-incl.js"
import { dispDate } from "@/utils.js";

import { ref, onMounted } from "vue";

export default {
  name: "SunsetList",
};
</script>

<script setup>
// Variables required for qtable-incl.js functions and table behavior
const filter = ref({});
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
const url = 'sunset/';

onMounted(() => {
  pagination.value.sortBy = columns[0].field;  // Default sort to first column
  tableRef.value.requestServerInteraction();
});

// Wrappers for qtable-incl functions
async function toCSV() {
  window.open(qtCsvLink(filter, pagination, url), '_blank', 'noreferrer');
}
async function qTableOnRequest(props) {
  qtOnRequest(props, loading, filter, rows, pagination, url, row_key);
}


const columns = [
  {
    name: "sunset_dt",
    align: "left",
    label: "Sunset",
    field: "sunset_dt",
    format: (val) => `${dispDate(val)}`,
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: false,
  },
  {
    name: "num",
    align: "left",
    label: "Spec",
    field: "num",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: false,
  },
  {
    name: "title",
    align: "left",
    label: "Title",
    field: "title",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: false,
  },
  {
    name: "doc_type",
    align: "left",
    label: "Doc Type",
    field: "doc_type",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: false,
  },
  {
    name: "department",
    align: "left",
    label: "Department",
    field: "department",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: false,
  },
  {
    name: "approved_dt",
    align: "left",
    label: "Approved",
    field: "approved_dt",
    format: (val) => `${dispDate(val)}`,
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: false,
  },
  {
    name: "sunset_extended_dt",
    align: "left",
    label: "Extended",
    field: "sunset_extended_dt",
    format: (val) => `${dispDate(val)}`,
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: false,
  },
];
</script>

