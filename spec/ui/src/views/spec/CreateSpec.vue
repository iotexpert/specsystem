<template>
  <q-card class="dialog-window">
        <q-card-section class="bg-primary text-white row ">
            <q-btn color="primary" icon="adb" @click="adminMode=!adminMode" v-if="isAdmin" dense data-cy="spec-admin-create"/>
            <q-space/>
            <div class="text-h4">Create Spec</div>
            <q-btn icon="close" flat round dense data-cy="spec-create-close" v-close-popup />
        </q-card-section>
        <q-card-section class="q-pt-none">
            <q-input label="Num" v-model.trim="num" v-if="adminMode" data-cy="spec-create-num"/>
            <q-input label="Ver" v-model.trim="ver" v-if="adminMode" data-cy="spec-create-ver"/>
            <q-select
                label="Document Type"
                v-model="doc_type"
                :options="doc_typeList"
                emit-value
                data-cy="spec-create-doc_type"
            />
            <q-select
                label="Department"
                v-model="department"
                :options="deptList"
                emit-value
                data-cy="spec-create-department"
            />
            <q-select
                label="Location"
                v-model="location"
                :options="locList"
                emit-value
                data-cy="spec-create-location"
            />
            <q-input label="Title" v-model.trim="title" data-cy="spec-create-title"/>
        </q-card-section>

        <q-card-actions class="bg-white text-teal" align="center">
          <q-btn label="Save" color="primary" icon="save" @click="saveSpec()" v-if="!adminMode" data-cy="spec-create-create"/>
          <q-btn label="Create with ID" color="red" icon="save" @click="saveSpec()" v-else data-cy="spec-create-create-admin"/>
          <div class="spacer"/>
          <q-btn label="Cancel" color="red" icon="cancel" v-close-popup data-cy="spec-create-cancel"/>
        </q-card-actions>

        <q-dialog v-model="waiting" no-esc-dismiss no-backdrop-dismiss>
            <q-card>
                <q-card-section align="center">
                    <h4>Creating new spec. Please wait</h4>
                    <p>This may take a minute while the Spec and Jira stories are created.</p>
                    <br/>
                    <p>Do not refresh the page.</p>
                </q-card-section>
            </q-card>
        </q-dialog>
    </q-card>
</template>

<script>
import { postData, retrieveData, showNotif, } from '@/utils.js'
import { computed, onMounted, ref, } from 'vue'
import { useStore } from 'vuex'
import { useRouter, } from 'vue-router'

export default {
    name: 'CreateSpecDialog',
}
</script>

<script setup>
    const store = useStore()

    const adminMode = ref(false)
    const department = ref('')
    const deptList = ref([])
    const doc_type = ref('')
    const doc_typeList = ref([])
    const isAdmin = ref(computed(() => store.getters.isAdmin))
    const location = ref('')
    const locList = ref([])
    const num = ref('')
    const router=useRouter();
    const title = ref('')
    const ver = ref('')
    const waiting = ref(false)

    async function saveSpec(){
        waiting.value = true
        const body = {
            num: adminMode.value ? num.value : null,
            ver: adminMode.value ? ver.value : null,
            state: 'Draft',
            title: title.value,
            doc_type: doc_type.value,
            department: department.value,
            location: location.value,
            sigs:[],
            refs:[],
            files:[]
        }


        let res = await postData('spec/', body, null)
        if (res.__resp_status < 300) {
            showNotif(`Spec created: ${res.num}/${res.ver}`, 'green')
            router.push({name:"Spec Detail", params:{num:res.num, ver:res.ver}})
        }

        waiting.value = false
    }

    onMounted(() => {
        waiting.value = false
        loadLists()
    })

    async function loadLists() {
        let data_rows = await retrieveData('doctype/?active=true&limit=1000');
        doc_typeList.value = data_rows['results'].map((e) => {return ({label:e['name'],value:e['name']})})

        data_rows = await retrieveData('dept/?active=true&limit=1000');
        deptList.value = data_rows['results'].map((e) => {return ({label:e['name'],value:e['name']})})

        data_rows = await retrieveData('loc/?active=true&limit=1000');
        locList.value = data_rows['results'].map((e) => {return ({label:e['name'],value:e['name']})})
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
