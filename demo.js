// Local workshop controls. No tracker service or external screenshot service.
let demoOpen=false,demoTab='scenarios',demoPinMode=false,demoTarget=null,demoShot=null,demoIssueId=null,demoIssues=[];
const demoLabels={strategy:'Strategy workshop · complete hierarchy',delivery_walkthrough:'Delivery-based walkthrough',walkthrough:'Editable walkthrough',mixed:'Complete data · mixed statuses',partial:'Partially filled plans',empty:'Empty workspace',finished:'All work completed'};
let bugDatabase,demoReportContext=null;
function bugDB(){if(!bugDatabase)bugDatabase=new Promise((resolve,reject)=>{const r=indexedDB.open('kaika-demo-reports',1);r.onupgradeneeded=()=>r.result.createObjectStore('issues',{keyPath:'id'});r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)});return bugDatabase}
async function bugStore(operation,value){const db=await bugDB();return new Promise((resolve,reject)=>{const tx=db.transaction('issues',operation==='getAll'?'readonly':'readwrite'),r=tx.objectStore('issues')[operation](value);let result;r.onsuccess=()=>result=r.result;tx.oncomplete=()=>resolve(result);tx.onerror=()=>reject(tx.error);tx.onabort=()=>reject(tx.error)})}
function demoButton(text,action,extra=''){return '<button type="button" class="btn" data-demo="'+action+'" '+extra+'>'+esc(text)+'</button>'}
function updateDemoChrome(){
 const root=$('demo-tools');if(!root)return;root.hidden=!['fixture','supabase-demo'].includes(mode);
 if(!['fixture','supabase-demo'].includes(mode))return;
 $('demo-current').textContent=data?.demo?.label||'Loading scenarios';
 if(mode==='supabase-demo'){
  const org=data?.organization;
  $('freshness').textContent=(org?'Workday organization · source '+org.source_as_of+' · '+org.active_workers+' active workers · Goals, approvals and results are simulated':'Synthetic workshop data')+' · saved in Supabase · scenario date '+(data?.demo?.as_of||'2026-10-27')+' · revision '+(data?.persistence?.revision??'…');
 }
 else if(data?.demo)$('freshness').textContent='Synthetic workshop data · demo date '+data.demo.as_of+' · '+data.demo.label;
 $('demo-toggle').setAttribute('aria-expanded',String(demoOpen));
}
function demoRender(){
 const box=$('demo-panel');box.hidden=!demoOpen;updateDemoChrome();if(!demoOpen)return;
 let content='';
 if(demoTab==='scenarios'&&mode==='supabase-demo')content='<h3>Connected workshop</h3><p>Goals, deliverables, approvals and check-ins save to Supabase. Evidence files use the private bucket.</p><p>Use the app to edit the sample plans. Refreshing or restarting preserves your changes.</p><p>Scenario replacement is disabled for this connected workspace. Screenshots and bug reports remain available.</p>';
 else if(demoTab==='scenarios')content='<p class="demo-help">Choose the story for your walkthrough. This replaces local demo records for all personas; bug reports stay saved.</p><label class="formfield">Dataset<select id="demo-preset">'+Object.entries(demoLabels).map(([k,v])=>'<option value="'+k+'" '+(data?.demo?.preset===k?'selected':'')+'>'+esc(v)+'</option>').join('')+'</select></label><div class="demo-preset-note" id="demo-preset-note"></div>'+demoButton('Load scenario','load')+'<h3>Status coverage</h3><p class="demo-help">The mixed scenario includes approved, draft, submitted and returned plans.</p><div class="demo-legend">'+['complete','on_track','not_started','awaiting_review','at_risk','blocked','unknown'].map(badge).join('')+'</div><p class="demo-help">Deliverables also show in progress and overdue. Percentages come from accepted checkpoints weighted by effort. Demo date: 27 October 2026.</p>';
 else if(demoTab==='report')content='<p class="demo-help">Pin an element or describe an issue. Nothing is sent to BugHerd or another service.</p>'+demoButton(demoTarget?'Pick another element':'Pin an element','pin')+'<p class="demo-target">'+esc(demoTarget?.text||'No element selected. The current page will be recorded.')+'</p><form id="demo-report-form"><label class="formfield">Issue title<input name="title" required maxlength="180" placeholder="Example: Deliverable status is hard to read"></label><label class="formfield">What happened?<textarea name="description" required placeholder="1. What you did\n2. What happened\n3. What you expected"></textarea></label><div class="formrow"><label class="formfield">Severity<select name="severity"><option>Medium</option><option>Low</option><option>High</option><option>Critical</option></select></label><label class="formfield">Status<select name="status"><option>Open</option><option>In progress</option><option>Resolved</option></select></label></div><div class="demo-shot-state">'+(demoShot?'View captured and attached.':'No screenshot attached.')+'</div>'+demoButton('Attach current view','attach')+' <button class="btn primary">Save issue locally</button><p id="demo-report-error" role="alert"></p></form>';
 else if(demoTab==='detail'){
 const i=demoIssues.find(x=>x.id===demoIssueId);
 content=i?'<h3>'+esc(i.title)+'</h3><p class="pre">'+esc(i.description)+'</p><dl class="demo-meta"><dt>Severity / status</dt><dd>'+esc(i.severity)+' / '+esc(i.status)+'</dd><dt>Page / leader</dt><dd>'+esc(i.context.route)+' · '+esc(i.context.leader)+'</dd><dt>Dataset / viewport</dt><dd>'+esc(i.context.preset)+' · '+i.context.width+' × '+i.context.height+'</dd><dt>Element</dt><dd>'+esc(i.target?.text||'Page-level issue')+'</dd><dt>Recorded</dt><dd>'+esc(new Date(i.created_at).toLocaleString())+'</dd></dl><label class="formfield">Update status<select id="demo-issue-status">'+['Open','In progress','Resolved'].map(s=>'<option '+(s===i.status?'selected':'')+'>'+s+'</option>').join('')+'</select></label>'+demoButton('Save status','status')+' '+demoButton('Go to recorded page','locate')+(i.screenshot?' '+demoButton('Download screenshot','issue-shot'):'')+ '<p>'+demoButton('Back to issues','issues')+'</p>':'<p>Issue not found.</p>';
 } else content='<div class="tools">'+demoButton('New issue','report')+demoButton('Export reports','export')+'</div><p class="demo-help">Saved in this browser. Export before clearing browser data.</p>'+(!demoIssues.length?'<div class="empty"><h3>No issues yet</h3><p>Pin a problem on the page to start a report.</p></div>':demoIssues.map(i=>'<button class="demo-issue" data-demo="detail" data-issue="'+i.id+'"><strong>'+esc(i.title)+'</strong><span>'+esc(i.severity)+' · '+esc(i.status)+' · '+esc(i.context.route)+'</span></button>').join(''));
 box.innerHTML='<header><div><h2>Demo studio</h2><small>Local workshop tools</small></div>'+demoButton('Close','close','aria-label="Close demo controls"')+'</header><nav class="demo-tabs" aria-label="Demo studio"><button data-demo="scenarios" aria-current="'+(demoTab==='scenarios'?'page':'false')+'">Scenarios</button><button data-demo="report" aria-current="'+(demoTab==='report'?'page':'false')+'">Report issue</button><button data-demo="issues" aria-current="'+(['issues','detail'].includes(demoTab)?'page':'false')+'">Issues ('+demoIssues.length+')</button></nav><div class="demo-body">'+content+'</div>';
 box.scrollTop=0;demoPresetNote();
}
function demoPresetNote(){const el=$('demo-preset-note');if(!el)return;el.textContent={strategy:'A complete strategy: three pillars, director objectives, inherited workstreams, team-owned deliverables, KPIs, accepted evidence and a scoped support request. All names and results are synthetic.',delivery_walkthrough:'Launch a monitoring service. Two deliverables with evidence checkpoints; accepting all of them achieves the goal without a KPI reading.',walkthrough:'One approved objective with two deliverables, starting at 0%. Change status, write or upload evidence, switch to the reviewer and accept checkpoints.',mixed:'11 objectives in Ada’s scope: completed, progressing, at risk, blocked, overdue work, not started, awaiting review, unknown, draft, submitted and returned.',partial:'Missing purpose, measure, effort, acceptance criteria and allocation examples. Unknown progress stays unknown.',empty:'Keep the reporting team; clear goals, evidence, portfolios and reviews for a first-use walkthrough.',finished:'Three objectives with 100% accepted delivery and measured outcomes, evidence files and decisions.'}[$('demo-preset').value]}
function downloadDemo(contents,filename,type){const a=document.createElement('a'),u=URL.createObjectURL(new Blob([contents],{type}));a.href=u;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(u),3000)}
// Vector screenshot of the current app viewport. No capture permission, external service or hidden data.
function captureDemoView(){
 const width=innerWidth,height=innerHeight,wrapper=document.createElement('div');wrapper.setAttribute('xmlns','http://www.w3.org/1999/xhtml');wrapper.style.cssText='position:relative;overflow:hidden;width:'+width+'px;height:'+height+'px;background:#f5f7f3';
 for(const src of document.querySelectorAll('body > .sidebar,body > .app-main')){
  const copy=src.cloneNode(true),originals=[src,...src.querySelectorAll('*')],copies=[copy,...copy.querySelectorAll('*')];
  originals.forEach((el,n)=>{const dst=copies[n],style=getComputedStyle(el);let text='';for(const prop of style)text+=prop+':'+style.getPropertyValue(prop)+';';dst.setAttribute('style',text);
   [...dst.attributes].filter(a=>a.name.startsWith('on')).forEach(a=>dst.removeAttribute(a.name));
   if(el instanceof HTMLInputElement)dst.setAttribute('value',el.type==='password'?'':el.value);
   if(el instanceof HTMLTextAreaElement)dst.textContent=el.value;
   if(el instanceof HTMLSelectElement){[...dst.options].forEach((o,i)=>{if(el.options[i].selected)o.setAttribute('selected','');else o.removeAttribute('selected')})}
  });
  copy.querySelectorAll('script,iframe,object,embed,video').forEach(el=>el.remove());
  const rect=src.getBoundingClientRect();copy.style.position='absolute';copy.style.left=rect.left+'px';copy.style.top=rect.top+'px';copy.style.width=rect.width+'px';copy.style.height=rect.height+'px';copy.style.margin='0';wrapper.append(copy);
 }
 if(demoTarget&&demoTarget.route===location.hash){const pin=document.createElement('div');pin.textContent='1';pin.style.cssText='position:absolute;left:'+demoTarget.x+'px;top:'+demoTarget.y+'px;background:#a63330;color:white;border:2px solid white;border-radius:50%;width:28px;height:28px;text-align:center;line-height:24px;font:600 16px sans-serif';wrapper.append(pin)}
 return '<svg xmlns="http://www.w3.org/2000/svg" width="'+width+'" height="'+height+'" viewBox="0 0 '+width+' '+height+'"><foreignObject width="100%" height="100%">'+new XMLSerializer().serializeToString(wrapper)+'</foreignObject></svg>';
}
function demoContext(){return{route:location.hash||'#/portfolio',leader:name(leader),leader_id:leader,preset:data?.demo?.label||'unknown',demo_date:data?.demo?.as_of,width:innerWidth,height:innerHeight,browser:navigator.userAgent}}
async function demoAction(action,button){
 if(!['fixture','supabase-demo'].includes(mode))return;
 if(action==='toggle'){try{demoIssues=(await bugStore('getAll')).sort((a,b)=>b.created_at.localeCompare(a.created_at));}catch(e){toast('Bug storage unavailable. Scenarios still work.');}demoOpen=!demoOpen;demoRender();if(demoOpen)$('demo-panel').querySelector('button').focus();return}
 if(action==='close'){demoOpen=false;demoRender();$('demo-toggle').focus();return}
 if(['scenarios','issues','report'].includes(action)){demoTab=action;demoOpen=true;if(action==='issues')demoIssues=(await bugStore('getAll')).sort((a,b)=>b.created_at.localeCompare(a.created_at));demoRender();return}
 if(['load','confirm-load'].includes(action)&&mode==='supabase-demo')throw Error('Connected data stays in Supabase. Scenario replacement is disabled here.');
 if(action==='load'){
  if(busy||loading)throw Error('Wait for the current operation to finish.');
  button.outerHTML='<div class="demo-reset-confirm" role="alert"><p>Replace the local demo records? Bug reports will be kept.</p>'+demoButton('Replace demo records','confirm-load')+' '+demoButton('Cancel','scenarios')+'</div>';return;
 }
 if(action==='confirm-load'){
  if(busy||loading)throw Error('Wait for the current operation to finish.');
  const preset=$('demo-preset').value;busy=true;
  try{await request('demo_scenario',{preset});const roster=await request('leaders');leaders=roster.leaders;if(!leaders.some(p=>p.id===leader))leader=leaders[0]?.id;$('leader').innerHTML=leaders.map(p=>'<option value="'+p.id+'" '+(p.id===leader?'selected':'')+'>'+esc(p.name)+' · '+esc(p.team)+'</option>').join('');dirty=false;draft=null;draftGoal='';pendingCommand=null;leadershipState.clear();location.hash='/portfolio';await refresh();if(problem)throw Error(problem);notifyDemoChange();demoRender();toast('Loaded '+demoLabels[preset]+'.')}finally{busy=false}return;
 }
 if(action==='screenshot'){downloadDemo(captureDemoView(),'kaika-'+route()+'-screenshot.svg','image/svg+xml');toast('View saved as SVG. Open in a browser to view.');return}
 if(action==='attach'){demoShot=captureDemoView();demoReportContext=demoContext();$('demo-panel').querySelector('.demo-shot-state').textContent='Current view attached (SVG).';return}
 if(action==='pin'){demoPinMode=true;demoOpen=false;demoRender();document.body.classList.add('demo-pinning');$('demo-pin-banner').hidden=false;return}
 if(action==='cancel-pin'){stopDemoPin();return}
 if(action==='detail'){demoIssueId=button.dataset.issue;demoTab='detail';demoRender();return}
 if(action==='status'){const i=demoIssues.find(i=>i.id===demoIssueId);i.status=$('demo-issue-status').value;i.updated_at=new Date().toISOString();await bugStore('put',i);demoRender();toast('Issue status saved locally.');return}
 if(action==='locate'){const i=demoIssues.find(i=>i.id===demoIssueId);if(i.context.leader_id!==leader)throw Error('Switch to '+i.context.leader+' to revisit this issue.');location.hash=i.context.route;demoOpen=false;demoRender();toast('Opened recorded page. Dataset changes may affect the original element.');return}
 if(action==='issue-shot'){const i=demoIssues.find(i=>i.id===demoIssueId);downloadDemo(i.screenshot,'kaika-issue-'+i.id+'.svg','image/svg+xml');return}
 if(action==='export'){const issues=await bugStore('getAll');downloadDemo(JSON.stringify({application:'Kaika local demo',exported_at:new Date().toISOString(),issues},null,2),'kaika-bug-reports.json','application/json');toast('Reports exported with context and attached SVG views.');return}
}
function stopDemoPin(){demoPinMode=false;document.body.classList.remove('demo-pinning');$('demo-pin-banner').hidden=true}
document.addEventListener('click',e=>{
 if(!demoPinMode||e.target.closest('#demo-tools,#demo-pin-banner'))return;
 e.preventDefault();e.stopImmediatePropagation();
 const el=e.target.closest('button,a,input,select,textarea,h1,h2,h3,td,.pill,.delivery-row')||e.target;
 demoTarget={route:location.hash,x:e.clientX,y:e.clientY,tag:el.tagName,text:(el.innerText||el.getAttribute('aria-label')||el.name||el.tagName).slice(0,240),selector:el.id?'#'+CSS.escape(el.id):el.tagName.toLowerCase()+(el.classList.length?'.'+[...el.classList].map(CSS.escape).join('.'):'')};
 stopDemoPin();demoShot=captureDemoView();demoReportContext=demoContext();demoTab='report';demoOpen=true;demoRender();
},true);
document.addEventListener('click',e=>{const b=e.target.closest('[data-demo]');if(b)demoAction(b.dataset.demo,b).catch(err=>toast('Demo tools: '+errorText(err)))});
document.addEventListener('change',e=>{if(e.target.id==='demo-preset')demoPresetNote()});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){if(demoPinMode)stopDemoPin();else if(demoOpen){demoOpen=false;demoRender();$('demo-toggle').focus()}}});
document.addEventListener('submit',async e=>{
 if(e.target.id!=='demo-report-form')return;e.preventDefault();
 const f=e.target,values=Object.fromEntries(new FormData(f)),button=f.querySelector('[type="submit"],button:not([type])');button.disabled=true;
 try{
  const issue={id:crypto.randomUUID(),title:values.title.trim(),description:values.description.trim(),severity:values.severity,status:values.status,created_at:new Date().toISOString(),context:demoReportContext||demoContext(),target:demoTarget,screenshot:demoShot};
  if(!issue.title||!issue.description)throw Error('Add a title and a description.');
  await bugStore('put',issue);demoIssues=(await bugStore('getAll')).sort((a,b)=>b.created_at.localeCompare(a.created_at));demoShot=null;demoTarget=null;demoReportContext=null;demoTab='issues';demoRender();toast('Issue saved in this browser.');
 }catch(err){$('demo-report-error').textContent='Could not save: '+errorText(err)+'. Export existing reports before clearing browser storage.';button.disabled=false}
});
