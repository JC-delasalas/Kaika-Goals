import unittest,json,uuid
from fixture_server import Fixture,uid
from scenarios import seed
class Personalization(unittest.TestCase):
 def setUp(self):
  self.f=Fixture();seed(self.f,'walkthrough');self.d=self.f.db['deliverables'][0];self.d['owner_id']=uid('ana');self.parent=self.f.db['goals'][0]
 def call(self,action,person,payload):
  return self.f.handle('/api/command','',json.dumps(dict(action=action,leader_id=uid(person),data=payload,mutation_id=str(uuid.uuid4()))).encode(),{})
 def test_assigned_leaf_without_parent_or_siblings(self):
  s=self.f.state(uid('ana'));self.assertEqual(s['goals'],[]);self.assertEqual(s['versions'],[]);self.assertEqual(s['deliverables'],[])
  self.assertEqual(len(s['assigned_work']),1);a=s['assigned_work'][0];self.assertEqual(a['deliverable']['id'],self.d['id']);self.assertEqual(a['progress']['accepted_pct'],0)
  self.assertNotIn('goal',a);self.assertEqual(self.f.state(uid('dan'))['assigned_work'],[])
  self.assertEqual(self.f.state(uid('bea'))['assigned_work'],[],'Normal goal scope cannot duplicate the same leaf')
 def test_owner_can_submit_evidence_not_approve_or_edit_parent(self):
  before=self.f.state(uid('bea'))['progress'][0]['delivery_pct']
  code,result,_=self.call('demo_evidence_note','ana',dict(deliverable_id=self.d['id'],text='Assignment test evidence with all acceptance criteria checked.'));self.assertEqual(code,200)
  s=self.f.state(uid('ana'));self.assertEqual(s['assigned_work'][0]['evidence'][0]['id'],result['evidence_id']);self.assertEqual(self.f.state(uid('bea'))['progress'][0]['delivery_pct'],before)
  download=self.f.handle('/api/download','',json.dumps(dict(leader_id=uid('ana'),evidence_id=result['evidence_id'])).encode(),{});self.assertEqual(download[0],200)
  self.assertEqual(self.f.handle('/api/download','',json.dumps(dict(leader_id=uid('dan'),evidence_id=result['evidence_id'])).encode(),{})[0],403)
  self.assertEqual(self.call('demo_delivery_status','ana',dict(deliverable_id=self.d['id'],status='blocked',reason='Test dependency unavailable'))[0],200)
  self.assertEqual(self.f.state(uid('bea'))['progress'][0]['calculated_health'],'blocked')
  self.assertEqual(self.call('demo_delivery_status','dan',dict(deliverable_id=self.d['id'],status='blocked',reason='Invalid access'))[0],403)
  self.assertEqual(self.call('checkin','ana',dict(goal_id=self.parent['id'],health='on_track',reason='Cannot edit manager plan'))[0],403)
 def test_assigned_allocations_do_not_expose_parent(self):
  v=self.d['version_id'];self.f.db['allocations'].append(dict(id='external',version_id=v,worker_id=uid('ana'),month='2026-10-01',allocation_pct=30))
  s=self.f.state(uid('ana'));a=next(a for a in s['assigned_allocations'] if a['id']=='external');self.assertEqual(a['allocation_pct'],30);self.assertNotIn('version_id',a);self.assertEqual(s['goals'],[])
  self.assertEqual(self.f.state(uid('dan'))['assigned_allocations'],[])
  self.assertNotIn('external',{a['id'] for a in self.f.state(uid('bea'))['assigned_allocations']})
 def test_unapproved_assignment_is_not_exposed(self):
  for g in self.f.db['goals']:g['active_version_id']=None
  self.assertEqual(self.f.state(uid('ana'))['assigned_work'],[])
if __name__=='__main__':unittest.main()
