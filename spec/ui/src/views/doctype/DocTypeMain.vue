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
            <q-card-section class="q-pt-none">
                <label>Bulk Update / Insert</label><br/>
                <input type="file"  @change="loadTextFromFile" v-show="isAdmin" name="inputFile"  ref="inputFile" accept="file/csv" />
            </q-card-section>
            <q-card-section class="q-pt-none">
                <q-btn dense v-show="isAdmin" color="primary" @click="add_doctype = true" icon="add" data-cy="add-row" label="Add Doctype" no-caps/>
                &nbsp;
                <q-btn dense color="primary" @click=" toCSV() " target="_blank" icon="file_download" data-cy="open-file">
                <q-tooltip>Download to CSV</q-tooltip>
                </q-btn>
            </q-card-section>
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

    <q-dialog v-model=" waiting " no-esc-dismiss no-backdrop-dismiss>
      <q-card>
        <q-card-section>
        <h4>Updating system. Please wait</h4>
        <br />
        <p>Do not refresh the page.</p>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script>
import { deleteData, postData, } from "@/utils.js";
import { qtCsvLink, qtFilterValue, qtOnRequest } from "@/qtable-incl.js"
import { computed, onMounted, ref, watch, } from 'vue'
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
const csvReadFromFile = ref(null)
const csvRows = ref([]);
const doctypeRow = ref();
const inputFile = ref();
const upd_doctype = ref(false);
const waiting = ref(false);

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

async function loadTextFromFile(ev) {
  const file = ev.target.files[0];
  const reader = new FileReader();

  reader.onload = e => csvReadFromFile.value = e.target.result;
  reader.readAsText(file);
}
watch(csvReadFromFile, (newVal, oldVal) => {
  if (newVal) {
    csvRows.value = [];
    const re = /(?:,|\n|^)("(?:(?:"")*[^"]*)*"|[^",\n]*|(?:\n|$))/  // find a cell in the row
    const re2 = /^"(.*)"$/ // Remove wrapping double quotes around a cell
    let offset = 0;
    let row = [];
    let csv_rows = [];
    while (offset < csvReadFromFile.value.length) {
      let r = csvReadFromFile.value.slice(offset).match(re);
      offset += r[0].length;
      if (r[0].startsWith('\n')) { csv_rows.push(row); row = []; }
      let v = r[1].trim()
      v = v.replace(re2, '$1')
      row.push(v.trim())
    }
    if (row.length) { csv_rows.push(row); }
    for (let r of csv_rows.slice(1)) {
      if (!r[0]) {continue}
      let b = {};
      for (let c = 0; c < csv_rows[0].length; c++) {
        b[csv_rows[0][c]] = r[c]?r[c]:null;
      }
      csvRows.value.push(b)
    }
    csvReadFromFile.value = null;
    inputFile.value.value = '';
    save();
  }
});

async function save() {
  try {
    waiting.value = true

    let res = {};
    if (csvRows.value.length) {
      res = await postData('doctype/', csvRows.value, 'Doc Types updated.')
    }
  }
  finally {
    waiting.value = false
  }
  tableRef.value.requestServerInteraction();
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
