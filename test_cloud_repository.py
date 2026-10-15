import unittest,json,copy,uuid
from concurrent.futures import ThreadPoolExecutor
from fixture_server import Fixture,uid
from supabase_repository import SupabaseRepository,normalized
class CloudMock:
 def __init__(self):
  f=Fixture(None,default_scenario='strategy');self.calls=[];self.saved={};self.snapshot={'people':f.people,'db':normalized(f.db),'as_of':f.as_of,'scenario':f.scenario,'revision':1,'workspace_id':'test','organization':{'source_as_of':'2026-10-01','preferred_leader_id':uid('ada')}}
 def request(self,action,data=None):
  self.calls.append(action)
  if action=='load':return copy.deepcopy(self.snapshot)
  if action=='lookup':return self.saved.get(data['mutation_id'])
  if action=='commit':
   assert data['revision']==self.snapshot['revision']
   for t,c in data['changes'].items():
    rows={r['id']:r for r in self.snapshot['db'][t]}
    for i in c['remove']:rows.pop(i,None)
    rows.update({r['id']:r for r in c['upsert']});self.snapshot['db'][t]=list(rows.values())
   self.snapshot['revision']+=1;self.saved[data['mutation_id']]={'result':data['result']}
   return {'revision':self.snapshot['revision'],'result':data['result']}
class RepositoryTests(unittest.TestCase):
 def setUp(self):self.r=SupabaseRepository.__new__(SupabaseRepository);self.r.cloud=CloudMock();self.r.executor=ThreadPoolExecutor(max_workers=2)
 def tearDown(self):self.r.executor.shutdown()
 def call(self,action,who='ada',**extra):return self.r.handle('/api/command','',json.dumps({'action':action,'leader_id':uid(who),**extra}).encode(),{})
 def test_session_one_read_and_scope(self):
  status,s,_=self.call('session');self.assertEqual(status,200);self.assertEqual(self.r.cloud.calls,['load']);self.assertTrue(s['state']['goals'])
  foreign={g['id'] for g in self.call('state','dan')[1]['goals']};self.assertFalse(foreign&{g['id'] for g in s['state']['goals']})
 def test_save_returns_committed_scoped_state_and_retry_deduplicates(self):
  gid=self.call('state')[1]['goals'][0]['id'];mid=str(uuid.uuid4());args={'mutation_id':mid,'data':{'goal_id':gid,'text':'Synthetic repository verification','assigned_to':uid('ada')}}
  status,result,_=self.call('record_question',**args);self.assertEqual(status,200,result);self.assertEqual(result['_state']['persistence']['revision'],2)
  status,replayed,_=self.call('record_question',**args);self.assertEqual(status,200)
  self.assertEqual(len([q for q in replayed['_state']['questions'] if q['question']=='Synthetic repository verification']),1);self.assertEqual(self.r.cloud.calls.count('commit'),1)
