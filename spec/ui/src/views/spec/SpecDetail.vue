<template>
  <q-page>
    <q-card>
      <q-card-section class="row">
        <q-card-actions class="text-h4">{{
          props.num + " / " + props.ver
        }}</q-card-actions>
        <q-card-actions>
          <q-btn
            v-if="state == null"
            label="Spec not loaded"
            @click="showRevs = !showRevs"
            color="red"
            data-cy="spec-detail-error"
          />
          <q-btn
            v-else
            :label="
              (state != 'Active'
                ? 'This is not an Active revision. Click to '
                : '') + 'Show Revisions'
            "
            :color="state != 'Active' ? 'orange' : 'primary'"
            icon="storage"
            @click="showRevs = !showRevs"
            data-cy="spec-detail-update"
          />
        </q-card-actions>
        <q-space />
        <span v-show="state_loaded === 'Draft'">
          <q-card-actions v-show="!edit">
            <q-btn
              label="Edit"
              color="primary"
              icon="edit"
              @click="edit = true"
              data-cy="spec-detail-update"
            />
            <div class="spacer" />
            <q-btn
              label="Submit"
              color="primary"
              icon="done_all"
              @click="submitSpec()"
              data-cy="spec-detail-cancel"
            />
          </q-card-actions>
          <q-card-actions
            v-show="edit"
            class="bg-white text-teal"
            align="center"
          >
            <q-btn
              label="Save"
              color="primary"
              icon="save"
              @click="saveSpec()"
              data-cy="spec-detail-update"
            />
            <div class="spacer" />
            <q-btn
              label="Delete"
              color="red"
              icon="delete"
              @click="deleteSpec()"
              data-cy="spec-detail-cancel"
            />
            <div class="spacer" />
            <q-btn
              label="Cancel"
              color="red"
              icon="cancel"
              @click="cancel()"
              data-cy="spec-detail-cancel"
            />
          </q-card-actions>
        </span>
        <span
          v-show="
            (state_loaded === 'Active' || state_loaded === 'Obsolete') &&
            isAuthenticated
          "
        >
          <q-card-actions>
            <q-btn
              label="Create New Revision"
              color="primary"
              icon="add"
              @click="reviseSpec()"
              data-cy="spec-detail-update"
            />
          </q-card-actions>
        </span>
        <span v-show="state_loaded !== 'Draft' && isAdmin">
          <q-card-actions v-show="!edit">
            <q-btn
              label="Admin Edit"
              icon="edit"
              color="red"
              @click="edit = true"
              data-cy="spec-detail-update"
            />
          </q-card-actions>
          <q-card-actions v-show="edit">
            <q-btn
              label="Admin Save"
              color="primary"
              icon="save"
              @click="saveSpec()"
              data-cy="spec-detail-update"
            />
            <div class="spacer" />
            <q-btn
              label="Cancel"
              color="red"
              icon="cancel"
              @click="cancel()"
              data-cy="spec-detail-cancel"
            />
          </q-card-actions>
        </span>
      </q-card-section>

      <q-card-section v-show="showRevs" class="row">
        <q-table
          label="All versions of this spec"
          :rows="version_list"
          :columns="spec_columns"
          :rows-per-page-options="[0]"
          hide-bottom
          data-cy="spec-table"
        >
          <template v-slot:top-left>
            <span class="text-h6">Other version(s) of this spec:</span>
          </template>
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
                    :to="
                      '/ui-spec/' + props.row['num'] + '/' + props.row['ver']
                    "
                  >
                    {{ props.row["num"] }}/{{ props.row["ver"] }}
                  </router-link>
                </span>
                <span v-else-if="col.name === 'mod_ts'">
                  {{ dispDate(props.row[col.name]) }}
                </span>
                <span v-else>{{ props.row[col.name] }}</span>
              </q-td>
            </q-tr>
          </template>
        </q-table>
      </q-card-section>

      <q-card-section class="row">
        <table class="paddingBetweenCols">
          <tr>
            <th align="left">State</th>
            <th align="left">Anonymous Access</th>
            <th align="left">Document Type</th>
            <th align="left">Department</th>
            <th align="left">Location</th>
            <th
              align="left"
              v-show="String(jira).length > 0 || (edit && isAdmin)"
            >
              Jira
            </th>
            <th align="left" v-show="String(approved_dt).length > 0">
              Approve Date
            </th>
            <th align="left" v-show="String(sunset_extended_dt).length > 0">
              Date Extended
            </th>
            <th align="left" v-show="String(sunset_dt).length > 0">
              Sunset Date
            </th>
            <th align="left">Created By</th>
          </tr>
          <tr>
            <td>
              <q-select
                v-model="state"
                :options="[
                  { label: 'Draft', value: 'Draft' },
                  { label: 'Signoff', value: 'Signoff' },
                  { label: 'Active', value: 'Active' },
                  { label: 'Obsolete', value: 'Obsolete' },
                ]"
                emit-value
                dense
                :readonly="!edit || !isAdmin"
                data-cy="spec-detail-state"
              />
            </td>
            <td>
              <q-select
                v-model="anon_access"
                :options="[
                  { label: 'True', value: true },
                  { label: 'False', value: false },
                ]"
                data-cy="spec-detail-anon_access"
                dense
                :readonly="!edit || !isAdmin"
              />
            </td>
            <td>
              <q-select
                v-model="doc_type"
                :options="doc_typeList"
                emit-value
                dense
                :readonly="!edit"
                data-cy="spec-detail-doc_type"
              />
            </td>
            <td>
              <q-select
                v-model="department"
                :options="deptList"
                emit-value
                dense
                :readonly="!edit"
                data-cy="spec-detail-department"
                ref="select"
                width="100px"
                :style="`width: ${width}px; word-break: break-all;`"
              />
            </td>
            <td>
              <q-select
                v-model="location"
                :options="locList"
                emit-value
                dense
                :readonly="!edit"
                data-cy="spec-detail-location"
                ref="select"
                width="100px"
                :style="`width: ${width}px; word-break: break-all;`"
              />
            </td>
            <td v-show="String(jira).length > 0 || (edit && isAdmin)">
              <q-input
                v-show="edit && isAdmin"
                label="Jira"
                v-model.trim="jira"
                data-cy="spec-detail-jira"
                dense
              />
              <a
                v-show="!edit || !isAdmin"
                :href="jira_url"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ jira }}
              </a>
            </td>
            <td v-show="String(approved_dt).length > 0">
              {{ approved_dt.substring(0, 10) }}
            </td>
            <td v-show="String(sunset_extended_dt).length > 0">
              {{ sunset_extended_dt.substring(0, 10) }}
            </td>
            <td
              v-show="String(sunset_dt).length > 0"
              :bgcolor="
                new Date().getTime() > sunset_warn_dt && state === 'Active'
                  ? 'orange'
                  : ''
              "
            >
              {{ sunset_dt.substring(0, 10) }}
              <q-btn
                v-if="
                  new Date().getTime() > sunset_warn_dt &&
                  state === 'Active' &&
                  String(sunset_extended_dt).length === 0
                "
                label="Extend"
                icon="more_time"
                @click="extendSunset()"
                data-cy="spec-detail-extend"
              />
            </td>
            <td>
              <q-input
                :disable="!edit || !isAdmin"
                v-model.trim="created_by"
                data-cy="spec-detail-created_by"
                dense
              />
            </td>
          </tr>
        </table>
        <q-space />
        <q-input
          label="Comment"
          v-model.trim="comment"
          data-cy="spec-detail-comment"
          type="textarea"
          class="comment-field"
          v-show="edit"
        />
      </q-card-section>

      <q-card-section class="q-pt-none">
        <q-input
          label="Title"
          v-model.trim="title"
          data-cy="spec-detail-title"
          dense
          :readonly="!edit"
        />
        <q-input
          label="Keywords"
          v-model.trim="keywords"
          data-cy="spec-detail-keywords"
          dense
          :readonly="!edit"
        />
        <q-input
          label="Reason for Change"
          v-model.trim="reason"
          type="textarea"
          data-cy="spec-detail-reason"
          dense
          :readonly="!edit"
        />
      </q-card-section>

      <q-card-section class="q-pt-none row">
        <q-table
          :rows="sigRows"
          :rows-per-page-options="[0]"
          hide-bottom
          data-cy="spec-detail-sigs"
        >
          <template v-slot:header>
            <q-th v-show="edit" />
            <q-th align="left">Role</q-th>
            <q-th align="left">Signer</q-th>
            <q-th align="left">Signed</q-th>
            <q-th align="left">By</q-th>
          </template>
          <template v-slot:top-left>
            <span class="text-h6">Signatures:</span>
          </template>
          <template v-slot:body="tprops">
            <q-tr>
              <q-td v-show="edit">
                <q-btn
                  round
                  color="negative"
                  @click="deleteSig(tprops.row)"
                  icon="delete"
                  size="xs"
                  dense
                  data-cy="data-delete-btn"
                  v-show="!tprops.row['from_am']"
                ></q-btn>
              </q-td>
              <q-td v-if="!tprops.row['_new']" style="white-space: nowrap">
                {{ tprops.row["role"] }}
                <span v-show="tprops.row['spec_one']">*</span>
              </q-td>
              <q-td v-else>
                <q-select
                  v-model="tprops.row['role']"
                  :options="roleList"
                  emit-value
                  dense
                  :readonly="!edit"
                />
              </q-td>
              <q-td>
                <q-select
                  v-if="
                    edit &&
                    roleUserMap[tprops.row['role']] &&
                    roleUserMap[tprops.row['role']].length > 1
                  "
                  v-model="tprops.row['signer']"
                  :options="roleUserMap[tprops.row['role']]"
                  emit-value
                  dense
                  :readonly="!edit"
                />
                <q-input
                  v-else
                  v-model="tprops.row['signer']"
                  :data-cy="genCy(`signer`, tprops.row['signer'])"
                  dense
                  borderless
                  :readonly="!edit"
                />
              </q-td>
              <q-td>
                {{ dispDate(tprops.row["signed_dt"]) }}
                <q-btn
                  v-if="
                    state_loaded === 'Signoff' &&
                    tprops.row['signed_dt'] === null
                  "
                  label="Sign"
                  icon="thumb_up"
                  @click="signRole(tprops.row)"
                  data-cy="spec-detail-sign"
                />
                <q-btn
                  v-if="
                    state_loaded === 'Signoff' &&
                    tprops.row['signed_dt'] === null
                  "
                  label="Reject"
                  icon="thumb_down"
                  @click="rejectRole(tprops.row)"
                  data-cy="spec-detail-reject"
                />
              </q-td>
              <q-td>{{ tprops.row["delegate"] }}</q-td>
            </q-tr>
          </template>
          <template v-slot:bottom-row v-if="edit">
            <q-btn
              color="primary"
              dense
              @click="sigRows.push({ _new: true })"
              icon-right="add"
              size="xs"
              no-caps
              data-cy="add_sig-btn"
              v-show="edit"
            ></q-btn>
          </template>
        </q-table>
        <q-space />
        <q-table
          :rows="refRows"
          :rows-per-page-options="[0]"
          hide-bottom
          data-cy="spec-detail-refs"
        >
          <template v-slot:top-left>
            <span class="text-h6">References:</span>
          </template>
          <template v-slot:header>
            <q-th v-show="edit" />
            <q-th align="left">Spec Number</q-th>
            <q-th align="left" v-show="edit">Version (optional)</q-th>
          </template>
          <template v-slot:body="tprops">
            <q-tr>
              <q-td v-show="edit">
                <q-btn
                  round
                  color="negative"
                  @click="deleteRef(tprops.row)"
                  icon="delete"
                  size="xs"
                  dense
                  data-cy="ref-delete-btn"
                ></q-btn>
              </q-td>
              <q-td v-show="!edit">
                <router-link
                  :to="
                    '/ui-spec/' + tprops.row['num'] + '/' + tprops.row['ver']
                  "
                  v-if="tprops.row['ver'] !== null"
                >
                  {{ tprops.row["num"] }}/{{ tprops.row["ver"] }}
                </router-link>
                <router-link
                  :to="'/ui-spec/' + tprops.row['num'] + '/*'"
                  v-else
                >
                  {{ tprops.row["num"] }}
                </router-link>
              </q-td>
              <q-td v-show="edit">
                <q-input
                  v-model.trim="tprops.row['num']"
                  type="number"
                  data-cy="spec-detail-ref-num"
                  dense
                  borderless
                  :readonly="!edit"
                />
              </q-td>
              <q-td v-show="edit">
                <q-input
                  v-model.trim="tprops.row['ver']"
                  data-cy="spec-detail-ref-ver"
                  dense
                  borderless
                  :readonly="!edit"
                />
              </q-td>
            </q-tr>
          </template>
          <template v-slot:bottom-row v-if="edit">
            <q-btn
              color="primary"
              dense
              @click="refRows.push({ _new: true })"
              icon-right="add"
              size="xs"
              no-caps
              data-cy="add_ref-btn"
              v-show="edit"
            ></q-btn>
          </template>
        </q-table>
        <q-space />
        <q-table
          :rows="fileRows"
          :rows-per-page-options="[0]"
          hide-bottom
          data-cy="spec-detail-files"
        >
          <template v-slot:top-left>
            <span class="text-h6">Files:</span>
          </template>
          <template v-slot:header>
            <q-th/>
            <q-th align="left" v-if="gen_pdf">Add to PDF</q-th>
          </template>
          <template v-slot:body="tprops">
            <q-tr>
              <q-td>
              <span v-show="edit" style="margin-right: 1vw;">
                <q-btn
                  round
                  color="negative"
                  @click="deleteFile(tprops.row)"
                  icon="delete"
                  size="xs"
                  dense
                  data-cy="file-delete-btn"
                ></q-btn>
                <q-btn
                  round
                  @click="moveFileRowUp(tprops.row)"
                  icon="arrow_upward"
                  size="xs"
                  dense
                  data-cy="file-move-up-btn"
                ></q-btn>
                <q-btn
                  round
                  @click="moveFileRowDown(tprops.row)"
                  icon="arrow_downward"
                  size="xs"
                  dense
                  data-cy="file-move-down-btn"
                ></q-btn>
              </span>
              <span>
                <a
                  :href="
                    apiServerHost +
                    '/file/' +
                    props.num +
                    '/' +
                    props.ver +
                    '/' +
                    encodeURIComponent(tprops.row['filename']) +
                    '?state=' +
                    state
                  "
                  data-cy="spec-detail-file-filename"
                  target="_blank"
                >
                  {{ tprops.row["filename"] }}
                </a>
              </span>
              </q-td>
              <q-td v-if="gen_pdf">
                <q-checkbox
                  v-if="disp_incl_pdf(tprops.row)"
                  v-model="tprops.row['incl_pdf']"
                  dense
                  :disable="!edit"
                  data-cy="spec-detail-ref-ver"
                />
              </q-td>
              <q-td></q-td>
            </q-tr>
          </template>
          <template v-slot:bottom-row v-if="edit">
            <q-uploader
              class="my-card"
              :fieldName="(file) => `file`"
              :headers="[
                { name: 'X-CSRFToken', value: getCookie('csrftoken') },
              ]"
              with-credentials
              :url="
                (files) => `${apiServerHost}/file/${props.num}/${props.ver}`
              "
              label="Select File to Upload"
              @uploaded="refreshFileList"
              data-cy="add_file-uploader"
              multiple
            />
          </template>
        </q-table>
      </q-card-section>

      <q-card-section class="q-pt-none">
        <span class="text-h6">History:</span>
        <span class="row">
          <q-table
            :rows="histRows"
            :rows-per-page-options="[0]"
            hide-bottom
            data-cy="spec-detail-files"
          >
            <template v-slot:header>
              <q-th align="left">Who</q-th>
              <q-th align="left">When</q-th>
              <q-th align="left">Operation</q-th>
              <q-th align="left">Comment</q-th>
            </template>
            <template v-slot:body="tprops">
              <q-tr>
                <q-td>{{ tprops.row["upd_by"] }}</q-td>
                <q-td>{{ dispDate(tprops.row["mod_ts"]) }}</q-td>
                <q-td>{{ tprops.row["change_type"] }}</q-td>
                <q-td>
                  <pre>{{ tprops.row["comment"] }}</pre>
                </q-td>
              </q-tr>
            </template>
          </q-table>
        </span>
      </q-card-section>

      <q-dialog v-model="submitDisabled" no-esc-dismiss no-backdrop-dismiss>
        <q-card>
          <q-card-section align="center">
            <h4>Changing Spec state to Signoff. Please wait</h4>
            <p>This may take a minute while:</p>
            <list>
              <li>PDF file is generated</li>
              <li>Jira stories are updated</li>
              <li>Signers are notified</li>
            </list>
            <br />
            <p>Do not refresh the page.</p>
          </q-card-section>
        </q-card>
      </q-dialog>

      <q-dialog v-model="deleteDisabled" no-esc-dismiss no-backdrop-dismiss>
        <q-card>
          <q-card-section align="center">
            <h4>Deleting Spec. Please wait</h4>
            <p>This may take a minute while:</p>
            <list>
              <li>Spec is removed</li>
              <li>Jira stories are deleted</li>
              <li>Files are removed</li>
            </list>
            <br />
            <p>Do not refresh the page.</p>
          </q-card-section>
        </q-card>
      </q-dialog>

      <q-dialog v-model="signoffDisabled" no-esc-dismiss no-backdrop-dismiss>
        <q-card>
          <q-card-section align="center">
            <h4>Recording Signoff on spec. Please wait</h4>
            <p>This may take a minute on last signature while:</p>
            <list>
              <li>Jira stories are updated</li>
              <li>Watchers are notified</li>
            </list>
            <br />
            <p>Do not refresh the page.</p>
          </q-card-section>
        </q-card>
      </q-dialog>
    </q-card>
    <q-dialog v-model="extend_spec">
      <extend-spec-dialog
        :num="props.num"
        :ver="props.ver"
        @updateSpec="loadSpec()"
      />
    </q-dialog>
    <q-dialog v-model="reject_spec">
      <reject-spec-dialog
        :num="props.num"
        :ver="props.ver"
        :sigRow="sigRow"
        @updateSpec="loadSpec()"
      />
    </q-dialog>
    <q-dialog v-model="revise_spec">
      <revise-spec-dialog
        :num="props.num"
        :ver="props.ver"
        @updateSpec="loadSpec()"
      />
    </q-dialog>
    <q-dialog v-model="login">
      <login-popup-page
        @close="
          login = false;
          loadSpec();
        "
      />
    </q-dialog>
  </q-page>
</template>

<script>
import {
  apiServerHost,
  defineProps,
  deleteData,
  dispDate,
  genCy,
  getCookie,
  postData,
  putData,
  retrieveData,
} from "@/utils.js";
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useStore } from "vuex";
import LoginPopupPage from "@/components/LoginPopup.vue";
import ExtendSpecDialog from "@/views/spec/ExtendSpec.vue";
import RejectSpecDialog from "@/views/spec/RejectSpec.vue";
import ReviseSpecDialog from "@/views/spec/ReviseSpec.vue";

export default {
  name: "SpecDetailPage",
  components: {
    ExtendSpecDialog,
    RejectSpecDialog,
    ReviseSpecDialog,
  },
};
</script>

<script setup>
const props = defineProps({
  num: String,
  ver: String,
  gen_pdf: Boolean,
});
const store = useStore();

const anon_access = ref({ label: "False", value: false });
const approved_dt = ref("");
const comment = ref("");
const created_by = ref("");
const create_dt = ref("");
const deleteDisabled = ref(false);
const department = ref("");
const deptList = ref([]);
const doc_type = ref("");
const doc_typeList = ref([]);
const edit = ref(false);
const extend_spec = ref(false);
const isAdmin = ref(computed(() => store.getters.isAdmin));
const isAuthenticated = ref(computed(() => store.getters.authenticated));
const keywords = ref("");
const location = ref("");
const locList = ref([]);
const fileRows = ref([]);
const histRows = ref([]);
const jira = ref("");
const jira_url = ref("");
const login = ref(false);
const mod_ts = ref("");
const reason = ref("");
const refRows = ref([]);
const reject_spec = ref(false);
const revise_spec = ref(false);
const roleList = ref([]);
const roleUserMap = ref({});
const router = useRouter();
const showRevs = ref(false);
const sigRow = ref({});
const sigRows = ref([]);
const signoffDisabled = ref(false);
const state = ref("");
const state_loaded = ref("");
const submitDisabled = ref(false);
const sunset_dt = ref("");
const sunset_extended_dt = ref("");
const sunset_warn_dt = ref("");
const title = ref("");
const version_list = ref([]);

async function saveSpec() {
  const body = {
    state: state.value,
    doc_type: doc_type.value,
    department: department.value,
    location: location.value,
    title: title.value,
    keywords: keywords.value,
    reason: reason.value,
    jira: jira.value,
    sigs: sigRows.value,
    files: fileRows.value,
    refs: refRows.value,
    comment: comment.value,
    anon_access: anon_access.value.value,
    created_by: created_by.value,
  };

  let res = await putData(
    `spec/${props.num}/${props.ver}`,
    body,
    "Successfully updated spec " + props.num + "/" + props.ver
  );
  if (res.__resp_status < 300) {
    edit.value = false;
    loadForm(res);
  }
}

onMounted(() => {
  loadSpec();
  loadOtherVersions();
  loadLists();
});

function cancel() {
  window.location.reload();
}

async function deleteFile(fileRow) {
  if (!window.confirm(`Delete file: ${fileRow.filename}?`)) {
    return;
  }
  let res = await deleteData(
    `file/${props.num}/${props.ver}/${encodeURIComponent(fileRow.filename)}`,
    {},
    `Deleting file: ${fileRow.filename}`
  );
  fileRows.value.splice(fileRows.value.indexOf(fileRow), 1);
}

function deleteRef(refRow) {
  refRows.value.splice(refRows.value.indexOf(refRow), 1);
}

function deleteSig(sigRow) {
  sigRows.value.splice(sigRows.value.indexOf(sigRow), 1);
}

async function deleteSpec() {
  if (!window.confirm(`Delete spec: ${props.num}/${props.ver}?`)) {
    return;
  }

  deleteDisabled.value = true;
  let res = await deleteData(
    `spec/${props.num}/${props.ver}`,
    "{}",
    `Deleted spec: ${props.num}/${props.ver} successfully.`
  );
  if (res.__resp_status < 300) {
    router.push({ name: "Spec" });
  }
  deleteDisabled.value = false;
}

//check if string ends with any of array suffixes
function endsWithAny(suffixes, string) {
  for (let suffix of suffixes) {
    if (string.endsWith(suffix)) return true;
  }
  return false;
}

// Only extensions LibreOffice knows how to translate to pdf should be included here
function disp_incl_pdf(row) {
  if (
    endsWithAny(
      [".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".pdf"],
      row["filename"]
    )
  ) {
    return true;
  } else {
    row["incl_pdf"] = false;
    return false;
  }
}

async function extendSunset() {
  extend_spec.value = true;
}

function loadForm(res) {
  edit.value = false;
  extend_spec.value = false;
  reject_spec.value = false;
  revise_spec.value = false;

  anon_access.value = res["anon_access"]
    ? { label: "True", value: true }
    : { label: "False", value: false };
  approved_dt.value = res["approved_dt"] ? res["approved_dt"] : "";
  created_by.value = res["created_by"];
  create_dt.value = res["create_dt"];
  department.value = res["department"];
  doc_type.value = res["doc_type"];
  fileRows.value = res["files"];
  histRows.value = res["hist"];
  jira.value = res["jira"];
  jira_url.value = res["jira_url"];
  keywords.value = res["keywords"];
  location.value = res["location"];
  mod_ts.value = res["mod_ts"];
  reason.value = res["reason"];
  refRows.value = res["refs"];
  sigRows.value = res["sigs"];
  state.value = res["state"];
  state_loaded.value = res["state"];
  sunset_dt.value =
    "sunset_dt" in res && res["sunset_dt"] != null ? res["sunset_dt"] : "";
  sunset_extended_dt.value = res["sunset_extended_dt"]
    ? res["sunset_extended_dt"]
    : "";
  sunset_warn_dt.value =
    "sunset_warn_dt" in res && res["sunset_warn_dt"] != null
      ? new Date(res["sunset_warn_dt"])
      : null;
  title.value = res["title"];
}

async function loadOtherVersions() {
  let res = await retrieveData(`spec/${props.num}?incl_obsolete=true`);
  version_list.value = res["results"];
  /* Put the most recent at the top of the list */
  version_list.value.sort((a, b) => {
    return -1 * a.create_dt.localeCompare(b.create_dt);
  });
}

async function loadSpec() {
  let res = await retrieveData(
    `spec/${props.num}/${props.ver ? props.ver : "*"}`
  );
  if (!props.ver || props.ver === "*") {
    router.push({
      name: "Spec Detail",
      params: { num: res.num, ver: res.ver },
    });
  }
  loadForm(res);

  if (res.state == null && !isAuthenticated.value) {
    login.value = true;
  }
}

async function moveFileRowUp(fileRow) {
  var rownum = fileRows.value.indexOf(fileRow);
  if (rownum <= 0) {
    return;
  }

  var row = fileRows.value.splice(rownum, 1)[0];
  fileRows.value.splice(rownum - 1, 0, row);
}

async function moveFileRowDown(fileRow) {
  var rownum = fileRows.value.indexOf(fileRow);
  if (rownum >= fileRows.value.length) {
    return;
  }

  var row = fileRows.value.splice(rownum, 1)[0];
  fileRows.value.splice(rownum + 1, 0, row);
}

async function refreshFileList() {
  let res = await retrieveData(`spec/${props.num}/${props.ver}`);
  fileRows.value = res["files"];
}

async function rejectRole(row) {
  sigRow.value = row;
  reject_spec.value = true;
}

async function reviseSpec() {
  revise_spec.value = true;
}

async function signRole(sigRow) {
  signoffDisabled.value = true;
  let res = await postData(
    `sign/${props.num}/${props.ver}`,
    { role: sigRow["role"], signer: sigRow["signer"] },
    `Signed spec: ${props.num}/${props.ver} successfully.`
  ).then((res) => {
    if (res.__resp_status < 300) {
      router.go();
    }
  });
  signoffDisabled.value = false;
}

async function submitSpec() {
  submitDisabled.value = true;
  await postData(
    `submit/${props.num}/${props.ver}`,
    {},
    `Submitted spec: ${props.num}/${props.ver} for signatures successfully.`
  ).then((res) => {
    if (res.__resp_status < 300) {
      router.go();
    }
  });
  submitDisabled.value = false;
}

async function loadLists() {
  let data_rows = await retrieveData("role/?limit=1000");
  roleList.value = data_rows["results"].map((e) => {
    return { label: e["role"], value: e["role"] };
  });
  roleUserMap.value = {};
  data_rows["results"].forEach((entry) => {
    roleUserMap.value[entry["role"]] = [{ label: "Any", value: "" }].concat(
      entry["user_arr"].map((e) => {
        let label = e["username"] + ", " + e["first_name"] + " " + e["last_name"];
        if (e["descr"]) {
            label += " (" + e["descr"] + ")"
        }
        return {
          label: label,
          value: e["username"],
        };
      })
    );
  });

  data_rows = await retrieveData("doctype/?limit=1000");
  doc_typeList.value = data_rows["results"].map((e) => {
    return { label: e["name"], value: e["name"] };
  });

  data_rows = await retrieveData("dept/?limit=1000");
  deptList.value = data_rows["results"].map((e) => {
    return { label: e["name"], value: e["name"] };
  });

  data_rows = await retrieveData("loc/?limit=1000");
  locList.value = data_rows["results"].map((e) => {
    return { label: e["name"], value: e["name"] };
  });
}

const spec_columns = [
  { name: "num", align: "left", label: "Spec", field: "num" },
  { name: "title", align: "left", label: "Title", field: "title" },
  { name: "doc_type", align: "left", label: "Doc Type", field: "doc_type" },
  { name: "department", align: "left", label: "Department", field: "department", },
  { name: "location", align: "left", label: "Location", field: "location", },
  { name: "keywords", align: "left", label: "Keywords", field: "keywords" },
  { name: "state", align: "left", label: "State", field: "state" },
  { name: "created_by", align: "left", label: "Created By", field: "created_by", },
  { name: "mod_ts", align: "left", label: "Last Modified", field: "mod_ts" },
];
</script>

<style scoped>
.comment-field {
  width: 50%;
}
.dialog_window {
  max-width: 50vw;
  width: 50vw;
}
.paddingBetweenCols th {
  padding: 0 20px 0 0;
}
td {
  padding: 0 20px 0 0;
}
.spacer {
  width: 2vw;
}
</style>
