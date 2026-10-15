function deliveryRollup(g){
 const p=data.progress.find(p=>p.root_id===g.id);
 return panel('Objective roll-up','<div class="tools">'+badge(objectiveState(g))+'<span>Accepted delivery</span>'+progress(p?.delivery_pct)+'</div><p>'+esc(p?.reason||'Recalculated after a status update or checkpoint decision.')+'</p><small>Effort-weighted accepted checkpoints. Uploading evidence does not earn completion credit.</small><div class="outcome-brief"><b>'+(goalBasis(g)==='delivery'?'Success basis':'Measured outcome')+'</b> '+outcomeSummary(g)+'</div>');
}
function demoDeliveryControls(d,g,v){
 if(!['fixture','supabase-demo'].includes(mode)||g.active_version_id!==v.id)return'';
 return '<div class="demo-delivery-tools"><b>Editable demo</b><div class="tools">'+btn('Update delivery status','delivery-status',d.id)+(leader===d.owner_id||leader===v.owner_id?btn('Write evidence','evidence-note',d.id):btn('Work as '+name(d.owner_id),'delivery-owner',d.id))+'</div><small>Set operational status directly. Awaiting review follows submitted evidence; Complete requires all checkpoints to be accepted.</small>'+ (d.status_reason?'<p>'+esc(d.status_reason)+'</p>':'')+'</div>';
}
async function changeDemoPersona(workerId,goalId,deliverableId){
 if(!['fixture','supabase-demo'].includes(mode))throw Error('Persona shortcuts are for synthetic demos only.');
 if(!leaders.some(p=>p.id===workerId))throw Error('This owner is not available in the preview switcher.');
 leader=workerId;if($('leader-search'))$('leader-search').value='';renderLeaderOptions();$('leader').value=leader;sessionStorage.setItem('kaika-preview-leader',leader);epoch++;data=null;draft=null;dirty=false;draftGoal='';pendingCommand=null;$('dialog').close();
 location.hash='/overview';await refresh();location.hash=deliverableId&&assignedItem(deliverableId)?'/assigned/'+deliverableId:'/plans/'+goalId+'/delivery';
}
async function deliveryAction(action,id){
 const assignment=assignedItem(id),d=data.deliverables.find(d=>d.id===id)||assignment?.deliverable;
 if(action==='review-as'){
  const c=data.checkpoints.find(c=>c.id===id),delivery=data.deliverables.find(d=>d.id===c.deliverable_id),v=data.versions.find(v=>v.id===delivery.version_id);
  await changeDemoPersona(c.reviewer_id,v.goal_id);return;
 }
 if(!d)throw Error('Deliverable unavailable. Refresh the workspace.');
 const v=data.versions.find(v=>v.id===d.version_id);
 if(action==='delivery-owner'){await changeDemoPersona(d.owner_id,v.goal_id,d.id);return}
 if(action==='delivery-status'){
  openDialog('Update deliverable status',modalForm('demo_delivery_status','<input type="hidden" name="deliverable_id" value="'+d.id+'"><p>'+esc(d.title)+'</p><label class="formfield">Operational status<select name="status">'+[['not_started','Not started'],['in_progress','In progress'],['at_risk','At risk'],['blocked','Blocked'],['unknown','Unknown']].map(([k,t])=>'<option value="'+k+'" '+(d.demo_signal===k?'selected':'')+'>'+t+'</option>').join('')+'</select></label>'+plainField('Reason for this status','reason',d.status_reason||'','textarea')+'<p>Changing operational status does not change accepted progress. Completion requires evidence and checkpoint approval.</p>','Save delivery status'));return;
 }
 openDialog('Submit written evidence',modalForm('demo_evidence_note','<input type="hidden" name="deliverable_id" value="'+d.id+'"><p>'+esc(d.title)+'</p><label class="formfield">Evidence for<select name="checkpoint_id"><option value="">Whole deliverable</option>'+(assignment?.checkpoints||data.checkpoints.filter(c=>c.deliverable_id===d.id)).map(c=>'<option value="'+c.id+'">'+esc(c.title)+'</option>').join('')+'</select></label>'+plainField('Evidence and result','text','','textarea','Describe the checks performed, results, and how they meet the acceptance criteria.')+'<p>Saved as a downloadable evidence file. Connected workshop files are stored in the private Supabase bucket. The designated reviewer must accept it before progress increases.</p>','Submit evidence'));
}
function objectiveState(g){return data.progress.find(p=>p.root_id===g.id)?.objective_state||(health(g)==='complete'?'delivery_complete':health(g))}
function outcomeSummary(g){
 if(goalBasis(g)==='delivery')return '<b>Delivery-based</b><small>All agreed deliverables must be accepted. KPI attainment does not apply.</small>'+link('View completion rules','plans/'+g.id+'/updates');
 const o=data.outcomes.find(o=>o.goal_id===g.id);
 if(!o?.details)return progress(o?.outcome_pct,'Outcome attainment');
 const state=o.measurement_state, label={not_measured:'Not measured',stale:'Reading overdue',invalid:'Measurement setup incomplete',target_met:'Target met',no_improvement:'No improvement from baseline',below_baseline:'Below baseline',improving:'Measured improvement'}[state];
 return (o.outcome_pct==null?'<b>'+esc(label)+'</b>':progress(o.outcome_pct,'Measured improvement toward target')+'<small>'+esc(label)+'</small>')+'<small>'+o.details.map(d=>esc(d.title)+': '+(d.value==null?'no observation':esc(d.value+d.unit))+' · baseline '+d.baseline+d.unit+' → target '+d.target+d.unit+(d.observed_at?' · '+d.observed_at.slice(0,10):'')).join('<br>')+'</small>'+link('View measurement & calculation','plans/'+g.id+'/updates');
}
function measurementExplanation(g){
 const o=data.outcomes.find(o=>o.goal_id===g.id);
 if(!o?.details)return '';
 const p=data.progress.find(p=>p.root_id===g.id);
 return panel('How this Objective is measured','<p>'+badge(objectiveState(g))+'</p><p><b>Accepted delivery:</b> sum of (approved deliverable effort × accepted checkpoint share), divided by total approved effort. Evidence submission alone earns no credit.</p><p><b>Outcome attainment:</b> (latest reading − baseline) ÷ (target − baseline) × 100, for both increasing and decreasing targets. Each measure is capped at 0–100% before applying its approved weight. No reading means unknown, not zero.</p><p>Example: 12/20 datasets passed at baseline (60%). At 17/20 (85%), improvement is (85 − 60) ÷ (95 − 60) = <b>71.4%</b>. At 19/20 (95%), the target is met. The 20 datasets must stay the same.</p><p>Delivery and outcome are separate; they are never averaged. Objective achievement requires accepted delivery and current readings meeting every weighted target. Outcome readings are owner-reported with a source note; this demo does not independently verify the source.</p>'+(p?.delivery_pct===100&&!o.target_met?'<div class="notice">Delivery is complete. '+(o.outcome_pct==null?'Record a post-delivery observation before judging impact.':o.measurement_state==='stale'?'Refresh the overdue observation before claiming success.':'The measured target is not met. Review adoption, remaining quality issues and any follow-up work.')+'</div>':'')+'<p>'+outcomeSummary(g)+'</p>');
}
