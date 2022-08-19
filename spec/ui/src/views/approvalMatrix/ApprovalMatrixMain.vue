<template>
    <q-page class="flex flex-center">
        <div class="q-pa-md window-width">
            <q-table
                title="Categories"
                :rows="rows"
                :columns="columns"
                separator="cell"
                row-key="ApprovalMatrix"
                :rows-per-page-options="[0]"
                data-cy="ApprovalMatrix-table">
                <template v-slot:top-left>
                    <div class="row">
                        <q-input 
                            v-model="filter_val"
                            @keydown.enter.prevent="applyFilter(`&search=${filter_val}`)"                             
                            label="filter value"
                            data-cy="data-filter-input"/>
                        <q-btn round color="primary" 
                            @click="clearFilters()"
                            icon="clear"
                            no-caps
                            data-cy="data-clear-filter-btn">                       
                        </q-btn>
                    </div>
                </template>
                <template v-slot:top-right>
                    <q-btn color="primary" 
                        v-show="isSupervisor && isAuthenticated"
                        @click="add_ApprovalMatrix = true"
                        label="Add ApprovalMatrix"
                        icon-right="add"
                        no-caps
                        data-cy="data-row-btn">
                    </q-btn>
                </template>
                <template v-slot:header="props">
                    <q-th v-show="isSupervisor && isAuthenticated" style="width: 15em">
                    </q-th>
                    <q-th v-for="col in columns" 
                          :key="col.name" 
                          :props="props" >
                            {{col.label}}
                    </q-th>
                </template>
                <template v-slot:body="props">
                    <q-tr :props="props" @click="props.row._new_row && !props.selected ? props.selected=true : false">
                        <q-td v-show="isSupervisor && isAuthenticated">
                            <q-btn round color="negative" 
                                    @click="deleteSelected(props.row)"
                                    icon="delete" size="xs"
                                    data-cy="data-delete-btn">
                            </q-btn>
                            <q-btn round color="primary" 
                                    @click="updateSelected(props.row)"
                                    icon="edit" size="xs"
                                    data-cy="data-edit-btn">
                            </q-btn>
                        </q-td>
                        <q-td v-for="col in props.cols" :key="col.name" :props="props" class='text-center'>
                            {{props.row[col.name]}}
                        </q-td>
                    </q-tr>
                </template>
                <template v-slot:bottom>
                    <q-btn @click="getTableData(page_num - 1)" :disable="page_num == 1" data-cy="data-prev-btn">
                        {{'<'}}
                    </q-btn>
                    <q-input input-class="text-right" 
                             v-model="page_num" 
                             class="page-input" 
                             @keydown.enter.prevent="getTableData(page_num)" 
                             data-cy="data-page-input"/>
                    <div class="num-pages" data-cy="data-num-pages">
                         &nbsp;/ {{num_pages}}
                    </div>
                    <q-btn @click="getTableData(page_num + 1)" :disable="page_num == num_pages" data-cy="data-next-btn">
                        {{'>'}}
                    </q-btn>
                </template>
            </q-table>
            <q-dialog v-model="add_ApprovalMatrix">
                <create-ApprovalMatrix-dialog
                    :ApprovalMatrixRow="{}"
                    :createMode="true"
                    @updateTable="getTableData(page_num)"/>
            </q-dialog >
            <q-dialog v-model="upd_ApprovalMatrix">
                <create-ApprovalMatrix-dialog
                    :ApprovalMatrixRow = "ApprovalMatrixRow"
                    :createMode="false"
                    @updateTable="getTableData(page_num)"/>
            </q-dialog >
        </div>
    </q-page>
</template>

<script>
import {
    retrieveData,
    deleteData,
} from '@/utils.js';

import { ref, onMounted, computed, defineProps, watch} from 'vue';
import { useStore } from 'vuex'
import CreateApprovalMatrixDialog from '@/views/approvalMatrix/CreateApprovalMatrix.vue'

export default {
    name: 'ApprovalMatrixPage',
    components: {
        CreateApprovalMatrixDialog,
    },
}
</script>

<script setup>

    const rows_per_page = 20

    const store = useStore()

    const rows = ref([])
    const selected = ref([])

    const add_ApprovalMatrix = ref(false);
    const filter_select = ref()
    const filter_val = ref()
    const filtered = ref(false)
    const filter_slug = ref('')
    const ApprovalMatrixRow = ref()
    const sort_slug = ref('')
    const upd_ApprovalMatrix = ref(false);

    const page_num = ref(1)
    const num_pages = ref()

    const isAuthenticated = ref(computed(() => store.getters.authenticated))
    const isSupervisor = ref(computed(() => store.getters.isSupervisor))

    const props = defineProps({
        rerender: Boolean,
    })

    onMounted(() => {
        getTableData(1)
    })

    watch(() => props.rerender, (newVal, oldVal) => {
        if (newVal === false){
            getTableData(page_num.value)
        }
    })

    async function getTableData(page_number) {
        add_ApprovalMatrix.value = false // Close Add ApprovalMatrix popup, if open
        upd_ApprovalMatrix.value = false // Close Update ApprovalMatrix popup, if open
        let data_url = `approvalmatrix/?_=_${pagination_slug(page_number)}`
        if (filter_slug.value){
            data_url = data_url + `${filter_slug.value}`
        }
        if (sort_slug.value){
            data_url = data_url + `${sort_slug.value}`
        }
        let data_rows = await retrieveData(data_url);
        rows.value = formatRows(data_rows['results'])

        set_pagination_params(page_number, data_rows.count)
        setSelected()
    }

    async function deleteSelected(apvlMtRow){
        if (!window.confirm(`Delete ApprovalMatrix: ${apvlMtRow['name']}?`)) {
            return
        }
        
        deleteData(`approvalmatrix/${apvlMtRow['name']}`, '{}', `Deleted ApprovalMatrix: ${apvlMtRow['name']} successfully.`).then((res) => {
            if (res.status < 300){
                clearSelected()
                getTableData(1)
            }
        })
    }

    async function clearSelected(){
        selected.value = []
    }

    async function updateSelected(row){
        ApprovalMatrixRow.value=row
        upd_ApprovalMatrix.value = true
    }

    function pagination_slug(page_number){
        return `&limit=${rows_per_page}&offset=${(page_number-1)*rows_per_page}`
    }

    function set_pagination_params(page_number, num_rows){
        if (num_pages.value){
            if (page_number > num_pages.value) {
                page_number = num_pages.value
            }
        }
        num_pages.value = Math.ceil(num_rows/rows_per_page)
        page_num.value = page_number
    }

    function formatRows(rows) {
        return rows
    }

    function getRowIdx(row_num, creation_tm){
        for (let i = 0; i < rows.value.length; i++){
            let row = rows.value[i]
            if ((row.row_num === row_num) && (row.creation_tm === creation_tm)){
                return i
            }
        }
        return null
    }

    // Data in selected rows is be overwritten when table is rerendered when data is modified
    // So when table is rerendered, the selected row data must be set in the table
    function setSelected(){
        for (const row of selected.value){
            let row_idx = getRowIdx(row.row_num, row.creation_tm)
            if (row_idx != null){
                rows.value[row_idx] = row
            }
        }
    }

    // Delete input box filter on advanced filter
    // Add documentation about basic vs. advanced filter
    async function applyFilter(filter_str){
        if (!filter_str){
            filtered.value = false;
            filter_slug.value = ""
            getTableData(1)
            return;
        }
        filter_slug.value = filter_str
        getTableData(1)
        filtered.value = true;
    }

    async function clearFilter(){
        filter_select.value = null;
        filter_val.value = null;
        filter_slug.value = null;
        getTableData(1)
    }

    async function clearFilters(){
        filtered.value = false;
        clearFilter()
    }
    
    const columns = [
            { name: 'name', align: 'center', label: 'Approval Matrix', field: 'name', classes: "tab page-col", headerStyle:"font-size:large;", style: 'width: 15em;', sortable: true},
            { name: 'doc_type', align: 'center', label: 'Doc Type', field: 'sub_cdoc_typeat', classes: "tab page-col", headerStyle:"font-size:large;", style: 'width: 15em;', sortable: true},
            { name: 'department', align: 'center', label: 'Department', field: 'department', classes: "tab page-col", headerStyle:"font-size:large;", style: 'width: 15em;', sortable: true},
            { name: 'jira_temp', align: 'center', label: 'Jira Template', field: 'jira_temp', classes: "tab page-col", headerStyle:"font-size:large;", style: 'width: 15em;', sortable: true},
            { name: 'signRoles', align: 'center', label: 'Required Signer Roles', field: 'signRoles', classes: "tab page-col", headerStyle:"font-size:large;", style: 'width: 15em;', sortable: true},
        ]
</script>

<style scoped>

.doc-btn {
    height: 4em;
    margin: 2vw;
}

.page-input {
    width:4em; 
    margin-left: 2vw;
    text-align: right;
}

.num-selected {
    margin-left: 1vw;
    font-size: 1.2em;
    margin-top: .7em;
    font-weight: bold;
}

.tool-row{
    margin-bottom: 2vh; 
    margin-top: 1vh
}

.spacer{
    width: 2vh
}

.col-row-width{
    min-width: 100%
}

.num-pages{
     margin-right: 1vw; 
     font-size: 1.15em;
}

 .page-title{
    font-size: 2em
 }

</style>