// Shared presentation only. Progress, authorization and approvals remain server-owned.
function avatarDefaultStyle(id){return [...String(id||'unassigned')].reduce((n,c)=>(n*31+c.charCodeAt(0))>>>0,0)%6}
function defaultAvatarImage(id,style=null){
 const palettes=[['#dcece5','#2f7562'],['#e4eafa','#4969a4'],['#f6e8d6','#9a7042'],['#eee4f1','#876395'],['#dcedef','#3f7c86'],['#f2e2df','#a2665b']];
 const hash=[...String(id||'unassigned')].reduce((n,c)=>(n*31+c.charCodeAt(0))>>>0,0),[bg,shirt]=palettes[Number.isInteger(style)&&style>=0&&style<6?style:hash%palettes.length];
 // A generic illustration, not a likeness or an inferred personal characteristic.
 const svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="32" fill="'+bg+'"/><path d="M8 65v-9c0-12 10-19 24-19s24 7 24 19v9" fill="'+shirt+'"/><path d="M25 35h14v12c-4 5-10 5-14 0" fill="#dfc6a6"/><ellipse cx="32" cy="27" rx="15" ry="17" fill="#f1dbbc"/><path d="M17 25v-5C17 6 45 3 47 22l-1 6-5-10c-5 5-13 7-24 7" fill="#344b49"/><circle cx="27" cy="28" r="1.5" fill="#344b49"/><circle cx="37" cy="28" r="1.5" fill="#344b49"/><path d="M28 35q4 3 8 0" fill="none" stroke="#8b6555" stroke-width="1.5" stroke-linecap="round"/></svg>';
 return 'data:image/svg+xml,'+encodeURIComponent(svg).replaceAll("'",'%27');
}
function personAvatar(id){
 const p=person(id),label=p?.name||name(id),initials=label==='Outside current view'?'?':label.trim().split(/\s+/).map(x=>x[0]).slice(0,2).join('').toUpperCase();
 // Only embedded raster photos supplied in the scoped person record are rendered.
 // Do not request employee photos from external hosts or infer a face from a name.
 const photo=typeof profilePhoto==='function'?profilePhoto(p):p?.photo_data_url,src=typeof photo==='string'&&photo.length<=280000&&/^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/]+=*$/.test(photo)?photo:null;
 return '<span class="person-avatar" data-profile-person="'+esc(id||'')+'" role="img" aria-label="'+esc(label+(src?' · profile photo':' · default avatar'))+'" title="'+esc(label)+'"><span aria-hidden="true">'+esc(initials)+'</span>'+'<img src="'+(src||defaultAvatarImage(id,p?.avatar_style))+'" alt="" loading="lazy" decoding="async" width="28" height="28">'+'</span>';
}
function personLabel(id){return '<span class="person-label">'+personAvatar(id)+'<span>'+esc(name(id))+'</span></span>'}
function avatarStack(ids,label='Assigned people'){
 const unique=[...new Set(ids.filter(Boolean))];if(!unique.length)return '';
 return '<span class="people-stack" aria-label="'+esc(label)+'">'+unique.slice(0,4).map(personAvatar).join('')+(unique.length>4?'<span class="person-avatar people-overflow" title="'+esc(unique.slice(4).map(name).join(', '))+'">+'+(unique.length-4)+'</span>':'')+'</span>';
}
function goalLifecycle(g){
 const v=latest(g.id),base=approved(g.id),state=status(g),proposed=!!base&&base.id!==v.id;
 if(g.assignment_state==='pending')return {state:'pending',label:'Awaiting assignment acceptance',actionable:true};
 if(g.assignment_state==='pushed_back')return {state:'pushed_back',label:'Assignment returned for clarification',actionable:true};
 if(proposed)return {state,label:'v'+v.version_no+' '+({draft:'revision in draft',submitted:'awaiting approval',returned:'returned for changes'}[state]||state)+' · v'+base.version_no+' remains approved',actionable:['draft','submitted','returned'].includes(state)};
 return {state,label:base?'Approved v'+base.version_no:({draft:'Draft · not approved',submitted:'Awaiting approval',returned:'Returned for changes'}[state]||state),actionable:['draft','submitted','returned'].includes(state)&&!base};
}
function goalLifecycleBadge(g){const l=goalLifecycle(g);return '<span class="goal-lifecycle '+(l.actionable?'pending':'')+'">'+esc(l.label)+'</span>'}
function goalSecondaryProgress(g){
 if(!['combined','outcome'].includes(goalBasis(g)))return '';
 const pct=g.active_version_id?data.progress.find(p=>p.root_id===g.id)?.delivery_pct:null;
 return '<small class="goal-secondary">Accepted delivery: <b>'+(pct==null?'Not baselined':esc(pct)+'%')+'</b> · both required</small>';
}
function goalResourceRows(g,v=gv(g)){return (data.allocations||[]).filter(a=>a.version_id===v.id)}
function goalResourceSummary(g){
 const v=gv(g),rows=goalResourceRows(g,v),people=[...new Set(rows.map(a=>a.worker_id))],children=goals().filter(c=>c.parent_id===g.id);
 return '<div class="goal-people">'+(children.length?'<span>'+avatarStack(children.map(c=>gv(c).owner_id),'Workstream owners')+' '+children.length+' workstream'+(children.length===1?'':'s')+'</span>':'')+(rows.length?'<span>'+avatarStack(people,'Resource contributors')+' '+people.length+' contributor'+(people.length===1?'':'s')+' · '+(g.active_version_id?'approved':'proposed')+'</span>':'<small>No '+(g.active_version_id?'approved':'proposed')+' resource allocation at this level</small>')+'</div>';
}
function goalResourceDetails(g,v=gv(g)){
 const rows=goalResourceRows(g,v);if(!rows.length)return '';
 return '<details class="goal-resources"><summary>Resource commitments · '+rows.length+'</summary><p>'+(v.id===g.active_version_id?'Approved':'Proposed')+' v'+v.version_no+' at this level. Monthly percentages are not progress; receiving workstream owners resource their own plans. Capacity is unverified.</p>'+table(['Contributor / deliverable','Dates / month','Allocation'],rows.map(a=>[personLabel(a.worker_id)+'<small>'+esc(data.deliverables.find(d=>d.id===a.deliverable_id)?.title||'Existing goal-level commitment')+'</small>',portfolioDate(a.starts_on)+' to '+portfolioDate(a.ends_on)+'<small>'+esc(a.month?.slice(0,7))+'</small>',esc(a.allocation_pct)+'%']))+'</details>';
}
document.addEventListener('error',e=>{if(e.target.matches?.('.person-avatar img'))e.target.remove()},true);

function goalResourceIssues(g,v=latest(g.id)){
 const rows=goalResourceRows(g,v),otherActive=new Set(data.goals.filter(x=>x.id!==g.id).map(x=>x.active_version_id).filter(Boolean)),keys=[...new Set(rows.map(a=>a.worker_id+'|'+a.month))],issues=[];
 for(const key of keys){const [worker,month]=key.split('|'),total=(data.allocations||[]).filter(a=>a.worker_id===worker&&a.month===month&&(a.version_id===v.id||otherActive.has(a.version_id))).reduce((n,a)=>n+Number(a.allocation_pct||0),0);if(total>100.001)issues.push(name(worker)+' has '+Number(total.toFixed(2))+'% planned in '+month.slice(0,7)+' across this plan and other visible approved commitments. Revise the allocation.');}
 return issues;
}

function goalNextLabel(g){return goalBasis(g)==='metric'?'No delivery gate required':!g.active_version_id?'Delivery plan not approved':activeDeliveries(g).length?'All agreed deliverables accepted':'No approved delivery breakdown'}
