<template>
  <q-card class="dialog-window">
        <q-card-section class="bg-primary text-white row ">
            <div class="text-h4">{{props.createMode?'Create':'Update '+props.locationRow['name']}} Location</div>
            <q-btn icon="close" flat round dense data-cy="token-create-close" v-close-popup />
        </q-card-section>
        <q-card-section class="q-pt-none">
            <q-input label="Name" v-model.trim="location" v-show="props.createMode" data-cy="location-create-location"/>
            <q-select label="Active" v-model="active"
                :options="[{label:'True',value:true}, {label:'False',value:false}]"
                data-cy="active-create-location"/>
        </q-card-section>

        <q-card-actions class="bg-white text-teal" align="center">
          <q-btn label="Save" color="primary" icon="save" @click="saveLocation()" data-cy="token-create-create"/>
          <div class="spacer"/>
          <q-btn label="Cancel" color="red" icon="cancel" v-close-popup data-cy="token-create-cancel"/>
        </q-card-actions>
    </q-card>
</template>

<script>
import { defineProps, postData, putData, } from '@/utils.js'
import {ref, defineEmits, onMounted} from 'vue'

export default {
    name: 'CreateLocationDialog',
}
</script>

<script setup>
    const props = defineProps({
        locationRow: Object,
        createMode: Boolean,
    })

    const emit = defineEmits(['updateTable'])

    const active = ref({label:'True',value:true})
    const location = ref('')

    async function saveLocation(){
        const body = {
            name: location.value,
            active: active.value.value,
        }

        if (props.createMode) {
            let res = await postData('loc/', body, 'Successfully created location ' + location.value)
            if (res.__resp_status < 300){
                emit('updateTable')
            }
        }
        else {
            let res = await putData(`loc/${location.value}`, body, 'Successfully updated location ' + location.value)
            if (res.__resp_status < 300){
                emit('updateTable')
            }
        }
    }

    onMounted(() => {
        if (props.locationRow['name'] !== undefined) {
            location.value = props.locationRow['name']
            if (props.locationRow['active']) {active.value = {label:'True',value:true}} else {active.value={label:'False',value:false}}
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
