<template>
  <q-card class="dialog-window">
        <q-card-section class="bg-primary text-white row ">
            <div class="text-h4">{{props.createMode?'Create':'Update '}} Approval Matrix</div>
            <q-btn icon="close" flat round dense data-cy="token-create-close" v-close-popup />
        </q-card-section>
        <q-card-section class="q-pt-none">
            <q-select
                label="Document Type"
                v-model="doc_type"
                :options="doc_typeList"
                emit-value
                :disable="!props.createMode"
                data-cy="doc_type-create-ApprovalMatrix"
            />
            <q-select
                label="Department"
                v-model="department"
                :options="deptList"
                emit-value
                :disable="!props.createMode"
                data-cy="department-create-ApprovalMatrix"
            />
            <q-input label="Required Signer Roles" v-model.trim="signRoles"  data-cy="signRoles-create-ApprovalMatrix"/>
        </q-card-section>

        <q-card-actions class="bg-white text-teal" align="center">
          <q-btn label="Save" color="primary" icon="save" @click="saveApprovalMatrix()" data-cy="ApprovalMatrix-create-create"/>
          <div class="spacer"/>
          <q-btn label="Cancel" color="red" icon="cancel" v-close-popup data-cy="ApprovalMatrix-create-cancel"/>
        </q-card-actions>
    </q-card>
</template>

<script>
import { defineProps, postData, putData, retrieveData, } from '@/utils.js'
import {ref, defineEmits, onMounted} from 'vue'

export default {
    name: 'CreateApprovalMatrixDialog',
}
</script>

<script setup>
    const props = defineProps({
        ApprovalMatrixRow: Object,
        createMode: Boolean,
    })

    const emit = defineEmits(['updateTable'])

    const department = ref('')
    const deptList = ref([])
    const doc_type = ref('')
    const doc_typeList = ref([])
    const id = ref('')
    const signRoles = ref('')

    async function saveApprovalMatrix(){
        const body = {
            doc_type: doc_type.value,
            department: department.value,
            signRoles: signRoles.value,
        }

        if (props.createMode) {
            let res = await postData('approvalmatrix/', body, 'Successfully created ApprovalMatrix ')
            if (res.__resp_status < 300){
                emit('updateTable')
            }
        }
        else {
            let res = await putData(`approvalmatrix/${id.value}`, body, 'Successfully updated ApprovalMatrix ')
            if (res.__resp_status < 300){
                emit('updateTable')
            }
        }
    }

    onMounted(() => {
        if (props.ApprovalMatrixRow['id'] !== undefined) {
            id.value = props.ApprovalMatrixRow['id']
            doc_type.value = props.ApprovalMatrixRow['doc_type']
            department.value = props.ApprovalMatrixRow['department']
            signRoles.value = props.ApprovalMatrixRow['signRoles']
        }

        loadLists()
    })

    async function loadLists() {
        let data_rows = await retrieveData('doctype/?active=true&limit=1000');
        doc_typeList.value = data_rows['results'].map((e) => {return ({label:e['name'],value:e['name']})})

        data_rows = await retrieveData('dept/?active=true&limit=1000');
        deptList.value = data_rows['results'].map((e) => {return ({label:e['name'],value:e['name']})})
    }
</script>

<style scoped>
.dialog_window{
    max-width: 50vw;
    width: 50vw;
}

.spacer{
    width: 2vw;
}
</style>
