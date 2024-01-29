
import { Notify } from 'quasar'

export const apiServerHost = process.env.NODE_ENV === 'production' ? '' : 'http://127.0.0.1:8000';
export const metadata_cols = ['row_num', 'creation_tm', '_new_row']
export const data_types = ['string', 'number', 'datetm', 'date']

export async function retrieveData(api) {
    let method = 'GET'
    let url = `${apiServerHost}/${api}`
    let res = await getHeader().then((header) => sendRequest(url, header, null, method))
    return notifyResponse(res)
}

export function isEmptyDict(dict){
  return Object.keys(dict).length === 0
}

export function removeFromList(elem, list){
  let del_idx = list.indexOf(elem)
  list.value.splice(del_idx, 1)
  return list
}

export async function postData(api, body, msg) {
  let method = 'POST'
  let url = `${apiServerHost}/${api}`
  let res = await getHeader().then((header) => sendRequest(url, header, JSON.stringify(body), method))
  return notifyResponse(res, msg)
}

export async function deleteData(api, body, msg) {
  let method = 'DELETE'
  let url = `${apiServerHost}/${api}`
  let res = await getHeader().then((header) => sendRequest(url, header, JSON.stringify(body), method))
  return notifyResponse(res, msg)
}

export async function putData(api, body, msg) {
  let method = 'PUT'
  let url = `${apiServerHost}/${api}`
  let res = await getHeader().then((header) => sendRequest(url, header, JSON.stringify(body), method))
  return notifyResponse(res, msg)
}

async function sendRequest(url, header, body, method) {
    let res = await window.fetch(url, {
        method: method,
        headers: header,
        credentials: 'include',
        body: body
      })
    return res
}

export function genCy(prefix, suffix){
  return prefix + '-' + suffix
}

async function getHeader(){
  let tok = getCookie('csrftoken')
  return {
          'Content-Type': 'application/json',
          'X-CSRFToken': tok,
        }
}

// Don't include content type in the header for form type request payloads
export async function getFormHeader(){
  let tok = getCookie('csrftoken')
  return {
          'X-CSRFToken': tok,
        }
  }

  // put this in uploadcsv
export async function postFormData(api, body, msg) {
  let method = 'POST'
  let url = `${apiServerHost}/${api}`
  let res = await getFormHeader().then((header) => sendRequest(url, header, body, method))
  return notifyResponse(res, msg)
}

export async function notifyResponse(response, msg) {
  let resp_body = {}
  try {
    resp_body = await response?.json()
  }
  catch (err) {
    resp_body = {}
  }
  if (typeof resp_body === 'object') {
    resp_body.__resp_status = response.status
  }

  if (response.status < 300) {
    if (msg) {
      showNotif(msg, 'green')
    }
  }
  else {
      showNotif(errorMsgHandler(resp_body), 'red')
  }
  return resp_body
}

export function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
          }
      }
  }
  return cookieValue;
}


export function errorMsgHandler(obj) {
  if (typeof obj === 'object') {
    if ('detail' in obj) {
      return obj['detail'];
    } else if ('schemaErrors' in obj) {
      let str = Object.keys(obj['schemaErrors']).map(e => {
        let err = obj['schemaErrors'][e];
        if ((err instanceof Array) & (err.length > 1)) {
          err = err.map(x => {
            let keys = Object.keys(x);
            let allErrs = keys.map(k => `${k}: ${x[k]}`);
            return allErrs
          });
          err = err.join(' | ');
        }

        let msg = `${e}: ${err}`;
        return msg
      });
      return `${obj['errorCode']}: ${str.join('   AND   ')}`;
    } else {
      return `${obj['errorCode']}: ${obj['error']}`;
    }
  } else {
    return obj;
  }
}

export function data_page_link(data_page){
    return `${apiServerHost}/data/?doc_type=${data_page}`
}

export function showNotif (msg, color) {
    Notify.create({
    message: msg,
    icon: 'announcement',
    color: color,
    actions: [
        { label: 'Dismiss', color: 'white', handler: () => { /* ... */ } }
      ]
    })
}

export function notifyLoginFail (msg) {
  Notify.create({
  message: msg,
  position:'top',
  icon: 'announcement',
  color: 'red',
  actions: [
      { label: 'Dismiss', color: 'white', handler: () => { /* ... */ } }
    ]
  })
}

const zeroPad = (num, places) => String(num).padStart(places, '0')
export function dispDate(date) {
  if (!date)
    return null;

  var d = new Date(date);
  var year = d.getFullYear();
  var month = zeroPad(d.getMonth() + 1, 2);
  var day = zeroPad(d.getDate(),2);
  var hour = zeroPad(d.getHours(), 2);
  var min = zeroPad(d.getMinutes(), 2);
  var sec = zeroPad(d.getSeconds(), 2);
  var tm = d.toLocaleTimeString('en-us',{timeZoneName:'short'}).split(' ')[2];

  return `${year}-${month}-${day} ${hour}:${min}:${sec} ${tm}`;
}