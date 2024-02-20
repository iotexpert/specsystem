<template>
  <q-card class="dialog-window">
        <q-card-section class="bg-primary text-white row ">
            <div class="text-h4">{{props.createMode?'Create':'Update '+props.roleRow['role']}} Role</div>
            <q-btn icon="close" flat round dense data-cy="token-create-close" v-close-popup />
        </q-card-section>
        <q-card-section class="q-pt-none">
            <q-input label="Role" v-model.trim="role" v-show="props.createMode" data-cy="role-create-role"/>
            <q-input label="Description" v-model.trim="descr" data-cy="descr-create-role"/>
            <q-select label="Must Specify Signer" v-model="spec_one"
                :options="[{label:'True',value:true}, {label:'False',value:false}]"
                data-cy="spec_one-create-role"/>
            <q-input label="Signers" v-model.trim="signers"  data-cy="signers-create-role"/>
            <q-select label="Active" v-model="active"
                :options="[{label:'True',value:true}, {label:'False',value:false}]"
                data-cy="active-create-role"/>
        </q-card-section>

        <q-card-actions class="bg-white text-teal" align="center">
          <q-btn label="Save" color="primary" icon="save" @click="saveRole()" data-cy="token-create-create"/>
          <div class="spacer"/>
          <q-btn label="Cancel" color="red" icon="cancel" v-close-popup data-cy="token-create-cancel"/>
        </q-card-actions>
    </q-card>
</template>

<script>
import { defineProps, postData, putData } from '@/utils.js'
import {ref, defineEmits, onMounted} from 'vue'

export default {
    name: 'CreateRoleDialog',
}
</script>

<script setup>
    const props = defineProps({
        roleRow: Object,
        createMode: Boolean,
    })

    const emit = defineEmits(['updateTable'])

    const active = ref({label:'True',value:true})
    const role = ref('')
    const descr = ref('')
    const spec_one = ref({label:'True',value:true})
    const signers = ref('')

    async function saveRole(){
        const body = {
            role: role.value,
            descr: descr.value,
            spec_one: spec_one.value.value,
            users: signers.value,
            active: active.value.value,
        }

        if (props.createMode) {
            let res = await postData('role/', body, 'Successfully created role ' + role.value)
            if (res.__resp_status < 300){
                emit('updateTable')
            }
        }
        else {
            let res = await putData(`role/${role.value}`, body, 'Successfully updated role ' + role.value)
            if (res.__resp_status < 300){
                emit('updateTable')
            }
        }
    }

    onMounted(() => {
        if (props.roleRow['role'] !== undefined) {
            role.value = props.roleRow['role']
            descr.value = props.roleRow['descr']
            if (props.roleRow['spec_one']) {spec_one.value = {label:'True',value:true}} else {spec_one.value={label:'False',value:false}}
            signers.value = props.roleRow['users']
            if (props.roleRow['active']) {active.value = {label:'True',value:true}} else {active.value={label:'False',value:false}}
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
