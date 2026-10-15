"""Explicit sharing contracts, independent of accountability and progress."""
import copy,uuid,datetime
from demo_mutations import require
ACTIONS={'support_create','support_accept','support_decline','support_submit','support_return','support_complete','support_cancel'}
PUBLIC=('id','title','context','criteria','due_on','requester_id','owner_id','requester_name','owner_name','requester_team','owner_team','state','revision','created_at','history')
def ensure(f):f.db.setdefault('support_requests',[])
def contacts(f,l):
 me=next((p for p in f.people if p['id']==l),None)
 if me and me.get('source_system')=='workday':
  # Shared cost-center names do not define reporting teams. Peers can support one another.
  excluded=f.scope(l);people={p['id']:p for p in f.people};parent=me.get('manager_id')
  while parent and parent not in excluded:
   excluded.add(parent);parent=people.get(parent,{}).get('manager_id')
  return [dict(id=p['id'],name=p['name'],team=p['team']) for p in f.people if p['id'] not in excluded]
 return [dict(id=p['id'],name=p['name'],team=p['team']) for p in f.people if me and p['org_id']!=me['org_id'] and p['id']!=l]
def project(f,l,gids):
 scope=f.scope(l);rows=[]
 for r in f.db.get('support_requests',[]):
  if not {r['requester_id'],r['owner_id']}&scope:continue
  x={k:copy.deepcopy(r[k]) for k in PUBLIC}
  for side in ['requester','delivery']:
   if r.get(side+'_goal_id') in gids:
    x[side+'_goal_id']=r[side+'_goal_id'];x[side+'_version_id']=r[side+'_version_id']
  x['overdue']=r['due_on']<f.as_of and r['state'] not in ['completed','declined','cancelled']
  rows.append(x)
 return rows
def text(p,k):
 v=p.get(k,'');require(isinstance(v,str) and 0<len(v.strip())<=4000,'Enter '+k.replace('_',' ')+' (1–4,000 characters).');return v.strip()
def owned_baseline(f,l,gid):
 g=next((g for g in f.db['goals'] if g['id']==gid),None)
 v=next((v for v in f.db['versions'] if g and v['id']==g.get('active_version_id')),None)
 require(v is not None and v['owner_id']==l,'Choose an approved goal you own.',403)
 return v
def handle(f,l,action,p):
 from fixture_server import now
 ensure(f);ts=now()
 if action=='support_create':
  v=owned_baseline(f,l,p.get('goal_id'));owner=p.get('owner_id')
  require(owner in {c['id'] for c in contacts(f,l)},'Choose a named owner from another team.',403)
  due=p.get('due_on','')
  try:datetime.date.fromisoformat(due)
  except (TypeError,ValueError):require(False,'Enter a valid due date.')
  require(f.as_of<=due<=v['ends_on'],'Due date must be on or after the demo date and within your approved goal period.')
  people={x['id']:x for x in f.people}
  r=dict(id=str(uuid.uuid4()),title=text(p,'title'),context=text(p,'context'),criteria=text(p,'criteria'),due_on=due,requester_id=l,owner_id=owner,requester_goal_id=v['goal_id'],requester_version_id=v['id'],state='requested',revision=0,created_at=ts,history=[])
  for side,who in [('requester',l),('owner',owner)]:
   r[side+'_name']=people[who]['name'];r[side+'_team']=people[who]['team']
  f.db['support_requests'].append(r);note='Request shared with its named owner.'
 else:
  r=next((r for r in f.db['support_requests'] if r['id']==(p.get('id') or p.get('support_id'))),None)
  require(r is not None and l in [r['requester_id'],r['owner_id']],'Supporting request unavailable.',403)
  try:revision=int(p.get('revision',-1))
  except (TypeError,ValueError):revision=-1
  require(revision==r['revision'],'This request changed. Refresh before recording your decision.',409)
  rules={'support_accept':('owner_id',['requested'],'accepted'),'support_decline':('owner_id',['requested'],'declined'),'support_submit':('owner_id',['accepted'],'submitted'),'support_return':('requester_id',['submitted'],'accepted'),'support_complete':('requester_id',['submitted'],'completed'),'support_cancel':('requester_id',['requested','accepted','submitted'],'cancelled')}
  role,states,target=rules[action]
  require(r[role]==l,'Only the named '+('receiving owner' if role=='owner_id' else 'requester')+' can take this action.',403)
  require(r['state'] in states,'This action is no longer available for the request.',409)
  note=text(p,'text')
  if action=='support_accept' and p.get('delivery_goal_id'):
   v=owned_baseline(f,l,p['delivery_goal_id']);r.update(delivery_goal_id=v['goal_id'],delivery_version_id=v['id'])
  r['state']=target;r['revision']+=1
 r['history'].append(dict(action=action,state=r['state'],author_id=l,author_name=next(x['name'] for x in f.people if x['id']==l),at=ts,text=note))
 return {'id':r['id'],'revision':r['revision']}
