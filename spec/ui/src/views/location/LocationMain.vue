<template>
  <q-page>
    <div class="q-pa-md row">
      <q-table
        title="Locations"
        :rows="rows"
        :columns="columns"
        separator="cell"
        row-key="location"
        :rows-per-page-options="[0]"
        data-cy="location-table"
      >
        <template v-slot:top-left>
          <div class="row">
            <q-card-actions>
              <q-input
                v-model="filter_val"
                @keydown.enter.prevent="applyFilter(`&search=${filter_val}`)"
                label="filter value"
                data-cy="data-filter-input"
              />
            </q-card-actions>
            <q-card-actions>
              <q-btn
                round
                color="primary"
                @click="clearFilters()"
                icon="clear"
                size="sm"
                data-cy="data-clear-filter-btn"
              >
              </q-btn>
            </q-card-actions>
          </div>
        </template>
        <template v-slot:top-right>
          <q-btn
            color="primary"
            v-show="isAdmin && isAuthenticated"
            @click="add_location = true"
            label="Add Location"
            icon-right="add"
            no-caps
            data-cy="data-row-btn"
          >
          </q-btn>
        </template>
        <template v-slot:header="props">
          <q-th v-show="isAdmin && isAuthenticated" style="width: 15em"> </q-th>
          <q-th v-for="col in columns" :key="col.name" :props="props">
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
            <q-td v-show="isAdmin && isAuthenticated">
              <q-btn
                round
                color="negative"
                @click="deleteSelected(props.row['name'])"
                icon="delete"
                size="xs"
                data-cy="data-delete-btn"
              >
              </q-btn>
            </q-td>
            <q-td
              v-for="col in props.cols"
              :key="col.name"
              :props="props"
              class="text-center"
            >
              {{ props.row[col.name] }}
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
          <q-space />
          <q-btn
            color="primary"
            :href="apiServerHost + '/loc/?output_csv=true' + filter_slug"
            target="_blank"
            icon="file_download"
            data-cy="open-file"
          />
        </template>
      </q-table>
      <q-dialog v-model="add_location">
        <create-location-dialog
          :locationRow="{}"
          :createMode="true"
          @updateTable="getTableData(page_num)"
        />
      </q-dialog>
      <q-dialog v-model="upd_location">
        <create-location-dialog
          :locationRow="locationRow"
          :createMode="false"
          @updateTable="getTableData(page_num)"
        />
      </q-dialog>
    </div>
  </q-page>
</template>

<script>
import { apiServerHost, deleteData, retrieveData } from "@/utils.js";

import { ref, onMounted, computed, defineProps, watch } from "vue";
import { useStore } from "vuex";
import CreateLocationDialog from "@/views/location/CreateLocation.vue";

export default {
  name: "LocationPage",
  components: {
    CreateLocationDialog,
  },
};
</script>

<script setup>
const rows_per_page = 20;

const store = useStore();

const rows = ref([]);
const selected = ref([]);

const add_location = ref(false);
const filter_select = ref();
const filter_val = ref();
const filtered = ref(false);
const filter_slug = ref("");
const locationRow = ref();
const sort_slug = ref("");
const upd_location = ref(false);

const page_num = ref(1);
const num_pages = ref();

const isAuthenticated = ref(computed(() => store.getters.authenticated));
const isAdmin = ref(computed(() => store.getters.isAdmin));

const props = defineProps({
  rerender: Boolean,
});

onMounted(() => {
  getTableData(1);
});

watch(
  () => props.rerender,
  (newVal, oldVal) => {
    if (newVal === false) {
      getTableData(page_num.value);
    }
  }
);

async function getTableData(page_number) {
  add_location.value = false; // Close Add Location popup, if open
  upd_location.value = false; // Close Update Location popup, if open
  let data_url = `loc/?_=_${pagination_slug(page_number)}`;
  if (filter_slug.value) {
    data_url = data_url + `${filter_slug.value}`;
  }
  if (sort_slug.value) {
    data_url = data_url + `${sort_slug.value}`;
  }
  let data_rows = await retrieveData(data_url);
  rows.value = formatRows(data_rows["results"]);

  set_pagination_params(page_number, data_rows.count);
  setSelected();
}

async function deleteSelected(location) {
  if (!window.confirm(`Delete location: ${location}?`)) {
    return;
  }

  let res = await deleteData(
    `loc/${encodeURIComponent(location)}`,
    "{}",
    `Deleted location: ${location} successfully.`
  );
  if (res.__resp_status < 300) {
    clearSelected();
    getTableData(1);
  }
}

async function clearSelected() {
  selected.value = [];
}

function pagination_slug(page_number) {
  return `&limit=${rows_per_page}&offset=${(page_number - 1) * rows_per_page}`;
}

function set_pagination_params(page_number, num_rows) {
  if (num_pages.value) {
    if (page_number > num_pages.value) {
      page_number = num_pages.value;
    }
  }
  num_pages.value = Math.ceil(num_rows / rows_per_page);
  page_num.value = page_number;
}

function formatRows(rows) {
  return rows;
}

function getRowIdx(row_num, creation_tm) {
  for (let i = 0; i < rows.value.length; i++) {
    let row = rows.value[i];
    if (row.row_num === row_num && row.creation_tm === creation_tm) {
      return i;
    }
  }
  return null;
}

// Data in selected rows is be overwritten when table is rerendered when data is modified
// So when table is rerendered, the selected row data must be set in the table
function setSelected() {
  for (const row of selected.value) {
    let row_idx = getRowIdx(row.row_num, row.creation_tm);
    if (row_idx != null) {
      rows.value[row_idx] = row;
    }
  }
}

// Delete input box filter on advanced filter
// Add documentation about basic vs. advanced filter
async function applyFilter(filter_str) {
  if (!filter_str) {
    filtered.value = false;
    filter_slug.value = "";
    getTableData(1);
    return;
  }
  filter_slug.value = filter_str;
  getTableData(1);
  filtered.value = true;
}

async function clearFilter() {
  filter_select.value = null;
  filter_val.value = null;
  filter_slug.value = null;
  getTableData(1);
}

async function clearFilters() {
  filtered.value = false;
  clearFilter();
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
];
</script>

<style scoped>
.doc-btn {
  height: 4em;
  margin: 2vw;
}

.page-input {
  width: 4em;
  margin-left: 2vw;
  text-align: right;
}

.num-selected {
  margin-left: 1vw;
  font-size: 1.2em;
  margin-top: 0.7em;
  font-weight: bold;
}

.tool-row {
  margin-bottom: 2vh;
  margin-top: 1vh;
}

.col-row-width {
  min-width: 100%;
}

.num-pages {
  margin-right: 1vw;
  font-size: 1.15em;
}

.page-title {
  font-size: 2em;
}
</style>
