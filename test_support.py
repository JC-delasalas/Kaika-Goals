import unittest,copy,json,tempfile
from pathlib import Path
from fixture_server import Fixture,uid
import test_editable_demo as helper
class SupportTests(unittest.TestCase):
 def setUp(self):self.f=Fixture();self.g=uid('mixed-blocked')
 def call(self,a,p,who='ada',mid=None):return helper.EditableDemo().call(self.f,a,who,p,mid)
 def create(self,**changes):
  p=dict(goal_id=self.g,owner_id=uid('dan'),title='Validate customer mappings',context='Validate the shared synthetic mapping only.',criteria='All 20 sample records reconcile; return a validation summary.',due_on='2026-11-20');p.update(changes)
  return self.call('support_create',p)
 def advance(self,r,a,who,text='Criteria checked.',**kw):
  p=dict(id=r['id'],revision=r['revision'],text=text);p.update(kw);return self.call(a,p,who)
 def test_lifecycle_return_resubmit_and_no_double_count(self):
  before={k:copy.deepcopy(self.f.state(uid('ada'))[k]) for k in ['progress','outcomes','allocations','goals','checkpoints','acceptances']}
  code,r,_=self.create();self.assertEqual(code,200)
  for action,who in [('support_accept','dan'),('support_submit','dan'),('support_return','ada'),('support_submit','dan'),('support_complete','ada')]:
   code,r,_=self.advance(r,action,who);self.assertEqual(code,200)
  self.assertEqual(self.f.db['support_requests'][0]['state'],'completed');self.assertEqual(len(self.f.db['support_requests'][0]['history']),6)
  self.create(title='A second contribution for the same goal')
  after=self.f.state(uid('ada'))
  for k,v in before.items():self.assertEqual(after[k],v,k)
 def test_explicit_projection_and_private_delivery_link(self):
  _,r,_=self.create();dan=self.f.state(uid('dan'));dg=dan['goals'][0]
  self.advance(r,'support_accept','dan',delivery_goal_id=dg['id'])
  received=self.f.state(uid('dan'))['support_requests'][0];sent=self.f.state(uid('ada'))['support_requests'][0]
  self.assertNotIn('requester_goal_id',received);self.assertNotIn(self.g,json.dumps(dan));self.assertNotIn('requester_version_id',received)
  self.assertNotIn('delivery_goal_id',sent);self.assertNotIn(dg['id'],json.dumps(self.f.state(uid('ada'))));self.assertEqual(received['delivery_goal_id'],dg['id'])
  self.assertEqual(self.f.state(uid('bea'))['support_requests'],[])
  self.assertEqual(set(self.f.state(uid('ada'))['support_contacts'][0]),{'id','name','team'})
 def test_roles_stale_revision_and_hidden_ids(self):
  _,r,_=self.create()
  for who in ['ada','bea','sam']:self.assertEqual(self.advance(r,'support_accept',who)[0],403)
  code,new,_=self.advance(r,'support_accept','dan');self.assertEqual(code,200)
  self.assertEqual(self.advance(r,'support_submit','dan')[0],409)
  self.assertEqual(self.advance(new,'support_complete','ada')[0],409)
  self.assertEqual(self.advance(new,'support_submit','bea')[0],403)
  self.assertEqual(self.advance(new,'support_submit','dan')[0],200)
 def test_validation_and_forged_goal(self):
  for changes in [dict(context=''),dict(criteria=''),dict(due_on='garbage'),dict(due_on='2026-10-01'),dict(due_on='2027-01-01'),dict(owner_id=uid('bea')),dict(goal_id=uid('mixed-progress'))]:self.assertGreaterEqual(self.create(**changes)[0],400)
  self.assertEqual(self.f.db['support_requests'],[])
  _,r,_=self.create();self.assertEqual(self.advance(r,'support_accept','dan',delivery_goal_id=self.g)[0],403)
 def test_decline_cancel_terminality(self):
  _,r,_=self.create();_,r,_=self.advance(r,'support_decline','dan');self.assertEqual(self.advance(r,'support_accept','dan')[0],409)
  _,r,_=self.create();_,r,_=self.advance(r,'support_cancel','ada');self.assertEqual(self.advance(r,'support_accept','dan')[0],409)
 def test_idempotency_is_identity_scoped(self):
  _,r,_=self.create();p=dict(id=r['id'],revision=0,text='Commit to date and criteria.')
  code,res,_=self.call('support_accept',p,'dan','retry-1');self.assertEqual(code,200)
  self.assertEqual(self.call('support_accept',p,'dan','retry-1')[1],res)
  self.assertEqual(self.call('support_accept',p,'bea','retry-1')[0],403)
  self.assertEqual(len(self.f.db['support_requests'][0]['history']),2)
 def test_overdue_persistence_and_frozen_snapshot(self):
  _,r,_=self.create();self.f.as_of='2026-11-21';self.assertTrue(self.f.state(uid('dan'))['support_requests'][0]['overdue'])
  _,snap,_=self.call('publish_snapshot',dict(goal_ids=[self.g],title='Support review',text='Open cross-team commitment.'))
  frozen=copy.deepcopy(self.f.db['reviews'][-1]['snapshot']);self.advance(r,'support_cancel','ada')
  self.assertEqual(self.f.db['reviews'][-1]['snapshot'],frozen);self.assertEqual(frozen['support_requests'][0]['state'],'requested')
  with tempfile.TemporaryDirectory() as t:
   self.f.storage=Path(t)/'state.json';self.f.persist();restored=Fixture(self.f.storage)
   self.assertEqual(restored.state(uid('ada'))['support_requests'][0]['state'],'cancelled');self.assertEqual(restored.state(uid('bea'))['support_requests'],[])
if __name__=='__main__':unittest.main()
