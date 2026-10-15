"""Versioned success basis and submission contract for the local demo."""
import math
from demo_mutations import require

def basis(v):return v.get('success_basis','outcome')

def validate_plan(f,v):
 require(basis(v) in ['delivery','outcome'],'Choose delivery-based or outcome-based success.')
 require(bool(v.get('title','').strip()) and bool(v.get('description','').strip()),'Complete the goal title and purpose.')
 require(v.get('starts_on','') and v.get('ends_on','') and v['starts_on']<=v['ends_on'],'Provide a valid goal period.')
 ds=[d for d in f.db['deliverables'] if d['version_id']==v['id']]
 children=[g for g in f.db['goals'] if g.get('parent_id')==v['goal_id']]
 g=next(g for g in f.db['goals'] if g['id']==v['goal_id'])
 require(not ds or g.get('hierarchy_model')!='workstream-delivery' or g.get('node_kind')=='workstream','Deliverables must attach to a workstream, not directly to an objective.')
 require(ds or children,'Define workstreams, or final-level deliverables, before submitting.')
 for child in children:
  cv=max((x for x in f.db['versions'] if x['goal_id']==child['id']),key=lambda x:x['version_no'])
  require(cv['owner_id'] in f.scope(v['owner_id']),'A workstream owner must be within the parent owner’s reporting team.')
  require(v['starts_on']<=cv.get('starts_on','')<=cv.get('ends_on','')<=v['ends_on'],'Set each workstream period within this goal period before approval.')
 for d in ds:
  require(bool(d.get('title','').strip()) and bool(d.get('definition_of_done','').strip()),'Every deliverable needs a title and definition of done.')
  require(number(d.get('effort_days'))>0,'Every deliverable needs a positive effort estimate.')
  require(d.get('owner_id') in f.scope(v['owner_id']),'A deliverable must have an owner in the goal owner’s reporting team, including the manager.')
  require(d.get('owner_id') and v['starts_on']<=d.get('due_on','')<=v['ends_on'],'Assign each deliverable an owner and date within the goal period.')
  cs=[c for c in f.db['checkpoints'] if c['deliverable_id']==d['id']]
  require(cs and all(number(c.get('weight'))>0 for c in cs) and abs(sum(number(c.get('weight')) for c in cs)-100)<.001,'Each deliverable requires positive checkpoint weights totaling 100%.')
  for c in cs:
   require(c.get('title','').strip() and c.get('acceptance_criteria','').strip(),'Define checkpoint titles and acceptance criteria.')
   require(c.get('reviewer_id') and c['reviewer_id']!=d['owner_id'],'Every checkpoint requires an independent reviewer.')
   require(v['starts_on']<=c.get('due_on','')<=d['due_on'],'Checkpoint dates must fall within the deliverable period.')
 for k in f.db.get('kpis',[]):
  if k['version_id']!=v['id']:continue
  require(k.get('title','').strip() and k.get('source','').strip() and k.get('direction') in ['above','below'],'Define the KPI, source and threshold direction.')
  number(k.get('target'))
 for a in f.db['allocations']:
  if a['version_id']!=v['id']:continue
  require(a.get('worker_id') in f.scope(v['owner_id']),'Allocate a person in the owner’s reporting scope.')
  require(0<number(a.get('allocation_pct'))<=100,'Monthly allocations must be greater than 0 and no more than 100%.')
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
   require(m.get('title','').strip() and m.get('source_definition','').strip(),'Describe every outcome measure and its measurement source.')
   b,t=number(m.get('baseline')),number(m.get('target'))
   require((t>b if m.get('direction')=='increase' else t<b if m.get('direction')=='decrease' else False),'Outcome targets must differ from the baseline in the chosen direction.')

def number(value):
 try:n=float(value)
 except (ValueError,TypeError):n=float('nan')
 require(math.isfinite(n),'Estimates, weights and targets must be finite numbers.')
 return n
