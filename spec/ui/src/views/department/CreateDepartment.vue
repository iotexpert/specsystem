<template>
  <q-card class="dialog-window">
        <q-card-section class="bg-primary text-white row ">
            <div class="text-h4">{{props.createMode?'Create':'Update '+props.departmentRow['name']}} Department</div>
            <q-btn icon="close" flat round dense data-cy="token-create-close" v-close-popup />
        </q-card-section>
        <q-card-section class="q-pt-none">
            <q-input label="Name" v-model.trim="department" v-show="props.createMode" data-cy="department-create-department"/>
            <q-input label="Read Roles" v-model.trim="readRoles" data-cy="readroles-create-department"/>
            <q-select label="Active" v-model="active"
                :options="[{label:'True',value:true}, {label:'False',value:false}]"
                data-cy="active-create-department"/>
        </q-card-section>

        <q-card-actions class="bg-white text-teal" align="center">
          <q-btn label="Save" color="primary" icon="save" @click="saveDepartment()" data-cy="token-create-create"/>
          <div class="spacer"/>
          <q-btn label="Cancel" color="red" icon="cancel" v-close-popup data-cy="token-create-cancel"/>
        </q-card-actions>
    </q-card>
</template>

<script>
import { defineProps, postData, putData } from '@/utils.js'
import {ref, defineEmits, onMounted} from 'vue'

export default {
    name: 'CreateDepartmentDialog',
}
</script>

<script setup>
    const props = defineProps({
        departmentRow: Object,
        createMode: Boolean,
    })

    const emit = defineEmits(['updateTable'])

    const active = ref({label:'True',value:true})
    const department = ref('')
    const readRoles = ref('')

    async function saveDepartment(){
        const body = {
            name: department.value,
            readRoles: readRoles.value,
            active: active.value.value,
        }

        if (props.createMode) {
            let res = await postData('dept/', body, 'Successfully created department ' + department.value)
            if (res.__resp_status < 300){
                emit('updateTable')
            }
        }
        else {
            let res = await putData(`dept/${department.value}`, body, 'Successfully updated department ' + department.value)
            if (res.__resp_status < 300){
                emit('updateTable')
            }
        }
    }

    onMounted(() => {
        if (props.departmentRow['name'] !== undefined) {
            department.value = props.departmentRow['name']
            readRoles.value = props.departmentRow['readRoles']
            if (props.departmentRow['active']) {active.value = {label:'True',value:true}} else {active.value={label:'False',value:false}}
        }
    })
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
