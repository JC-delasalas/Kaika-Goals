// Session-local recovery. No credentials, roster exports or file bytes are stored.
function recoveryRead(key){try{return JSON.parse(sessionStorage.getItem(key)||'null')}catch{return null}}
function recoveryWrite(key,value){try{value==null?sessionStorage.removeItem(key):sessionStorage.setItem(key,JSON.stringify(value));return true}catch{return false}}
function recoveryKey(){return 'kaika-recovery-v1:'+String(data?.persistence?.workspace_id||mode)+':'+leader}
const recoveryMemory=new Map();
let recoveryFormInFlight='';
function recoveryState(){const k=recoveryKey();if(!recoveryMemory.has(k))recoveryMemory.set(k,recoveryRead(k)||{drafts:{},forms:{},undo:{},pending:null,failure:null});return recoveryMemory.get(k)}
function recoveryPersist(){const ok=recoveryWrite(recoveryKey(),recoveryState());if(!ok&&typeof toast==='function')toast('Browser recovery storage is unavailable. Keep this tab open until your save is confirmed.');}
function recoverySignature(action,payload){return JSON.stringify({action,leader_id:leader,data:payload})}
function recoveryError(message,status=0){return Object.assign(new Error(message),{status})}
function recoveryPrepare(action,input){
 const state=recoveryState(),payload=structuredClone(input||{});
 const guarded=['save_draft','submit','approve','new_version'];
 if(guarded.includes(action)&&payload.goal_id&&!payload.expected_version_id)payload.expected_version_id=latest(payload.goal_id)?.id;
 if(action==='submit'&&payload.edit_revision==null)payload.edit_revision=latest(payload.goal_id)?.edit_revision;
 const signature=recoverySignature(action,payload);
 if(state.pending){if(state.pending.signature!==signature)throw recoveryError('An earlier save is still unconfirmed. Use Retry unconfirmed save before sending another change.',425);return state.pending}
 const g=data?.goals.find(g=>g.id===payload.goal_id),v=g&&latest(g.id);
 state.pending={action,payload,signature,id:crypto.randomUUID(),route:location.hash,step:typeof step==='number'?step:0,formKey:typeof recoveryCurrentFormKey==='function'?recoveryCurrentFormKey():'',before:action==='save_draft'&&g&&v?makeDraft(g,v):null};
 state.failure=null;recoveryPersist();return state.pending;
}
function recoveryFailed(op,error){const s=recoveryState();if(error.status===425)return;
 s.failure={action:op.action,payload:op.payload,before:op.before,message:errorText(error),status:error.status||0,route:op.route};
 // A server rejection confirms no commit; network/5xx results remain uncertain.
 if(error.status>=400&&error.status<500)s.pending=null;
 recoveryPersist();
}
function recoveryConfirmed(op,result){const s=recoveryState();s.pending=null;s.failure=null;
 if(op.formKey)delete s.forms[op.formKey];
 if(op.action==='save_draft'){
  const v=result._state?.versions.filter(v=>v.goal_id===op.payload.goal_id).sort((a,b)=>b.version_no-a.version_no)[0]||(op.payload.expected_version_id&&Number.isInteger(op.payload.edit_revision)?{id:op.payload.expected_version_id,edit_revision:op.payload.edit_revision+1}:null);
  if(op.payload.undo_of_revision!=null)delete s.undo[op.payload.goal_id];
  else if(op.before&&v)s.undo[op.payload.goal_id]={before:op.before,version:v.id,revision:v.edit_revision};
  delete s.drafts[op.payload.goal_id];
 }
 if(op.action==='submit')delete s.drafts[op.payload.goal_id];
 recoveryPersist();
}
