"""Durable Supabase repository for the shared synthetic workshop.

The loopback service is the trusted domain/authorization boundary. Supabase is the
sole data store; every request loads committed rows and mutations use revision CAS.
No silent local fallback, service-role key, or credential is sent to the browser.
"""
import json,uuid,hashlib,urllib.request,urllib.error,urllib.parse,threading,copy
import httpx
from concurrent.futures import ThreadPoolExecutor
from fixture_server import Fixture
from demo_mutations import Invalid,require

class RemoteError(Exception):
 def __init__(self,message,status=502):super().__init__(message);self.status=status

class Cloud:
 def __init__(self,config):
  self.config=config
  self.client=httpx.Client(timeout=httpx.Timeout(3.0,connect=2.0),limits=httpx.Limits(max_connections=12,max_keepalive_connections=6),follow_redirects=False)
 def close(self):self.client.close()
 def request(self,action,data=None,raw=None,mime='application/json',params=None):
  try:
   response=self.client.post(self.config['edge_url'],params={'action':action,**(params or {})},content=raw if raw is not None else json.dumps(data or {}).encode(),headers={'Content-Type':mime,'X-Kaika-Capability':self.config['capability']},timeout=30.0 if action in ('upload','download') else self.client.timeout)
   if response.is_error:
    try:message=response.json().get('error','Database request failed')
    except ValueError:message='Database request failed'
    raise RemoteError(message,response.status_code)
   return response.content if action=='download' else response.json()
  except httpx.TimeoutException:
   raise RemoteError('The database took too long to respond. A save may still be finishing. Retry the same action to confirm it safely.',504)
  except httpx.RequestError:
   raise RemoteError('Supabase could not be reached. Check the connection, then retry the same action. No successful save is assumed.',502)
 def upload(self,e,content):
  return self.request('upload',raw=content,mime=e['mime_type'],params={'evidence_id':e['id'],'deliverable_id':e['deliverable_id'],'checkpoint_id':e.get('checkpoint_id') or '', 'leader':e['uploaded_by']})

class Files(dict):
 """Known remote evidence IDs, with only newly uploaded bytes held in memory."""
 def __init__(self,cloud,evidence):
  super().__init__();self.cloud=cloud;self.remote={e['id'] for e in evidence if e.get('object_path') and e.get('upload_state')=='complete'}
 def __contains__(self,key):return key in self.remote or super().__contains__(key)
 def __getitem__(self,key):return super().__getitem__(key) if super().__contains__(key) else self.cloud.request('download',{'evidence_id':key})

def normalized(db):
 for t,rows in db.items():
  for r in rows:r.setdefault('id',str(uuid.uuid5(uuid.NAMESPACE_DNS,t+json.dumps(r,sort_keys=True))))
 return db

def delta(before,after):
 changes={}
 for t,rows in after.items():
  previous={r['id']:r for r in before.get(t,[])};current={r['id']:r for r in rows}
  put=[r for i,r in current.items() if previous.get(i)!=r];remove=list(previous.keys()-current.keys())
  if put or remove:changes[t]={'upsert':put,'remove':remove}
 return changes

class SupabaseRepository:
 def __init__(self,config):self.cloud=Cloud(config);self.executor=ThreadPoolExecutor(max_workers=8)
 def engine(self,snapshot):
  # Reuse the exact validated domain commands and scoped projections used by the demo.
  f=Fixture.__new__(Fixture);f.storage=None;f.lock=threading.RLock();f.people=[p for p in snapshot['people'] if p.get('source_active',True)];f.db=snapshot['db'];f.as_of=snapshot['as_of'];f.scenario=snapshot['scenario'];f.done={};f.files=Files(self.cloud,f.db['evidence'])
  profiles={p['person_id']:p for p in snapshot.get('profiles',[])}
  for p in f.people:p.update(profiles.get(p['id'],{}))
  f.db['checkins'].sort(key=lambda c:c.get('created_at',''),reverse=True)
  return f
 def state(self,f,snapshot,leader):
  result=f.state(leader)
  result['persistence']={'backend':'supabase','revision':snapshot['revision'],'workspace_id':snapshot['workspace_id']}
  result['organization']=snapshot.get('organization')
  result['people'].sort(key=lambda p:(0 if p['id']==leader else 1 if p['manager_id']==leader else 2,p['name'].casefold()))
  return result
 def handle(self,path,query,body,headers):
  try:
   inp=json.loads(body) if path!='/api/upload' else {};q={k:v[0] for k,v in urllib.parse.parse_qs(query).items()};action=inp.get('action');leader=q.get('leader') if path=='/api/upload' else inp.get('leader_id')
   require(action!='demo_scenario','Connected workshop records are persistent. Scenario replacement is available only in the separate offline demo.',403)
   if action=='profile_save':
    from profile_domain import normalize_profile
    payload=normalize_profile(leader,inp.get('data',{}));mid=inp.get('mutation_id');uuid.UUID(mid)
    result=self.cloud.request('profile_save',{**payload,'leader_id':leader,'mutation_id':mid,'request_hash':hashlib.sha256(body).hexdigest()})
    snapshot=self.cloud.request('load');f=self.engine(snapshot)
    return 200,{**result,'_state':self.state(f,snapshot,leader)},{}
   if action=='profile_photos':
    ids=inp.get('data',{}).get('person_ids',[])
    require(isinstance(ids,list) and 0<len(ids)<=24,'Request up to 24 profile images.')
    return 200,{'profiles':self.cloud.request('profile_photos',{'leader_id':leader,'person_ids':ids})},{}
   mutation=path=='/api/upload' or path=='/api/command' and action not in ['state','leaders','session']
   mid=q.get('upload_id') if path=='/api/upload' else inp.get('mutation_id');signature=hashlib.sha256(path.encode()+b'\0'+query.encode()+b'\0'+body).hexdigest()
   prior_future=None
   if mutation:
    require(mid is not None,'Mutation identifier required.');uuid.UUID(mid)
    prior_future=self.executor.submit(self.cloud.request,'lookup',{'mutation_id':mid,'leader_id':leader,'request_hash':signature})
   snapshot=self.cloud.request('load');f=self.engine(snapshot)
   require(action in ('leaders','session') or any(p['id']==leader for p in f.people),'Select an active person in the imported organization.',403)
   if action in ('leaders','session') and snapshot.get('organization'):
    from collections import Counter
    reports=Counter(p['manager_id'] for p in f.people)
    current={g.get('active_version_id') or max((v for v in f.db['versions'] if v['goal_id']==g['id']),key=lambda v:v['version_no'])['id'] for g in f.db['goals']}
    owned=Counter(v['owner_id'] for v in f.db['versions'] if v['id'] in current)
    roster=[dict(id=p['id'],name=p['name'],title=p['title'],team=p['team'],direct_reports=reports[p['id']],goal_count=owned[p['id']]) for p in sorted(f.people,key=lambda p:p['name'].casefold())]
    result={'leaders':roster,'source_date':snapshot['organization']['source_as_of'],'organization':snapshot['organization'],'preferred_leader_id':snapshot['organization']['preferred_leader_id']}
    if action=='session':
     leader=leader if any(p['id']==leader for p in f.people) else result['preferred_leader_id']
     result['leader_id']=leader;result['state']=self.state(f,snapshot,leader)
    return 200,result,{}
   if mutation:
    require(mid is not None,'Mutation identifier required.');uuid.UUID(mid)
    prior=prior_future.result()
    if prior is not None:return 200,{**prior['result'],'_state':self.state(f,snapshot,leader)},{}
   if path=='/api/download':
    e=next((e for e in f.visible_evidence(leader) if e['id']==inp.get('evidence_id') and e['upload_state']=='complete'),None)
    require(e is not None,'Evidence is outside this leader’s reporting scope.',403)
    return 200,self.cloud.request('download',{'evidence_id':e['id']}),{'Content-Type':e['mime_type'],'Content-Disposition':"attachment; filename*=UTF-8''"+urllib.parse.quote(e['original_name'])}
   if action=='state':return 200,self.state(f,snapshot,leader),{}
   before=copy.deepcopy(f.db)
   status,result,response_headers=f._handle(path,query,body,headers)
   if status>=400:return status,result,response_headers
   if mutation:
    for e in f.db['evidence']:
     if dict.__contains__(f.files,e['id']):e.update(self.cloud.upload(e,dict.__getitem__(f.files,e['id'])))
    normalized(f.db)
    committed=self.cloud.request('commit',{'revision':snapshot['revision'],'mutation_id':mid,'leader_id':leader,'request_hash':signature,'changes':delta(before,f.db),'result':result})
    result=committed['result']
    # The CAS commit succeeded. Return its scoped projection in the same response.
    # Replayed commits can describe an older operation: reload to avoid stale UI.
    if committed.get('replayed'):
     snapshot=self.cloud.request('load');f=self.engine(snapshot)
    else:snapshot['revision']=committed['revision']
    result={**result,'_state':self.state(f,snapshot,leader)}
   if action=='state':result=self.state(f,snapshot,leader)
   return status,result,response_headers
  except (RemoteError,Invalid) as e:return e.status,{'error':str(e)},{}
  except (ValueError,KeyError,StopIteration):return 400,{'error':'Invalid workshop request. No successful save is assumed.'},{}
