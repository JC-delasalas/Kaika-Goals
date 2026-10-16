"""Versioned success basis and submission contract for the local demo."""
import math,datetime
from demo_mutations import require

def basis(v):return v.get('success_basis','outcome')

def validate_plan(f,v):
 require(basis(v) in ['delivery','outcome','metric','combined'],'Choose metric-only, delivery-based or combined success.')
 require(bool(v.get('title','').strip()) and bool(v.get('description','').strip()),'Complete the goal title and purpose.')
 require(v.get('starts_on','') and v.get('ends_on','') and v['starts_on']<=v['ends_on'],'Provide a valid goal period.')
 ds=[d for d in f.db['deliverables'] if d['version_id']==v['id']]
 children=[g for g in f.db['goals'] if g.get('parent_id')==v['goal_id']]
 g=next(g for g in f.db['goals'] if g['id']==v['goal_id'])
 require(not ds or g.get('hierarchy_model')!='workstream-delivery' or g.get('node_kind')=='workstream','Deliverables must attach to a workstream, not directly to an objective.')
 require(basis(v)=='metric' or ds or children,'Define workstreams, or final-level deliverables, before submitting.')
 require(v.get('approver_id') and v['approver_id']!=v['owner_id'],'An independent plan approver must be assigned before submission.')
 require(g.get('assignment_state') not in ['pending','pushed_back'],'Accept the assigned remit before submitting.')
 for key in ['starts_on','ends_on']:
  try:datetime.date.fromisoformat(v[key])
  except (ValueError,TypeError):require(False,'Provide valid calendar dates.')
 require(v.get('cadence') in ['daily','weekly','monthly'] and v.get('priority') in ['vital','fuel'] and v.get('category','').strip(),'Choose priority, category and update cadence.')
 parent=next((p for p in f.db['goals'] if p['id']==g.get('parent_id')),None)
 if parent:
  pv=next((p for p in f.db['versions'] if p['id']==parent.get('active_version_id')),None) or max((p for p in f.db['versions'] if p['goal_id']==parent['id']),key=lambda p:p['version_no'])
  if pv.get('starts_on') and pv.get('ends_on'):require(pv['starts_on']<=v['starts_on']<=v['ends_on']<=pv['ends_on'],'Keep this workstream period inside its parent commitment.')
 for child in children:
  cv=max((x for x in f.db['versions'] if x['goal_id']==child['id']),key=lambda x:x['version_no'])
  require(cv['owner_id'] in f.scope(v['owner_id']),'A workstream owner must be within the parent owner’s reporting team.')
  if cv.get('starts_on') and cv.get('ends_on'):require(v['starts_on']<=cv['starts_on']<=cv['ends_on']<=v['ends_on'],'Keep each workstream period within this goal period. Unset dates remain the receiving owner’s responsibility.')
 for d in ds:
  require(bool(d.get('title','').strip()) and bool(d.get('definition_of_done','').strip()),'Every deliverable needs a title and definition of done.')
  require(number(d.get('effort_days'))>0,'Every deliverable needs a positive effort estimate.')
  require(d.get('owner_id') in f.scope(v['owner_id']),'A deliverable must have an owner in the goal owner’s reporting team, including the manager.')
  valid_day(d.get('due_on'),'deliverable due date')
  require(d.get('owner_id') and v['starts_on']<=d.get('due_on','')<=v['ends_on'],'Assign each deliverable an owner and date within the goal period.')
  cs=[c for c in f.db['checkpoints'] if c['deliverable_id']==d['id']]
  require(cs and all(number(c.get('weight'))>0 for c in cs) and abs(sum(number(c.get('weight')) for c in cs)-100)<.001,'Each deliverable requires positive checkpoint weights totaling 100%.')
  for c in cs:
   require(c.get('title','').strip() and c.get('acceptance_criteria','').strip(),'Define checkpoint titles and acceptance criteria.')
   require(c.get('reviewer_id') and c['reviewer_id']!=d['owner_id'],'Every checkpoint requires an independent reviewer.')
   valid_day(c.get('due_on'),'checkpoint due date')
   require(v['starts_on']<=c.get('due_on','')<=d['due_on'],'Checkpoint dates must fall within the deliverable period.')
 for k in f.db.get('kpis',[]):
  if k['version_id']!=v['id']:continue
  require(k.get('title','').strip() and k.get('source','').strip() and k.get('direction') in ['above','below'],'Define the KPI, source and threshold direction.')
  number(k.get('target'))
 for a in f.db['allocations']:
  if a['version_id']!=v['id']:continue
  require(a.get('worker_id') in f.scope(v['owner_id']),'Allocate a person in the owner’s reporting scope.')
  require(0<number(a.get('allocation_pct'))<=100,'Monthly allocations must be greater than 0 and no more than 100%.')
  if v.get('registration_contract')==2:
   delivery=next((d for d in ds if d['id']==a.get('deliverable_id')),None)
   require(delivery is not None,'Link each resource commitment to a deliverable in this version.')
   try:
    start=datetime.date.fromisoformat(a.get('starts_on',''));end=datetime.date.fromisoformat(a.get('ends_on',''))
   except (ValueError,TypeError):require(False,'Set valid resource start and end dates.')
   require(v['starts_on']<=str(start)<=str(end)<=delivery['due_on'],'Resource dates must fit the goal and linked deliverable.')
   require(str(start)[:7]<=a.get('month','')[:7]<=str(end)[:7],'The allocation month must intersect its resource date range.')
  valid_day(a.get('month'),'allocation month')
  require(a.get('month','').endswith('-01') and v['starts_on'][:7]<=a['month'][:7]<=v['ends_on'][:7],'Allocation months must be inside the goal period.')
 totals={}
 other_active={g['active_version_id'] for g in f.db['goals'] if g['id']!=v['goal_id'] and g.get('active_version_id')}
 proposed=[a for a in f.db['allocations'] if a['version_id']==v['id']]
 keys={(a['worker_id'],a['month']) for a in proposed}
 for a in f.db['allocations']:
  key=(a['worker_id'],a['month'])
  if key in keys and (a['version_id']==v['id'] or a['version_id'] in other_active):totals[key]=totals.get(key,0)+number(a['allocation_pct'])
 require(all(n<=100+.001 for n in totals.values()),'A person’s proposed monthly allocation plus existing approved commitments exceeds 100%. Revise the allocation before approval.')
 ms=[m for m in f.db['measures'] if m['version_id']==v['id']]
 if basis(v)=='delivery':
  require(not ms,'Delivery-based plans use acceptance checkpoints, not outcome measures. Remove the measures or choose outcome-based success.')
 else:
  require(1<=len(ms)<=4,'Outcome-based plans require 1–4 outcome measures.')
  require(all(number(m.get('weight'))>0 for m in ms) and abs(sum(number(m.get('weight')) for m in ms)-100)<.001,'Outcome measure weights must be positive and total 100%.')
  for m in ms:
   require(m.get('title','').strip() and m.get('unit','').strip() and m.get('source_definition','').strip(),'Describe every outcome measure and its measurement source.')
   b,t=number(m.get('baseline')),number(m.get('target'))
   require((t>b if m.get('direction')=='increase' else t<b if m.get('direction')=='decrease' else False),'Outcome targets must differ from the baseline in the chosen direction.')

def number(value):
 try:n=float(value)
 except (ValueError,TypeError):n=float('nan')
 require(math.isfinite(n),'Estimates, weights and targets must be finite numbers.')
 return n

def valid_day(value,label):
 try:datetime.date.fromisoformat(value)
 except (TypeError,ValueError):require(False,'Set a valid '+label+'.')
