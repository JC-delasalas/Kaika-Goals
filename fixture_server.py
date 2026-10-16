import uuid,json,copy,datetime,hashlib,urllib.parse,base64,threading,os
from pathlib import Path
from goal_contract import basis,validate_plan
import leadership_domain as leadership
import support_domain as support
from demo_mutations import Invalid,require,update_delivery,evidence_note,validate_acceptance,validate_upload,new_version
def uid(x):return str(uuid.uuid5(uuid.NAMESPACE_DNS,'kaika-fixture-'+x))
def now():return datetime.datetime.now(datetime.timezone.utc).replace(year=2026,month=10,day=27).isoformat()
class Fixture:
 def __init__(self,storage=None,default_scenario='mixed'):
  self.storage=Path(storage) if storage else None
  self.lock=threading.RLock()
  self.people=[
   dict(id=uid('ada'),name='Ada Reyes',title='Director, Data',team='Data & Analytics',manager_id=uid('sam'),org_id=uid('data')),
   dict(id=uid('bea'),name='Bea Santos',title='Analytics Lead',team='Data & Analytics',manager_id=uid('ada'),org_id=uid('data')),
   dict(id=uid('ana'),name='Ana Cruz',title='Data Analyst',team='Data & Analytics',manager_id=uid('bea'),org_id=uid('data')),
   dict(id=uid('dan'),name='Dan Tan',title='Director, Customer',team='Customer Experience',manager_id=uid('sam'),org_id=uid('customer')),
   dict(id=uid('sam'),name='Sam Lee',title='Executive',team='Leadership',manager_id=None,org_id=uid('leadership'))]
  for p in self.people:p.update(worker_type='Employee',source_fte=1,site_weekly_hours=40,capacity_verified=False,observed_at='2026-09-14')
  self.db={k:[] for k in ['goals','versions','measures','readings','deliverables','checkpoints','evidence','acceptances','allocations','approvals','checkins','portfolios','portfolio_goals','questions','decisions','reviews']}
  leadership.ensure(self);support.ensure(self)
  for k in ['strategies','pillars']:self.db.setdefault(k,[])
  self.files={};self.done={}
  from scenarios import seed
  seed(self,default_scenario)
  if self.storage and self.storage.exists():
   stored=json.loads(self.storage.read_text())
   self.db=stored['db'];self.files={k:base64.b64decode(v) for k,v in stored['files'].items()};self.scenario=stored['scenario'];self.as_of=stored['as_of'];self.done=stored.get('done',{})
  leadership.ensure(self);support.ensure(self)
  self.people=[p for p in self.people if p['id'] in {uid(k) for k in ['ada','bea','ana','dan','sam']}]
  for k in ['strategies','pillars']:self.db.setdefault(k,[])
  if self.scenario=='strategy':
   from strategy_workshop import people
   people(self)
  from scenarios import upgrade_walkthrough
  upgrade_walkthrough(self)
 def persist(self):
  if not self.storage:return
  payload=dict(db=self.db,files={k:base64.b64encode(v).decode() for k,v in self.files.items()},scenario=self.scenario,as_of=self.as_of,done=self.done)
  temp=self.storage.with_suffix('.tmp');temp.write_text(json.dumps(payload));os.chmod(temp,0o600);temp.replace(self.storage)

 def scope(self,l):
  ids={l};changed=True
  while changed:
   n={p['id'] for p in self.people if p['manager_id'] in ids};changed=bool(n-ids);ids|=n
  return ids
 def new_goal(self,owner,title,level,parent):
  gid=str(uuid.uuid4());vid=str(uuid.uuid4());p=next(p for p in self.people if p['id']==owner)
  g=dict(id=gid,parent_id=parent,org_id=p['org_id'],level=level,origin='initiated',synthetic=True,active_version_id=None)
  self.db['goals'].append(g)
  approver=p['manager_id']
  self.db['versions'].append(dict(id=vid,goal_id=gid,version_no=1,title=title,description='Synthetic fixture. No real employee records.',owner_id=owner,approver_id=approver,approver_name=next((p['name'] for p in self.people if p['id']==approver),'Not assigned'),period_id=uid('period'),starts_on='2026-10-27',ends_on='2026-12-18',priority='fuel',category='Productivity',cadence='weekly',success_basis='outcome',state='draft',edit_revision=0))
  return g
 def assigned_work(self,l,visible_versions):
  """Exact assigned leaves only. Never grant access to their parent goal or siblings."""
  from scenarios import delivery_metric
  active={g['active_version_id'] for g in self.db['goals'] if g.get('active_version_id')}
  scope=self.scope(l);names={p['id']:p['name'] for p in self.people};result=[]
  for d in self.db['deliverables']:
   if d['owner_id'] not in scope or d['version_id'] in visible_versions or d['version_id'] not in active:continue
   v=next(v for v in self.db['versions'] if v['id']==d['version_id'])
   item={'deliverable':copy.deepcopy(d),'assigned_by':names.get(v['owner_id'],'Goal owner'),'progress':delivery_metric(self.db,d,self.as_of,active)}
   for key in ['checkpoints','evidence','acceptances']:item[key]=copy.deepcopy([x for x in self.db[key] if x['deliverable_id']==d['id']])
   for c in item['checkpoints']:c['reviewer_name']=names.get(c['reviewer_id'],'Designated reviewer')
   result.append(item)
  return result
 def assigned_allocations(self,l,visible_versions):
  scope=self.scope(l);active={g['active_version_id'] for g in self.db['goals'] if g.get('active_version_id')}
  names={p['id']:p['name'] for p in self.people};versions={v['id']:v for v in self.db['versions']}
  return [dict(id=a['id'],worker_id=a['worker_id'],month=a['month'],allocation_pct=a['allocation_pct'],assignment_label='Commitment assigned by '+names.get(versions[a['version_id']]['owner_id'],'goal owner')) for a in self.db['allocations'] if a['worker_id'] in scope and a['version_id'] in active and a['version_id'] not in visible_versions]
 def visible_evidence(self,l):
  s=self.state(l)
  return s['evidence']+[e for a in s.get('assigned_work',[]) for e in a['evidence']]
 def state(self,l):
  scope=self.scope(l);gids={v['goal_id'] for v in self.db['versions'] if v['owner_id'] in scope};vids={v['id'] for v in self.db['versions'] if v['goal_id'] in gids};dids={d['id'] for d in self.db['deliverables'] if d['version_id'] in vids}
  x={k:copy.deepcopy(v) for k,v in self.db.items()}
  x['goals']=[g for g in x['goals'] if g['id'] in gids];x['versions']=[v for v in x['versions'] if v['id'] in vids]
  for key in ['measures','deliverables','allocations','approvals']:x[key]=[r for r in x[key] if r['version_id'] in vids]
  for key in ['checkpoints','evidence','acceptances']:x[key]=[r for r in x[key] if r['deliverable_id'] in dids]
  for key in ['checkins','questions','decisions']:x[key]=[r for r in x[key] if r['goal_id'] in gids]
  mids={m['id'] for m in x['measures']};x['readings']=[r for r in x['readings'] if r['measure_id'] in mids]
  x['people']=[copy.deepcopy(p) for p in self.people if p['id'] in scope]
  profiles={p['person_id']:p for p in x.pop('profiles',[])}
  for p in x['people']:
   profile=profiles.get(p['id'],{});p.update({k:v for k,v in profile.items() if k!='photo_data_url'})
   if profile:p['has_photo']=bool(profile.get('photo_data_url'))
   if p['manager_id'] not in scope:p['manager_id']=None
  x['portfolios']=[p for p in x['portfolios'] if p['owner_id'] in scope];pids={p['id'] for p in x['portfolios']}
  x['portfolio_goals']=[p for p in x['portfolio_goals'] if p['portfolio_id'] in pids and p['goal_id'] in gids]
  x['reviews']=[r for r in x['reviews'] if r['facilitator_id']==l]
  leadership.scope_extra(x,l,gids,vids)
  x['support_requests']=support.project(self,l,gids);x['support_contacts']=support.contacts(self,l)
  labels={v.get('pillar') for v in x['versions']}
  x['pillars']=[p for p in x.get('pillars',[]) if p['title'] in labels]
  strategy_ids={p['strategy_id'] for p in x['pillars']}
  x['strategies']=[s for s in x.get('strategies',[]) if s['id'] in strategy_ids]
  for g in x['goals']:
   g['has_workstreams']=any(c['parent_id']==g['id'] for c in self.db['goals'])
   if g['parent_id'] not in gids:
    g['alignment_hidden']=bool(g['parent_id']);g['parent_id']=None
  from scenarios import derive,PRESETS
  x=derive(x,self.as_of);x['assigned_work']=self.assigned_work(l,vids);x['assigned_allocations']=self.assigned_allocations(l,vids);x['demo']={'preset':self.scenario,'label':PRESETS[self.scenario],'as_of':self.as_of}
  return x
 def handle(self,path,query,body,headers):
  with self.lock:
   before=(copy.deepcopy(self.db),self.files.copy(),self.done.copy(),self.scenario,self.as_of)
   try:
    result=self._handle(path,query,body,headers)
    if result[0]<400:
     is_read=path=='/api/download' or path=='/api/command' and json.loads(body).get('action') in ['state','leaders']
     if not is_read:self.persist()
    else:self.db,self.files,self.done,self.scenario,self.as_of=before
    return result
   except Invalid as e:
    self.db,self.files,self.done,self.scenario,self.as_of=before
    return e.status,{'error':str(e)},{}
   except Exception:
    self.db,self.files,self.done,self.scenario,self.as_of=before
    raise
 def _handle(self,path,query,body,headers):
  try:
   q={k:v[0] for k,v in urllib.parse.parse_qs(query).items()}
   if path=='/api/upload':
    l=q['leader'];d=validate_upload(self,l,q['deliverable_id'],q.get('checkpoint_id'),body,headers.get('Content-Type'))
    eid=q['upload_id'];name=urllib.parse.unquote(headers.get('X-File-Name','test.txt'))
    existing=next((e for e in self.db['evidence'] if e['id']==eid),None)
    require(not existing or existing['deliverable_id']==d['id'] and existing['sha256']==hashlib.sha256(body).hexdigest(),'Upload retry does not match the original file.',409)
    self.files[eid]=body
    if not any(e['id']==eid for e in self.db['evidence']):
     self.db['evidence'].append(dict(id=eid,deliverable_id=d['id'],checkpoint_id=q.get('checkpoint_id'),original_name=name,mime_type=headers.get('Content-Type'),byte_size=len(body),sha256=hashlib.sha256(body).hexdigest(),scan_state='pending',upload_state='complete',created_at=now(),uploaded_by=l))
    return 200,{'id':eid,'complete':True},{}
   inp=json.loads(body);l=inp.get('leader_id');action=inp.get('action');p=inp.get('data',{})
   if path=='/api/download':
    e=next((e for e in self.visible_evidence(l) if e['id']==inp['evidence_id']),None)
    require(e is not None,'Evidence is outside this leader’s scope.',403)
    return 200,self.files[e['id']],{'Content-Type':e['mime_type'],'Content-Disposition':"attachment; filename*=UTF-8''"+urllib.parse.quote(e['original_name'])}
   if action=='leaders':return 200,{'leaders':[dict(p,goal_count=sum(v['owner_id']==p['id'] for v in self.db['versions'])) for p in self.people if True],'source_date':'2026-09-14'},{}
   if action=='state':return 200,self.state(l),{}
   if action=='profile_photos':
    ids=p.get('person_ids',[]);require(len(ids)<=24 and set(ids)<=self.scope(l),'Profile is outside this leader scope',403)
    return 200,{'profiles':[dict(r,revision=r['profile_revision']) for r in self.db.get('profiles',[]) if r['person_id'] in ids]},{}
   if action=='demo_scenario':
    from scenarios import seed
    seed(self,p['preset'])
    return 200,{'preset':self.scenario},{}

   cache_key=str(l)+':'+str(inp.get('mutation_id'))
   if inp.get('mutation_id') and cache_key in self.done:return 200,self.done[cache_key],{}
   if action=='profile_save':
    from profile_domain import normalize_profile
    profile=normalize_profile(l,p);rows=self.db.setdefault('profiles',[]);old=next((r for r in rows if r['person_id']==l),{})
    require(old.get('profile_revision',0)==profile.pop('expected_revision'),'Your profile changed. Reopen the editor.',409)
    profile.update(id=l,profile_revision=old.get('profile_revision',0)+1);self.db['profiles']=[r for r in rows if r['person_id']!=l]+[profile];result={'person_id':l}
   elif action in support.ACTIONS:result=support.handle(self,l,action,p)
   elif action in leadership.ACTIONS:result=leadership.handle(self,l,action,p)
   elif action in ['demo_delivery_status','demo_evidence_note']:
    result=update_delivery(self,l,p) if action=='demo_delivery_status' else evidence_note(self,l,p)
   elif action=='create_goal':
    if p['owner_id'] not in self.scope(l):return 403,{'error':'Owner outside scope'},{}
    require(str(p.get('title','')).strip(),'Enter a goal title.')
    parent=p.get('parent_id') or None
    require(p['level'] in ['corporate','department','team'],'Choose an organizational level.')
    if parent:
     pg=next((g for g in self.state(l)['goals'] if g['id']==parent),None)
     require(pg is not None and (p['level']=='department' and pg['level']=='corporate' or p['level']=='team' and pg['level'] in ['department','team']),'Parent must match the organizational level.')
    if p['owner_id']!=l:
     require(parent and any(v['goal_id']==parent and v['owner_id']==l for v in self.db['versions']),'Assign a workstream beneath a goal you own.')
    g=self.new_goal(p['owner_id'],p['title'],p['level'],parent);g.update(hierarchy_model='workstream-delivery',node_kind='workstream' if parent else 'objective');nv=self.db['versions'][-1]
    nv.update(description='',starts_on='',ends_on='',success_basis='metric',registration_contract=2,category=str(p.get('category') or nv['category'])[:120],pillar=str(p.get('pillar') or '')[:200])
    if parent:nv['pillar']=max((v for v in self.db['versions'] if v['goal_id']==parent),key=lambda v:v['version_no']).get('pillar','')
    if p['owner_id']!=l:g.update(origin='inherited',assignment_state='pending',assigned_by=l);nv.update(approver_id=l,approver_name=next(p['name'] for p in self.people if p['id']==l))
    result={'goal_id':g['id']}
   elif action=='create_portfolio':
    require(set(p.get('goals',[]))<={g['id'] for g in self.state(l)['goals']},'Portfolio goals must be in your reporting scope.',403)
    pid=str(uuid.uuid4());self.db['portfolios'].append(dict(id=pid,title=p['title'],description=p['description'],owner_id=l))
    for gid in p.get('goals',[]):self.db['portfolio_goals'].append(dict(portfolio_id=pid,goal_id=gid))
    result={'id':pid}
   else:
    g=next(g for g in self.state(l)['goals'] if g['id']==p['goal_id']);v=sorted([v for v in self.db['versions'] if v['goal_id']==g['id']],key=lambda x:x['version_no'])[-1]
    if action=='new_version':result=new_version(self,l,g,v)
    elif action=='checkin':
     require(v['owner_id']==l and p.get('health') in ['on_track','at_risk','blocked','unknown'],'Only the owner can record a valid check-in.',403)
     require(p.get('reason','').strip(),'Explain the update.')
     # created_at is the legacy workshop clock used by cadence and frozen reviews.
     # Keep it monotonic across real midnights; retain the real audit time separately.
     stamp=datetime.datetime.fromisoformat(now())
     prior=[datetime.datetime.fromisoformat(c['created_at'].replace('Z','+00:00')) for c in self.db['checkins'] if c['goal_id']==g['id']]
     if prior:stamp=max(stamp,max(prior)+datetime.timedelta(microseconds=1))
     self.db['checkins'].insert(0,dict(id=str(uuid.uuid4()),goal_id=g['id'],author_id=l,health=p['health'],reason=p['reason'],eta=p.get('eta'),created_at=stamp.isoformat(),recorded_at=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    elif action=='save_draft':
     require(v['owner_id']==l and v['state']=='draft','Only the owner can edit a draft.',403)
     require(not p.get('deliverables') or g.get('hierarchy_model')!='workstream-delivery' or g.get('node_kind')=='workstream','Attach deliverables to a workstream beneath this objective.')
     require(g.get('assignment_state') not in ['pending','pushed_back'],'Accept the inherited remit before editing setup.')
     require(v['edit_revision']==p.get('edit_revision'),'This draft has changed. Refresh and try again.',409)
     require(p.get('success_basis',basis(v)) in ['delivery','outcome','metric','combined'],'Choose a valid success basis.')
     if p.get('registration_contract')==2:v['registration_contract']=2
     v['success_basis']=p.get('success_basis',basis(v));v['pillar']=str(p.get('pillar',v.get('pillar','')))[:120]
     for k in ['title','description','starts_on','ends_on','priority','category','cadence']:v[k]=p[k]
     v['edit_revision']+=1
     oldd={d['id'] for d in self.db['deliverables'] if d['version_id']==v['id']}
     for key in ['deliverables','measures','allocations','kpis']:self.db[key]=[d for d in self.db[key] if d['version_id']!=v['id']]
     self.db['checkpoints']=[c for c in self.db['checkpoints'] if c['deliverable_id'] not in oldd]
     for k in p.get('kpis',[]):
      kc={key:value for key,value in k.items() if key not in ['id','version_id']}
      self.db['kpis'].append(dict(kc,id=str(uuid.uuid4()),version_id=v['id']))
     for m in p['measures']:self.db['measures'].append(dict(m,id=str(uuid.uuid4()),version_id=v['id'],source_definition=m['source']))
     delivery_ids={}
     for d in p['deliverables']:
      did=str(uuid.uuid4());delivery_ids[d.get('id') or d.get('client_id')]=did
      dc={k:vv for k,vv in d.items() if k not in ['id','version_id','checkpoints']};self.db['deliverables'].append(dict(dc,id=did,version_id=v['id']))
      for c in d['checkpoints']:
       cc={k:vv for k,vv in c.items() if k not in ['id','deliverable_id','reviewer_id']}
       self.db['checkpoints'].append(dict(cc,id=str(uuid.uuid4()),deliverable_id=did,reviewer_id=v['approver_id']))
     for a in p.get('allocations',[]):
      ac={k:value for k,value in a.items() if k not in ['id','version_id','deliverable_id']}
      linked=a.get('deliverable_id')
      require(not linked or linked in delivery_ids,'A resource references a removed or unrelated deliverable.')
      self.db['allocations'].append(dict(ac,id=str(uuid.uuid4()),version_id=v['id'],deliverable_id=delivery_ids.get(linked)))
    elif action=='submit':
     require(v['owner_id']==l and v['state']=='draft','Only the owner can submit a draft.',403)
     require(g.get('assignment_state') not in ['pending','pushed_back'],'Accept this inherited workstream before submitting its breakdown.')
     validate_plan(self,v)
     v['state']='submitted'
    elif action=='approve':
     if v['approver_id']!=l:return 403,{'error':'Designated approver required'},{}
     require(v['state']=='submitted' and not any(a['version_id']==v['id'] for a in self.db['approvals']),'This version is not awaiting approval.',409)
     require(p.get('decision') in ['approved','returned'] and p.get('reason','').strip(),'Provide a decision and reason.')
     if p['decision']=='approved':validate_plan(self,v)
     self.db['approvals'].append(dict(id=str(uuid.uuid4()),version_id=v['id'],decision=p['decision'],reason=p['reason'],approver_id=l,decided_at=now()))
     if p['decision']=='approved':next(g for g in self.db['goals'] if g['id']==v['goal_id'])['active_version_id']=v['id']
    elif action=='accept_checkpoint':
     c=validate_acceptance(self,l,p,g)
     self.db['acceptances'].append(dict(p,id=str(uuid.uuid4()),deliverable_id=c['deliverable_id'],reviewer_id=l,decided_at=now()))
    elif action=='reading':
     from outcome_metrics import record_reading
     record_reading(self,l,p,g)
    elif action in ['decision','question','publish_review']:
     rid=str(uuid.uuid4());self.db['reviews'].append(dict(id=rid,facilitator_id=l,title='Fixture review',published_at=now() if action=='publish_review' else None,snapshot={'text':p['text']}))
     if action=='decision':self.db['decisions'].append(dict(id=str(uuid.uuid4()),goal_id=g['id'],decision=p['text'],rationale=p['rationale'],decided_at=now()))
     if action=='question':self.db['questions'].append(dict(id=str(uuid.uuid4()),goal_id=g['id'],question=p['text'],assigned_to=v['owner_id'],asked_by=l,resolved_at=None))
    elif action=='resolve_question':
     q=next((q for q in self.db['questions'] if q['id']==p['question_id'] and q['goal_id']==g['id']),None)
     require(q is not None and l in [q['asked_by'],q['assigned_to']],'Only the asker or assigned owner can resolve this question.',403)
     q['resolved_at']=now()
    else:return 400,{'error':'Not included in this UI fixture test'},{}
    result={'goal_id':g['id']}
   if inp.get('mutation_id'):self.done[cache_key]=result
   return 200,result,{}
  except (KeyError,StopIteration,ValueError):return 403,{'error':'Record outside fixture scope or invalid request'},{}
