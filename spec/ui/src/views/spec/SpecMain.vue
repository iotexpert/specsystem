<template>
  <q-page>
    <div>
      <q-table
        :rows="rows"
        :columns="columns"
        :rows-per-page-options="[0]"
        data-cy="spec-table"
      >
        <template v-slot:top-left>
          <div>
            <q-btn
              round
              color="primary"
              @click="applyFilter()"
              icon="filter_alt"
              data-cy="data-filter-btn"
            />
            &nbsp;
            <q-btn
              round
              color="primary"
              @click="clearFilter()"
              icon="filter_alt_off"
              data-cy="data-clear-filter-btn"
            />
          </div>
        </template>
        <template v-slot:top-right>
          <div>
            <q-btn
              color="primary"
              v-show="isAuthenticated"
              @click="add_spec = true"
              label="Add Spec"
              icon-right="add"
              no-caps
              data-cy="data-row-btn"
            />
          </div>
        </template>
        <template v-slot:header="props">
          <q-th
            v-for="col in columns"
            :key="col.name"
            :props="props"
            style="vertical-align: top"
          >
            {{ col.label }}
            <br />
            <span
              v-show="
                [
                  'num',
                  'title',
                  'doc_type',
                  'department',
                  'location',
                  'keywords',
                  'created_by',
                ].includes(col.name)
              "
            >
              <q-icon name="filter_alt" />
              <q-input
                v-model.trim="filter[col.name]"
                data-cy="spec-detail-ref-num"
                dense
                @keydown.enter="applyFilter()"
                @blur="applyFilter()"
                class="inline-block"
              />
            </span>
            <span v-show="['state'].includes(col.name)" class="row">
              <q-select
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
            </span>
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
                <q-btn
                  v-if="!props.row['watched']"
                  round
                  color="primary"
                  @click="setWatch(props.row['num'].toString())"
                  icon="visibility_off"
                  size="xs"
                  data-cy="set-watch"
                >
                  <q-tooltip>Toggle Watch</q-tooltip>
                </q-btn>
                <q-btn
                  v-if="props.row['watched']"
                  round
                  color="primary"
                  @click="clearWatch(props.row['num'].toString())"
                  icon="visibility"
                  size="xs"
                  data-cy="clear-watch"
                >
                  <q-tooltip>Toggle Watch</q-tooltip>
                </q-btn>
                &nbsp;
                <router-link
                  :to="'/ui-spec/' + props.row['num'] + '/' + props.row['ver']"
                >
                  {{ props.row["num"] }}/{{ props.row["ver"] }}
                </router-link>
                &nbsp;
                <q-btn
                  v-if="props.row['state'] === 'Active'"
                  round
                  color="primary"
                  :href="
                    apiServerHost +
                    '/file/' +
                    props.row['num'] +
                    '/' +
                    props.row['ver'] +
                    '?state=Active'
                  "
                  target="_blank"
                  icon="description"
                  size="xs"
                  data-cy="open-file"
                >
                  <q-tooltip>View first file</q-tooltip>
                </q-btn>
              </span>
              <span v-else-if="col.name === 'sunset_dt'">
                {{
                  props.row[col.name]
                    ? props.row[col.name].substring(0, 10)
                    : ""
                }}
              </span>
              <span v-else-if="col.name === 'state' && props.row[col.name] === 'Signoff'">
                {{ props.row['state'] }}
                <br> Submitted: {{ dispDate(props.row['last_submit_dt']) }}
                <br> {{ props.row['missing_sigs'] }}
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
          <q-space />
          <q-btn
            color="primary"
            :href="apiServerHost + '/spec/?output_csv=true' + filter_slug"
            target="_blank"
            icon="file_download"
            data-cy="open-file"
          />
        </template>
      </q-table>
      <q-dialog v-model="add_spec">
        <create-spec-dialog
          :createMode="true"
          @updateTable="getTableData(page_num)"
        />
      </q-dialog>
    </div>
  </q-page>
</template>

<script>
import { apiServerHost, deleteData, dispDate, postData, retrieveData } from "@/utils.js";

import { ref, onMounted, computed, defineProps, watch } from "vue";
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
const rows_per_page = 20;

const store = useStore();

const rows = ref([]);
const selected = ref([]);

const add_spec = ref(false);
const filter = ref({});
const filter_state = ref([]);
const filter_slug = ref("");
const upd_spec = ref(false);

const page_num = ref(1);
const num_pages = ref();

const isAuthenticated = ref(computed(() => store.getters.authenticated));
const username = ref(computed(() => store.getters.username));

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
  add_spec.value = false; // Close Add Spec popup, if open
  upd_spec.value = false; // Close Update Spec popup, if open
  let data_url = `spec/?_=_${pagination_slug(page_number)}`;
  if (filter_slug.value) {
    data_url = data_url + `${filter_slug.value}`;
  }

  let data_rows = await retrieveData(data_url);
  rows.value = formatRows(data_rows["results"]);

  set_pagination_params(page_number, data_rows.count);
  setSelected();
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

async function applyFilter() {
  filter_slug.value = "";
  Object.entries(filter.value).forEach((entry) => {
    const [key, value] = entry;
    filter_slug.value += "&" + key + "=" + value;
  });
  if (filter_state.value.length > 0) {
    filter_slug.value += "&incl_obsolete=true";
    filter_slug.value +=
      "&state=" +
      filter_state.value
        .map(function (s) {
          return s["value"];
        })
        .join();
  }
  getTableData(1);
}

async function clearFilter() {
  filter.value = {};
  filter_state.value = [];
  applyFilter();
}

async function setWatch(num) {
  let res = await postData(
    `user/watch/${username.value}/${num}`,
    "{}",
    `Set watch on: ${num} successfully.`
  );
  if (res.__resp_status < 300) {
    getTableData(page_num.value);
  }
}

async function clearWatch(num) {
  let res = await deleteData(
    `user/watch/${username.value}/${num}`,
    "{}",
    `Deleted watch on: ${num} successfully.`
  );
  if (res.__resp_status < 300) {
    getTableData(page_num.value);
  }
}

const columns = [
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
    name: "location",
    align: "left",
    label: "Location",
    field: "location",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: false,
  },
  {
    name: "keywords",
    align: "left",
    label: "Keywords",
    field: "keywords",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: false,
  },
  {
    name: "created_by",
    align: "left",
    label: "Created By",
    field: "created_by",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: false,
  },
  {
    name: "state",
    align: "left",
    label: "State",
    field: "state",
    classes: "tab page-col",
    headerStyle: "font-size:large;",
    style: "width: 15em;",
    sortable: false,
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
