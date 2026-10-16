const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const goals=[{id:'mine',active_version_id:'v1'},{id:'team',active_version_id:'v2'},{id:'plan',active_version_id:null},{id:'foreign',active_version_id:null}];
const versions=[{id:'v1',goal_id:'mine',owner_id:'me',state:'submitted',approver_id:'boss',starts_on:'2026-10-01',cadence:'weekly'},{id:'v2',goal_id:'team',owner_id:'report',state:'submitted',approver_id:'me',starts_on:'2026-10-01',cadence:'weekly'},{id:'v3',goal_id:'plan',owner_id:'report',state:'submitted',approver_id:'me'},{id:'v4',goal_id:'foreign',owner_id:'report',state:'submitted',approver_id:'else'}].map(v=>({...v,title:v.goal_id}));
const ds=[{id:'own',version_id:'v1',owner_id:'me',title:'My delivery',due_on:'2026-11-01'},{id:'review',version_id:'v2',owner_id:'report',title:'Review delivery',due_on:'2026-11-02'},{id:'done',version_id:'v1',owner_id:'me',title:'Completed delivery'}];
const cps=[{id:'c1',deliverable_id:'own',reviewer_id:'boss',weight:100},{id:'c2',deliverable_id:'review',reviewer_id:'me',weight:100}];
const data={goals,versions,deliverables:ds,checkpoints:cps,evidence:[{id:'e1',deliverable_id:'review',checkpoint_id:'c2',upload_state:'complete'}],acceptances:[],approvals:[{version_id:'v1'},{version_id:'v2'}],delivery_progress:[{deliverable_id:'own',calculated_health:'in_progress',accepted_pct:0},{deliverable_id:'review',calculated_health:'awaiting_review',accepted_pct:0},{deliverable_id:'done',calculated_health:'complete',accepted_pct:100}],demo:{as_of:'2026-10-27'},checkins:[{goal_id:'mine',created_at:'2026-10-10',reason:'Old update'}],questions:[{id:'q',goal_id:'mine',assigned_to:'me'},{id:'q-other',goal_id:'team',assigned_to:'report'}],followups:[{id:'f',goal_id:'team',owner_id:'me',due_on:'2026-10-24'},{id:'f-other',goal_id:'mine',owner_id:'report'}],assigned_work:[{deliverable:{id:'assigned',owner_id:'me',title:'Assigned leaf'},assigned_by:'Boss',checkpoints:[],evidence:[],acceptances:[],progress:{calculated_health:'in_progress',accepted_pct:0}}]};
const state={home:'team',reviewAudience:'team',reviewScope:'foreign'};const ctx={data,leader:'me',ls:()=>state,goals:()=>goals,latest:id=>versions.find(v=>v.goal_id===id),gv:g=>versions.find(v=>v.goal_id===g.id),goalTitle:id=>id,name:id=>id,portfolioDate:s=>s,objectiveState:()=> 'on_track',status:g=>g.active_version_id?'approved':'submitted',supportRows:()=>[],act:()=>{},reviews:()=>{},console};vm.createContext(ctx);vm.runInContext(fs.readFileSync(__dirname+'/reviews_ui.js','utf8'),ctx);vm.runInContext(fs.readFileSync(__dirname+'/hygiene_actions.js','utf8'),ctx);
const queue=()=>ctx.hygieneActionQueue(),keys=()=>queue().map(r=>r.key);
assert(keys().includes('delivery-own'));assert(keys().includes('delivery-assigned'));assert(!keys().includes('delivery-done'));assert.equal(queue().filter(r=>r.kind==='evidence').length,1);assert.equal(queue().filter(r=>r.kind==='approval').length,1);assert.equal(queue().filter(r=>r.kind==='checkin').length,1);assert.equal(queue().find(r=>r.kind==='checkin').update.overdue,10);assert(keys().includes('question-q'));assert(keys().includes('followup-f'));assert(!keys().includes('question-q-other'));assert(!keys().includes('followup-f-other'));
// Parent/child roll-up duplicates do not create duplicate personal delivery actions.
data.assigned_work.push(ctx.actionDeliveryRecords().find(a=>a.deliverable.id==='own'));assert.equal(queue().filter(r=>r.key==='delivery-own').length,1);data.assigned_work.pop();
data.evidence.push({id:'own-evidence',deliverable_id:'own',upload_state:'complete'});assert.equal(queue().find(r=>r.key==='delivery-own').waiting,true);
cps.push({id:'c3',deliverable_id:'own',reviewer_id:'boss',weight:0});data.evidence.find(e=>e.id==='own-evidence').checkpoint_id='c1';assert.equal(queue().find(r=>r.key==='delivery-own').waiting,false,'One submitted checkpoint does not imply all work is awaiting review');
data.acceptances.push({checkpoint_id:'c2',deliverable_id:'review',evidence_id:'e1',accepted:false,decided_at:'2026-10-27'});assert(!keys().includes('evidence-c2'),'Returned evidence needs a new submission');data.evidence.push({id:'e2',deliverable_id:'review',upload_state:'complete'});assert(keys().includes('evidence-c2'));data.acceptances.push({checkpoint_id:'c2',deliverable_id:'review',evidence_id:'e2',accepted:true,decided_at:'2026-10-28'});assert(!keys().includes('evidence-c2'));
data.checkins.push({goal_id:'mine',created_at:'2026-10-27'});assert(!keys().includes('checkin-mine'),'Saved check-in removes the due action');data.approvals.push({version_id:'v3'});assert(!queue().some(r=>r.kind==='approval'));
console.log('PASS: current-user queue independent of tab filters, exact ownership, leaf deduplication, waiting vs actionable, pending/rejected/resubmitted/accepted evidence, approvals and check-in refresh.');
// Urgency is mutually exclusive: waiting never competes with overdue personal actions.
const cases=[{key:'future',due:'2026-11-10',rank:0,title:'Later'},{key:'soon',due:'2026-11-03',rank:4,title:'Soon'},{key:'today',due:'2026-10-27',rank:4,title:'Today'},{key:'late-review',due:'2026-10-25',rank:0,title:'Late review'},{key:'late-update',update:{overdue:10},rank:2,title:'Late update'},{key:'waiting',due:'2026-10-01',waiting:true,rank:8,title:'Waiting'},{key:'undated',rank:0,title:'Approval'},{key:'blocked',due:'2026-11-10',state:'blocked',rank:1,title:'Blocked'}];
const grouped=ctx.hygieneUrgencyGroups(cases);
assert.equal(grouped.map(g=>g.key).join(','),'overdue,today,attention,soon,later,waiting');
assert.equal(grouped[0].rows.map(r=>r.key).join(','),'late-update,late-review','Oldest overdue obligation first');
assert.equal(grouped.reduce((n,g)=>n+g.rows.length,0),cases.length,'No duplicates or missing actions');
assert.equal(ctx.hygieneUrgency({kind:'checkin',update:{overdue:null}}),'attention','Missing updates are not invented overdue');
vm.runInContext("hygieneActionRow=r=>'<article>'+r.key+'<button>Direct action</button></article>'",ctx);
let markup=ctx.hygieneUrgencyGroup(grouped[0]);
assert(markup.includes('Show all 2'));assert(markup.includes('Direct action'));assert(!markup.includes('<article>late-review'));
state.hygieneUrgencyExpanded={overdue:true};markup=ctx.hygieneUrgencyGroup(grouped[0]);
assert(markup.includes('Show less'));assert(markup.includes('<article>late-review'));assert(markup.includes('aria-expanded="true"'));
console.log('PASS: urgency precedence, overdue ordering, waiting exclusion, full counts and compact/expanded actions.');

assert.equal(ctx.hygieneUrgency({kind:'evidence',due:'2026-12-01'}),'attention','Submitted evidence needs a decision now, even with a future checkpoint date');

// Completeness checks are read-only and preserve outcome/delivery distinctions.
ctx.goalResourceIssues=()=>[];ctx.makeDraft=(g,v)=>({...v,measures:[],deliverables:[]});ctx.gaps=d=>d.success_basis==='delivery'?[]:['Define outcome measures.'];
vm.runInContext(fs.readFileSync(__dirname+'/hygiene_ui.js','utf8').split('function hygienePlanChecks')[0],ctx);
versions[0].state='draft';versions[0].ends_on=null;versions[0].success_basis='delivery';
let issues=ctx.hygienePlanIssues(goals[0]);assert(issues.includes('Set the start and end dates.'));assert(!issues.includes('Define outcome measures.'));
versions[0].success_basis='outcome';assert(ctx.hygienePlanIssues(goals[0]).includes('Define outcome measures.'));
goals[0].assignment_state='pending';assert(ctx.hygienePlanIssues(goals[0])[0].includes('Accept the assigned workstream'));
console.log('PASS: missing plan dates, delivery-based goals need no KPI, outcome measures, pending inheritance.');

data.questions.forEach(q=>q.question=q.id);
data.questions.push({question:'Outgoing question',id:'asked-by-me',goal_id:'mine',asked_by:'me',assigned_to:'report'});
assert(queue().find(r=>r.key==='question-asked-by-me').waiting,'Questions I asked stay visible while waiting for the assignee');
assert.equal(ctx.hygieneUrgency(queue().find(r=>r.key==='question-asked-by-me')),'waiting');
console.log('PASS: outgoing questions stay visible as waiting, not assigned work.');

goals[0].assignment_state='accepted';ctx.status=()=> 'returned';
assert(ctx.hygienePlanIssues(goals[0])[0].includes('approver'), 'Return decision is read from approval status even when stored version state is submitted');
console.log('PASS: returned plans stay in the checklist until revised.');

// A revision awaiting approval remains visible to its owner without granting approval.
versions.push({id:'proposal',goal_id:'mine',owner_id:'me',approver_id:'boss',state:'submitted',version_no:2,title:'Proposed revision'});
ctx.latest=id=>versions.filter(v=>v.goal_id===id).at(-1);
let waitingApproval=queue().find(r=>r.key==='waiting-approval-proposal');assert(waitingApproval?.waiting);assert.equal(waitingApproval.path,'plans/mine/setup');assert.equal(ctx.hygieneUrgency(waitingApproval),'waiting');
data.approvals.push({version_id:'proposal',decision:'returned'});assert(!queue().some(r=>r.key==='waiting-approval-proposal'));
console.log('PASS: own submitted revisions remain inspectable as waiting and clear after a decision.');
