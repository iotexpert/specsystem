<template>
  <q-card class="dialog-window">
        <q-card-section class="bg-primary text-white row ">
            <div class="text-h4">Reject Spec</div>
            <q-btn icon="close" flat round dense data-cy="spec-create-close" v-close-popup /> 
        </q-card-section>
        <q-card-section class="q-pt-none">
            <q-input label="Reason" v-model.trim="comment" type="textarea" data-cy="spec-reject-comment"/>
        </q-card-section>

        <q-card-actions class="bg-white text-teal" align="center">
          <q-btn label="Reject" color="primary" icon="thumb_down" @click="rejectRole()" data-cy="spec-create-create"/>
          <div class="spacer"/>
          <q-btn label="Cancel" color="red" icon="cancel" v-close-popup data-cy="spec-create-cancel"/>
        </q-card-actions>

        <q-dialog v-model="rejectDisabled" no-esc-dismiss no-backdrop-dismiss>
            <q-card>
                <q-card-section align="center">
                    <h4>Rejecting spec. Please wait</h4>
                    <p>This may take a minute while the Spec and Jira stories are updated.</p>
                    <br/>
                    <p>Do not refresh the page.</p>
                </q-card-section>
            </q-card>
        </q-dialog>
    </q-card>
</template>

<script>
import { defineProps, postData, } from '@/utils.js'
import { defineEmits, ref, onMounted} from 'vue'

export default {
    name: 'RejectSpecDialog',
}
</script>

<script setup>
    const props = defineProps({
        num: String,
        ver: String,
        sigRow: Object,
    })
    const comment = ref('')
    const emit = defineEmits(['updateSpec'])
    const rejectDisabled = ref(false)

    async function rejectRole(){
        rejectDisabled.value = true
        let res = await postData(`reject/${props.num}/${props.ver}`, 
            {'role':props.sigRow['role'], 'signer':props.sigRow['signer'], 'comment':comment.value}, 
            `Rejected spec: ${props.num}/${props.ver} successfully.`)
        if (res.__resp_status < 300){
            emit('updateSpec')
        }
        rejectDisabled.value = false
    }

    onMounted(() => {
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
