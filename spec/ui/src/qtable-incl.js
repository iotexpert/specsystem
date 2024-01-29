/*
  Utilities to support q-table load/filter/sort/paginate
 */
import { apiServerHost, retrieveData } from "@/utils.js";
import { nextTick } from "vue";

export async function qtOnRequest(props, loading, filter, rows, pagination, url, row_key) {
  const { page, rowsPerPage, sortBy, descending } = props.pagination;

  loading.value = true;
  let filter_s = filter_slug(filter);

  let page_slug = `&limit=${rowsPerPage}&offset=${(page - 1) * rowsPerPage}${sortBy !== null ? ('&orderBy=' + (descending ? '-' : '') + sortBy) : ''}`;
  let data_url = `${url}?_=_${page_slug}`;
  if (filter_s) {
    data_url = data_url + `${filter_s}`;
  }

  let data_rows = await retrieveData(data_url);
  rows.value = data_rows["results"];
  if (row_key) {rows.value = rows.value.map(r => {r['key']= r[row_key]; return r})}

  // update local pagination object
  pagination.value.page = page;
  pagination.value.rowsNumber = data_rows.count;
  pagination.value.rowsPerPage = rowsPerPage;
  pagination.value.sortBy = sortBy;
  pagination.value.descending = descending;

  // ...and turn off loading indicator
  loading.value = false;
}

// Function that Handles the Shift-Click multi-row selection
export async function qtHandleSelection({ rows, added, evt }, storedSelectedRow, tableRef, selected) {
  // ignore selection change from header of not from a direct click event
  if (rows.length !== 1 || evt === void 0) {
    return;
  }

  const oldSelectedRow = storedSelectedRow.value;
  const [newSelectedRow] = rows;
  const { shiftKey } = evt;

  if (shiftKey !== true) {
    storedSelectedRow.value = newSelectedRow;
  }

  // wait for the default selection to be performed
  nextTick(() => {
    if (shiftKey === true) {
      const tableRows = tableRef.value.filteredSortedRows;
      let firstIndex = tableRows.indexOf(oldSelectedRow);
      let lastIndex = tableRows.indexOf(newSelectedRow);

      if (firstIndex < 0) {
        firstIndex = 0;
      }

      if (firstIndex > lastIndex) {
        [firstIndex, lastIndex] = [lastIndex, firstIndex];
      }

      const rangeRows = tableRows.slice(firstIndex, lastIndex + 1);
      // we need the original row object so we can match them against the rows in range
      const selectedRows = selected.value;

      selected.value =
        added === true
          ? selectedRows.concat(
            rangeRows.filter((row) => selectedRows.includes(row) === false)
          )
          : selectedRows.filter((row) => rangeRows.includes(row) === false);
    }
  });
}

// Utility function for building request with filtering
export function qtCsvLink(filter, pagination, url) {
  return apiServerHost + '/' + url + '?output_csv=true' +
    (pagination.value.sortBy !== null ? ('&orderBy=' + (pagination.value.descending ? '-' : '') +
      pagination.value.sortBy) : '') +
      ( filter_slug(filter) !== null ? (filter_slug(filter)) : '')
}

export function filter_slug(filter) {
  let ret = "";
  Object.entries(filter.value).forEach((entry) => {
    const [key, value] = entry;
    if (value.length > 0) {
      ret += "&" + key + "=" + value;
    }
  });
  return ret;
}

// Human display of current filter value
export function qtFilterValue(filter, columns) {
  let vals = [];
  if (!filter || !filter.value || !columns) {return;}

  Object.entries(filter.value).forEach((entry) => {
    const [key, value] = entry;
    const cols = columns.filter(function (el) {
      return el.field === key;
    });
    if (value.length > 0) {
      vals.push(cols[0].label + ": " + value);
    }
  });

  if (vals.length === 0) { return ''; }
  return 'Current Filter: ' + vals.join(", ");
}