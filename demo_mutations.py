"""Validated commands for synthetic local walkthroughs only."""
import uuid,copy
class Invalid(Exception):
 def __init__(self,message,status=400):super().__init__(message);self.status=status

def require(condition,message,status=400):
 if not condition:raise Invalid(message,status)

def delivery_context(f,leader,p):
 s=f.state(leader)
 d=next((d for d in s['deliverables'] if d['id']==p.get('deliverable_id')),None)
 if d is None:
  d=next((a['deliverable'] for a in s.get('assigned_work',[]) if a['deliverable']['id']==p.get('deliverable_id') and a['deliverable']['owner_id']==leader),None)
 require(d is not None,'Deliverable is outside this leader’s scope.',403)
 v=next(v for v in f.db['versions'] if v['id']==d['version_id'])
 g=next(g for g in f.db['goals'] if g['id']==v['goal_id'])
 require(g['active_version_id']==v['id'],'Approve the goal baseline before updating delivery.')
 return next(d0 for d0 in f.db['deliverables'] if d0['id']==d['id']),v,g

def update_delivery(f,leader,p):
 from fixture_server import now
 d,v,g=delivery_context(f,leader,p)
 require(p.get('status') in ['not_started','in_progress','at_risk','blocked','unknown'],'Choose an operational status. Completion comes from accepted evidence.')
 require(bool(p.get('reason','').strip()),'Explain the status change.')
 d.update(demo_signal=p['status'],status_reason=p['reason'].strip(),status_updated_at=now(),status_updated_by=leader)
 return {'goal_id':g['id'],'deliverable_id':d['id']}

def evidence_note(f,leader,p):
 from fixture_server import now
 import hashlib
 d,v,g=delivery_context(f,leader,p)
 require(leader in [d['owner_id'],v['owner_id']],'Switch to the owner to submit evidence.',403)
 text=p.get('text','').strip();require(len(text)>=20,'Provide at least 20 characters describing the evidence and result.')
 cid=p.get('checkpoint_id') or None
 require(cid is None or any(c['id']==cid and c['deliverable_id']==d['id'] for c in f.db['checkpoints']),'Checkpoint does not belong to this deliverable.')
 eid=str(uuid.uuid4());content=('SYNTHETIC DEMO EVIDENCE\n'+text+'\n').encode()
 f.files[eid]=content
 f.db['evidence'].append(dict(id=eid,deliverable_id=d['id'],checkpoint_id=cid,original_name='evidence-note.txt',mime_type='text/plain',byte_size=len(content),sha256=hashlib.sha256(content).hexdigest(),scan_state='pending',upload_state='complete',created_at=now(),uploaded_by=leader))
 return {'goal_id':g['id'],'evidence_id':eid}

def validate_acceptance(f,leader,p,g):
 c=next((c for c in f.db['checkpoints'] if c['id']==p.get('checkpoint_id')),None)
 require(c is not None,'Checkpoint not found.',404)
 d=next(d for d in f.db['deliverables'] if d['id']==c['deliverable_id'])
 require(d['version_id']==g['active_version_id'],'Only checkpoints in the approved goal baseline can be reviewed.')
 require(c['reviewer_id']==leader and d['owner_id']!=leader,'The designated independent reviewer must make this decision.',403)
 e=next((e for e in f.db['evidence'] if e['id']==p.get('evidence_id')),None)
 require(e is not None and e['deliverable_id']==d['id'] and (not e['checkpoint_id'] or e['checkpoint_id']==c['id']) and e['upload_state']=='complete' and e['id'] in f.files,'Choose completed evidence for this checkpoint.')
 require(isinstance(p.get('accepted'),bool),'A review decision is required.')
 require(p.get('file_safety_acknowledged') is True and bool(p.get('reason','').strip()),'Review the file and record a reason.')
 return c

def validate_upload(f,leader,deliverable,checkpoint,body,mime):
 d,v,g=delivery_context(f,leader,{'deliverable_id':deliverable})
 require(leader in [d['owner_id'],v['owner_id']],'Switch to the owner to upload evidence.',403)
 require(checkpoint is None or any(c['id']==checkpoint and c['deliverable_id']==deliverable for c in f.db['checkpoints']),'Checkpoint does not belong to deliverable.')
 require(0<len(body)<=20*1024*1024,'Choose a nonempty file up to 20 MiB.')
 require(mime in ['text/plain','text/csv','application/pdf','image/png','image/jpeg','application/vnd.openxmlformats-officedocument.wordprocessingml.document','application/vnd.openxmlformats-officedocument.wordprocessingml.sheet','application/vnd.openxmlformats-officedocument.presentationml.presentation'],'Unsupported file type.')
 return d

def new_version(f,leader,g,v):
 require(v['owner_id']==leader,'Only the owner can propose a new version.',403)
 require(v['state']!='draft','An editable draft already exists.')
 nv=copy.deepcopy(v);nv.update(id=str(uuid.uuid4()),version_no=v['version_no']+1,state='draft',edit_revision=0)
 f.db['versions'].append(nv)
 for key in ['measures','allocations','kpis']:
  for row in list(f.db[key]):
   if row['version_id']==v['id']:
    clone=copy.deepcopy(row);clone.update(id=str(uuid.uuid4()),version_id=nv['id']);f.db[key].append(clone)
 for d in list(f.db['deliverables']):
  if d['version_id']==v['id']:
   clone=copy.deepcopy(d);clone.update(id=str(uuid.uuid4()),version_id=nv['id'],demo_signal='in_progress');f.db['deliverables'].append(clone)
   for c in list(f.db['checkpoints']):
    if c['deliverable_id']==d['id']:
     cc=copy.deepcopy(c);cc.update(id=str(uuid.uuid4()),deliverable_id=clone['id']);f.db['checkpoints'].append(cc)
 return {'goal_id':g['id']}
