"""Scoped leadership workflows. Synthetic local demo, no external services."""
import copy,uuid,datetime,math
from demo_mutations import require
KEYS=['saved_views','reflections','replies','followups','kpis','kpi_readings']
ACTIONS={'save_view','delete_view','record_question','reply_question','close_question','record_decision','record_learning','create_followup','complete_followup','publish_snapshot','record_kpi','accept_assignment','pushback_assignment','resend_assignment'}
def ensure(f):
 for k in KEYS:f.db.setdefault(k,[])
def scope_extra(x,l,gids,vids):
 x['saved_views']=[r for r in x.get('saved_views',[]) if r['owner_id']==l]
 for key in ['reflections','replies','followups']:x[key]=[r for r in x.get(key,[]) if r['goal_id'] in gids]
 x['kpis']=[r for r in x.get('kpis',[]) if r['version_id'] in vids]
 kids={k['id'] for k in x['kpis']};x['kpi_readings']=[r for r in x.get('kpi_readings',[]) if r['kpi_id'] in kids]
 x['reviews']=[r for r in x['reviews'] if set(r.get('goal_ids',[]))<=gids]
def date(value):
 try:return datetime.date.fromisoformat(value)
 except (TypeError,ValueError):require(False,'Enter a valid date.')
def text(p,key):
 v=str(p.get(key,'')).strip();require(bool(v),'Complete '+key.replace('_',' ')+'.');return v[:12000]
def handle(f,l,action,p):
 from fixture_server import now
 ensure(f);s=f.state(l);gids={g['id'] for g in s['goals']};rid=str(uuid.uuid4());ts=now()
 if action=='save_view':
  name=text(p,'name');filters=p.get('filters',{})
  if isinstance(filters,str):
   import json
   filters=json.loads(filters)
  require(isinstance(filters,dict),'Invalid view filters.')
  fields={k:str(filters.get(k,''))[:200] for k in ['search','health','scope','group','display','basis','collection','category']}
  require(not any(v['owner_id']==l and v['name'].lower()==name.lower() for v in f.db['saved_views']),'A personal view already uses this name.')
  f.db['saved_views'].append(dict(id=rid,owner_id=l,name=name,filters=fields,created_at=ts));return {'id':rid}
 if action=='delete_view':
  require(any(v['id']==p.get('id') and v['owner_id']==l for v in f.db['saved_views']),'View is outside your personal workspace.',403)
  f.db['saved_views']=[v for v in f.db['saved_views'] if not(v['id']==p['id'] and v['owner_id']==l)];return {'id':p['id']}
 if action=='publish_snapshot':
  if p.get('summary_capture'):ts=datetime.datetime.now(datetime.timezone.utc).isoformat()
  ids=p.get('goal_ids',[])
  if isinstance(ids,str):
   import json
   ids=json.loads(ids)
  require(isinstance(ids,list) and ids and set(ids)<=gids,'Choose visible objectives for this review.',403)
  ids=set(ids);selected=set(ids)
  while True:
   expanded=ids|{g['id'] for g in s['goals'] if g.get('parent_id') in ids}
   if expanded==ids:break
   ids=expanded
  vs=[v for v in s['versions'] if v['goal_id'] in ids];vids={v['id'] for v in vs};dids={d['id'] for d in s['deliverables'] if d['version_id'] in vids};mids={m['id'] for m in s['measures'] if m['version_id'] in vids};kids={k['id'] for k in s['kpis'] if k['version_id'] in vids}
  snapshot=dict(text=text(p,'text'),as_of=f.as_of,goals=[g for g in s['goals'] if g['id'] in selected],contributing_goals=[g for g in s['goals'] if g['id'] in ids-selected],versions=vs,progress=[r for r in s['progress'] if r['root_id'] in ids],outcomes=[r for r in s['outcomes'] if r['goal_id'] in ids],measures=[m for m in s['measures'] if m['id'] in mids],readings=[r for r in s['readings'] if r['measure_id'] in mids],kpis=[k for k in s['kpis'] if k['id'] in kids],kpi_readings=[r for r in s['kpi_readings'] if r['kpi_id'] in kids],evidence=[e for e in s['evidence'] if e['deliverable_id'] in dids])
  for key in ['deliverables','allocations']:snapshot[key]=[r for r in s[key] if r['version_id'] in vids]
  for key in ['checkpoints','acceptances','delivery_progress']:snapshot[key]=[r for r in s[key] if r['deliverable_id'] in dids]
  for key in ['checkins','questions','decisions','reflections','replies','followups']:snapshot[key]=[r for r in s[key] if r['goal_id'] in ids]
  if p.get('summary_capture'):
   filters=p.get('filters',{});require(isinstance(filters,dict),'Invalid summary filters.')
   snapshot['summary_meta']={'method':'goals-pulse-v1','leader_id':l,'captured_at':ts,'filters':{k:str(filters.get(k,''))[:200] for k in ['scope','search','health','basis','category','collection']}}
  snapshot['support_requests']=[r for r in s.get('support_requests',[]) if r.get('requester_goal_id') in ids or r.get('delivery_goal_id') in ids]
  f.db['reviews'].append(dict(id=rid,facilitator_id=l,title=text(p,'title'),goal_ids=sorted(ids),selected_goal_ids=sorted(selected),published_at=ts,snapshot=copy.deepcopy(snapshot)));return {'id':rid}
 gid=p.get('goal_id');require(gid in gids,'Goal is outside this reporting scope.',403)
 g=next(g for g in f.db['goals'] if g['id']==gid);v=max([v for v in f.db['versions'] if v['goal_id']==gid],key=lambda v:v['version_no'])
 record=dict(id=rid,goal_id=gid,created_at=ts)
 if action in ['pushback_assignment','resend_assignment']:
  if action=='pushback_assignment':
   require(v['owner_id']==l and g.get('assignment_state')=='pending','Only the assigned owner can push back a pending remit.',403)
   reason=text(p,'reason');g.update(assignment_state='pushed_back',assignment_reason=reason)
  else:
   require(g.get('assigned_by')==l and g.get('assignment_state')=='pushed_back','Only the assigning leader can resend this remit.',403)
   reason=text(p,'reason');g.update(assignment_state='pending',assignment_response=reason)
  f.db['decisions'].append(dict(record,decision='Assignment pushed back' if action=='pushback_assignment' else 'Assignment resent',rationale=reason,decided_at=ts,decided_by=l))
  return {'goal_id':gid}
 if action=='accept_assignment':
  require(v['owner_id']==l and g.get('assignment_state')=='pending','Only the assigned owner can accept this workstream.',403)
  g.update(assignment_state='accepted',accepted_at=ts);return {'goal_id':gid}
 if action=='record_question':
  assignee=p.get('assigned_to') or v['owner_id'];require(assignee in f.scope(l),'Choose a person in your reporting scope.',403)
  f.db['questions'].append(dict(record,question=text(p,'text'),assigned_to=assignee,asked_by=l,resolved_at=None))
 elif action in ['reply_question','close_question']:
  q=next((q for q in f.db['questions'] if q['id']==p.get('question_id') and q['goal_id']==gid),None);require(q is not None,'Question not found.',404)
  if action=='reply_question':
   require(not q.get('resolved_at'),'This question has already been resolved.')
   f.db['replies'].append(dict(record,question_id=q['id'],author_id=l,text=text(p,'text')))
  else:
   require(l in [q['assigned_to'],q['asked_by']],'Only the asker or assigned owner can resolve this question.',403)
   require(not q.get('resolved_at'),'This question is already resolved.',409)
   q.update(resolved_at=ts,resolved_by=l,resolution=text(p,'text'))
 elif action=='record_decision':f.db['decisions'].append(dict(record,decision=text(p,'text'),rationale=text(p,'rationale'),decided_at=ts,decided_by=l))
 elif action=='record_learning':
  require(v['owner_id']==l,'Only the goal owner records its learning note.',403)
  require(p.get('result') in ['Achieved','Partially achieved','Missed','Still in progress'],'Choose an observed result.')
  f.db['reflections'].append(dict(record,result=p['result'],learning=text(p,'text'),next_step=text(p,'next_step'),author_id=l))
 elif action=='create_followup':
  require(p.get('owner_id') in f.scope(l),'Choose an action owner in your reporting scope.',403);date(p.get('due_on'))
  f.db['followups'].append(dict(record,text=text(p,'text'),owner_id=p['owner_id'],due_on=p['due_on'],created_by=l,completed_at=None))
 elif action=='complete_followup':
  a=next((a for a in f.db['followups'] if a['id']==p.get('id') and a['goal_id']==gid),None)
  require(a is not None and l in [a['owner_id'],a['created_by']],'Only the action owner or creator can complete it.',403)
  a.update(completed_at=ts,completed_by=l)
 elif action=='record_kpi':
  k=next((k for k in f.db['kpis'] if k['id']==p.get('kpi_id') and k['version_id']==g['active_version_id']),None)
  require(k is not None and next(v for v in f.db['versions'] if v['id']==k['version_id'])['owner_id']==l,'Only the owner can report against an approved KPI.',403)
  try:val=float(p.get('value'))
  except (ValueError,TypeError):val=float('nan')
  require(math.isfinite(val),'Enter a finite reading.');observed=p.get('observed_on');require(date(observed)<=date(f.as_of),'Observation cannot be in the future.')
  require(observed>=next(v for v in f.db['versions'] if v['id']==k['version_id'])['starts_on'],'Observation predates this baseline.')
  f.db['kpi_readings'].append(dict(id=rid,kpi_id=k['id'],value=val,observed_at=observed+'T12:00:00Z',recorded_at=ts,recorded_by=l,evidence_note=text(p,'evidence_note')))
 else:require(False,'Unknown leadership command.')
 return {'goal_id':gid,'id':rid}
