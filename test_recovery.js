const vm=require('vm'),fs=require('fs'),assert=require('node:assert/strict');
const storage=new Map();
function context(){const c={structuredClone,crypto:require('crypto').webcrypto,sessionStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},data:{persistence:{workspace_id:'w'},goals:[{id:'g'}]},leader:'owner',mode:'connected',location:{hash:'#/plans/g/setup'},step:1,latest:()=>({id:'v1',edit_revision:3}),makeDraft:()=>({goal_id:'g',description:'Before',edit_revision:3}),errorText:e=>e.message};vm.createContext(c);vm.runInContext(fs.readFileSync('recovery_store.js','utf8'),c);return c}
let c=context();const op=c.recoveryPrepare('save_draft',{goal_id:'g',description:'Mine',edit_revision:3});
c.recoveryFailed(op,c.recoveryError('Lost confirmation',503));assert.equal(c.recoveryState().pending.id,op.id);
assert.throws(()=>c.recoveryPrepare('checkin',{goal_id:'g',reason:'new'}),e=>e.status===425);
c=context();assert.equal(c.recoveryPrepare('save_draft',op.payload).id,op.id,'reload reuses operation ID');
c.leader='other';assert.equal(c.recoveryState().pending,null,'leader cannot see another recovery');c.leader='owner';
c.recoveryFailed(op,c.recoveryError('Concurrent draft',409));assert.equal(c.recoveryState().pending,null);assert.equal(c.recoveryState().failure.payload.description,'Mine');
const again=c.recoveryPrepare('save_draft',{...op.payload,edit_revision:4});assert.notEqual(again.id,op.id);
c.recoveryConfirmed(again,{_state:{versions:[{id:'v1',goal_id:'g',version_no:1,edit_revision:5}]}});
assert.equal(c.recoveryState().pending,null);assert.equal(c.recoveryState().undo.g.revision,5);assert.equal(c.recoveryState().undo.g.before.description,'Before');
const undo=c.recoveryPrepare('save_draft',{goal_id:'g',description:'Before',edit_revision:5,undo_of_revision:5});c.recoveryConfirmed(undo,{});assert.equal(c.recoveryState().undo.g,undefined);
const fixtureSave=c.recoveryPrepare('save_draft',{goal_id:'g',edit_revision:8});c.recoveryConfirmed(fixtureSave,{});assert.equal(c.recoveryState().undo.g.revision,9);
console.log('PASS: uncertain retries retain IDs across reload; actor isolation; conflicting writes blocked; definitive conflicts retain inputs; saved undo binds revision and clears after success.');
Object.assign(c,{setupForm:()=>'',goalPage:()=>'',render:()=>{},openDialog:()=>{},act:async()=>{},demoRender:()=>{},document:{addEventListener:()=>{}},draft:null,draftGoal:'',esc:x=>String(x??'').replaceAll('<','&lt;'),table:(_h,rows)=>JSON.stringify(rows),btn:t=>t});
vm.runInContext(fs.readFileSync('recovery_ui.js','utf8'),c);
(async()=>{
 c.latest=()=>({id:'v1',goal_id:'g',version_no:1,edit_revision:7,state:'draft',owner_id:'owner'});
 c.request=async()=>c.data;let html='';c.openDialog=(_t,body)=>html=body;
 c.recoveryState().failure={action:'save_draft',payload:{goal_id:'g',expected_version_id:'v1',description:'Mine',undo_of_revision:5}};
 await c.recoveryReviewConflict();assert.doesNotMatch(html,/Keep my entries for review/,'stale Undo cannot be rebased into an overwrite');
 delete c.recoveryState().failure.payload.undo_of_revision;await c.recoveryReviewConflict();assert.match(html,/Keep my entries for review/);
 c.latest=()=>({id:'v2',goal_id:'g',version_no:2,edit_revision:0,state:'draft',owner_id:'owner'});await c.recoveryReviewConflict();assert.doesNotMatch(html,/Keep my entries for review/,'older goal versions cannot overwrite a new draft');
 console.log('PASS: conflict UI permits explicit same-version draft comparison, but never rebases stale Undo or a different goal version.');
})().catch(e=>{console.error(e);process.exitCode=1});
