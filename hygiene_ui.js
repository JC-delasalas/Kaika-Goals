// Hygiene is the leader's action surface. It does not inherit Summary filters.
const hygieneTabs=[['actions','My actions'],['checks','Plan checks'],['history','Decisions & history']];
function hygieneState(){return ls().hygiene||(ls().hygiene={tab:'actions',scope:'mine'})}
function hygienePlanIssues(g){
 const v=latest(g.id),d=makeDraft(g,v),issues=gaps(d);
 if(!v.title?.trim())issues.push('Give the goal a title.');
 if(!v.starts_on||!v.ends_on)issues.push('Set the start and end dates.');
 else if(v.starts_on>v.ends_on)issues.push('End date must follow the start date.');
 if(!v.owner_id)issues.push('Assign an accountable owner.');
 if(!v.approver_id)issues.push('Assign a plan approver.');
 if(!v.category)issues.push('Choose a category.');
 if(!v.cadence)issues.push('Choose an update frequency.');
 for(const m of d.measures){if(!m.title||!m.unit||!m.source)issues.push('Complete the measure name, unit and data source.');if(m.baseline==null||m.target==null||Number(m.baseline)===Number(m.target))issues.push('Set distinct baseline and target values for each measure.');}
 for(const x of d.deliverables){if(!x.owner_id||!x.due_on)issues.push('Assign a deliverable owner and due date.');for(const c of x.checkpoints){if(!c.acceptance_criteria?.trim()||!c.reviewer_id||!c.due_on)issues.push('Complete checkpoint criteria, reviewer and due date.');}}
 if(g.assignment_state==='pending')issues.unshift('Accept the assigned workstream before completing the plan.');
 else if(status(g)==='returned')issues.unshift('Address the approver’s feedback and resubmit this version.');
 else if(status(g)==='draft'&&!issues.length)issues.push('Submit this draft to establish an approved baseline.');
 return [...new Set(issues)];
}
function hygienePlanChecks(){const h=hygieneState(),gs=goals().filter(g=>h.scope==='team'||latest(g.id).owner_id===leader),rows=gs.map(g=>({g,issues:hygienePlanIssues(g),update:reviewUpdateInfo(g)})).filter(r=>r.issues.length||r.update.due);
 return '<form id="hygiene-check-scope" class="hygiene-check-form">'+selectUI('Check scope','scope',[['mine','My goals'],['team','My reporting team']],h.scope)+'<button class="btn">Apply scope</button></form><p class="hygiene-context">'+rows.length+' of '+gs.length+' visible goals need attention. Checks use saved fields and update cadence. Passing these checks does not approve a plan.</p>'+ (rows.length?rows.map(({g,issues,update})=>{const v=latest(g.id),own=v.owner_id===leader,request=(data.followups||[]).find(f=>f.goal_id===g.id&&f.owner_id===v.owner_id&&!f.completed_at&&f.text.startsWith('Hygiene: '));return '<details class="hygiene-check"><summary><span><b>'+esc(v.title)+'</b><small>'+esc(name(v.owner_id))+' · '+(update.due?esc(update.label)+' · ':'')+esc(status(g))+'</small></span><span class="count-tag">'+(issues.length+(update.due?1:0))+((issues.length+(update.due?1:0))===1?' check':' checks')+'</span></summary><ul>'+issues.map(s=>'<li>'+esc(s)+'</li>').join('')+(update.due?'<li>Record the '+esc(gv(g).cadence)+' check-in. '+esc(update.label)+'.</li>':'')+'</ul><div class="tools">'+(own?(g.assignment_state==='pending'?btn('Accept workstream','accept-inherited',g.id):link('Open goal setup','plans/'+g.id+'/setup')):link('Inspect plan','plans/'+g.id+'/setup'))+(own&&update.due?btn('Check in','checkin',g.id):'')+(!own?(request?'<span class="scope-note">Request already open · due '+portfolioDate(request.due_on)+'</span>':btn('Request an update','hygiene-request',g.id)):'')+'</div></details>'}).join(''):'<p class="empty">No missing setup details or overdue updates found in this scope.</p>');
}
function hygieneDecisionHistory(){
 const approvalRows=data.approvals.filter(a=>a.approver_id===leader).map(a=>{const v=data.versions.find(v=>v.id===a.version_id);return reviewDisclosure(v?.title||'Plan approval','Version '+(v?.version_no||'')+' · '+(a.decided_at?portfolioDate(a.decided_at):'Decision date not recorded'),badge(a.decision),'<p>'+esc(a.reason)+'</p>'+(v?link('Inspect plan','plans/'+v.goal_id+'/setup'):''))});
 const acceptanceRows=data.acceptances.filter(a=>a.reviewer_id===leader).sort((a,b)=>(b.decided_at||'').localeCompare(a.decided_at||'')).map(a=>{const d=data.deliverables.find(d=>d.id===a.deliverable_id),c=data.checkpoints.find(c=>c.id===a.checkpoint_id);return reviewDisclosure(d?.title||'Checkpoint review',(c?.title||'Checkpoint')+' · '+portfolioDate(a.decided_at),badge(a.accepted?'complete':'returned'),'<p>'+esc(a.reason)+'</p>')});
 return '<details><summary>Approval & evidence decisions</summary>'+approvalRows.concat(acceptanceRows).join('')+(!approvalRows.length&&!acceptanceRows.length?'<p>No decisions recorded by you.</p>':'')+'</details>';
}
function hygieneHistory(){
 const q=reviewQueue(),mine=id=>goals().some(g=>g.id===id&&gv(g).owner_id===leader),questions=data.questions.filter(q=>q.resolved_at&&(q.assigned_to===leader||q.asked_by===leader)),followups=(data.followups||[]).filter(f=>f.completed_at&&(f.owner_id===leader||f.created_by===leader));
 return '<div class="hygiene-history"><div class="tools">'+btn('Record decision','new-decision')+btn('Prepare review','hygiene-session')+'</div>'+reviewGroup('Decision log',q.decisions.map(reviewDecisionRow),'No decisions recorded for you or your owned goals.','hygiene-decisions',5)+hygieneDecisionHistory()+'<details><summary>Recorded check-ins</summary>'+reviewGroup('Your updates',data.checkins.filter(c=>c.author_id===leader||mine(c.goal_id)).sort((a,b)=>b.created_at.localeCompare(a.created_at)).map(c=>reviewDisclosure(goalTitle(c.goal_id),portfolioDate(c.created_at),badge(c.health),'<p>'+esc(c.reason)+'</p><p>ETA '+portfolioDate(c.eta)+'</p>')),'No recorded updates.','hygiene-updates',5)+'</details><details><summary>Resolved questions & completed actions</summary>'+questions.map(reviewQuestionRow).join('')+followups.map(f=>reviewDisclosure(f.text,goalTitle(f.goal_id),badge('complete'),'<p>Completed '+portfolioDate(f.completed_at)+'</p>')).join('')+(!questions.length&&!followups.length?'<p>No resolved questions or completed actions involving you.</p>':'')+'</details><details><summary>Saved review snapshots</summary>'+data.reviews.filter(r=>r.facilitator_id===leader&&r.published_at).map(snapshotView).join('')+(!data.reviews.some(r=>r.facilitator_id===leader&&r.published_at)?'<p>No saved reviews. Save a Summary snapshot or prepare a review.</p>':'')+'</details></div>';
}
function hygieneSession(){
 // Reuse the existing review editor and persistence, without the old page navigation.
 const holder=document.createElement('div');holder.innerHTML=reviewsBeforeCompact();
 holder.querySelector('.pagehead')?.remove();holder.querySelector('.work-tabs')?.remove();const note=holder.querySelector('#review-scope-form p');if(note)note.textContent='This scope applies to the review draft. My actions always shows your assigned responsibilities.';
 return '<div class="tools">'+btn('Back to history','hygiene-tab','history')+'</div>'+holder.innerHTML;
}
function hygiene(){const h=hygieneState();ls().reviewAudience='me';if(h.tab!=='session')ls().reviewScope='all';
 const body=h.tab==='checks'?hygienePlanChecks():h.tab==='history'?hygieneHistory():h.tab==='session'?hygieneSession():hygieneActionHub();
 return '<div class="hygiene-workspace">'+heading('Hygiene',name(leader)+' · Keep commitments current, resolve questions and make the decisions waiting on you.',h.tab==='actions'&&goals().length?btn('Ask a question','new-question')+btn('Assign action','new-followup'):'')+subTabs(hygieneTabs,h.tab==='session'?'history':h.tab,'hygiene-tab')+body+'</div>';
}
const hygienePreviousAct=act;act=async function(action,id){
 if(action==='hygiene-tab'){hygieneState().tab=id;render();return}
 if(action==='hygiene-session'){hygieneState().tab='session';ls().review='session';render();return}
 if(action==='hygiene-request'){const g=goals().find(g=>g.id===id);if(!g||latest(id).owner_id===leader)return;const v=latest(id);if((data.followups||[]).some(f=>f.goal_id===id&&f.owner_id===v.owner_id&&!f.completed_at&&f.text.startsWith('Hygiene: ')))return toast('There is already an open update request.');openDialog('Request a plan update',modalForm('create_followup','<input type="hidden" name="goal_id" value="'+esc(id)+'"><input type="hidden" name="owner_id" value="'+esc(v.owner_id)+'"><p>Assigned to '+esc(name(v.owner_id))+'</p>'+plainField('Request','text','Hygiene: Please review missing setup details and update '+v.title+'.','textarea')+plainField('Due date','due_on',data.demo.as_of,'date')+'<p class="scope-note">Creates a saved action in the owner’s Hygiene queue. No email or external notification is sent.</p>','Create update request'));return}
 if(action==='question-detail'&&route()==='hygiene'){const q=data.questions.find(q=>q.id===id&&(q.assigned_to===leader||q.asked_by===leader));if(q)openDialog('Question discussion',questionPanel(q));return}
 return hygienePreviousAct(action,id);
};
document.addEventListener('submit',e=>{if(e.target.id!=='hygiene-check-scope')return;e.preventDefault();hygieneState().scope=new FormData(e.target).get('scope');render()});
// Preserve old Reviews deep links while making Hygiene the only action destination.
function hygieneDeepLink(){if(route()!=='hygiene')return;const sub=parts()[1];if(!sub)return;const h=hygieneState();h.tab=['decisions','published','session'].includes(sub)?(sub==='session'?'session':'history'):'actions';if(sub==='session')ls().review='session';if(['questions','checkins','support'].includes(sub))ls().hygieneActionFilter={questions:'question',checkins:'checkin',support:'other'}[sub];}
window.addEventListener('hashchange',()=>{hygieneDeepLink();if(route()==='hygiene')render()});
hygieneDeepLink();
