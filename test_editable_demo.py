import unittest,json,uuid,tempfile
from pathlib import Path
from fixture_server import Fixture,uid
from scenarios import seed
class EditableDemo(unittest.TestCase):
 def call(self,f,action,leader='bea',data=None,mid=None):
  return f.handle('/api/command','',json.dumps(dict(action=action,leader_id=uid(leader),data=data or {},mutation_id=mid or str(uuid.uuid4()))).encode(),{})
 def setup_flow(self,f):
  seed(f,'walkthrough');s=f.state(uid('bea'));g=s['goals'][0];ds=s['deliverables'];return g,ds
 def test_full_flow_and_rejection(self):
  f=Fixture();g,ds=self.setup_flow(f);d=ds[0]
  def progress():return f.state(uid('ada'))['progress'][0]
  self.assertEqual(progress()['delivery_pct'],0)
  self.assertEqual(self.call(f,'demo_delivery_status',data=dict(deliverable_id=d['id'],status='blocked',reason='Waiting for source access'))[0],200)
  self.assertEqual(progress()['calculated_health'],'blocked')
  self.call(f,'demo_delivery_status',data=dict(deliverable_id=d['id'],status='in_progress',reason='Source access restored'))
  self.assertEqual(progress()['calculated_health'],'on_track')
  code,note,_=self.call(f,'demo_evidence_note',data=dict(deliverable_id=d['id'],text='All 20 validation checks passed with reconciled exceptions.'))
  self.assertEqual(code,200);self.assertEqual(progress()['delivery_pct'],0)
  cs=[c for c in f.db['checkpoints'] if c['deliverable_id']==d['id']]
  def decision(c,accepted=True):return dict(goal_id=g['id'],checkpoint_id=c['id'],evidence_id=note['evidence_id'],accepted=accepted,reason='Verified the results against the criteria',file_safety_acknowledged=True)
  self.assertEqual(self.call(f,'accept_checkpoint',data=decision(cs[0]))[0],403)
  self.assertEqual(self.call(f,'accept_checkpoint','ada',decision(cs[0]))[0],200)
  self.assertEqual(progress()['delivery_pct'],15)
  self.call(f,'accept_checkpoint','ada',decision(cs[1]))
  self.assertEqual(progress()['delivery_pct'],37.5)
  code,note2,_=self.call(f,'demo_evidence_note',data=dict(deliverable_id=ds[1]['id'],text='Implementation is independently validated across all checks.'))
  for c in [c for c in f.db['checkpoints'] if c['deliverable_id']==ds[1]['id']]:
   p=decision(c);p['evidence_id']=note2['evidence_id'];self.assertEqual(self.call(f,'accept_checkpoint','ada',p)[0],200)
  self.assertEqual(progress()['delivery_pct'],100);self.assertEqual(progress()['calculated_health'],'complete')
  self.call(f,'accept_checkpoint','ada',decision(cs[1],False))
  self.assertEqual(progress()['delivery_pct'],77.5);self.assertNotEqual(progress()['calculated_health'],'complete')
 def test_scoping_and_invalid_evidence(self):
  f=Fixture();g,ds=self.setup_flow(f);d=ds[0]
  self.assertEqual(self.call(f,'demo_delivery_status','dan',dict(deliverable_id=d['id'],status='blocked',reason='Outside scope'))[0],403)
  c=f.db['checkpoints'][0]
  p=dict(goal_id=g['id'],checkpoint_id=c['id'],evidence_id='nonexistent',accepted=True,reason='invalid',file_safety_acknowledged=True)
  self.assertEqual(self.call(f,'accept_checkpoint','ada',p)[0],400)
  self.assertEqual(f.state(uid('bea'))['acceptances'],[])
 def test_file_upload_download_and_no_unearned_credit(self):
  import urllib.parse
  f=Fixture();g,ds=self.setup_flow(f);d=ds[0];eid=str(uuid.uuid4());content=b'Synthetic validation evidence. All checks reconciled.'
  query=urllib.parse.urlencode(dict(leader=uid('bea'),deliverable_id=d['id'],upload_id=eid))
  headers={'Content-Type':'text/plain','X-File-Name':'validation.txt'}
  code,result,_=f.handle('/api/upload',query,content,headers);self.assertEqual(code,200)
  self.assertEqual(f.state(uid('ada'))['progress'][0]['delivery_pct'],0)
  response=f.handle('/api/download','',json.dumps(dict(leader_id=uid('ada'),evidence_id=eid)).encode(),{})
  self.assertEqual(response[1],content)
  self.assertEqual(f.handle('/api/upload',query,b'Different bytes',headers)[0],409)
  self.assertEqual(f.files[eid],content)
 def test_persistence_and_idempotency(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'demo.json';f=Fixture(path);g,ds=self.setup_flow(f);mid=str(uuid.uuid4())
   p=dict(deliverable_id=ds[0]['id'],text='Evidence survives a complete local server restart.')
   a=self.call(f,'demo_evidence_note',data=p,mid=mid);b=self.call(f,'demo_evidence_note',data=p,mid=mid)
   self.assertEqual(a,b)
   restored=Fixture(path);self.assertEqual(restored.scenario,'walkthrough');self.assertEqual(len(restored.state(uid('bea'))['evidence']),1)
   self.assertIn(a[1]['evidence_id'],restored.files)
if __name__=='__main__':unittest.main()
