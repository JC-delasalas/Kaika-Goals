import unittest,copy
from fixture_server import Fixture,uid
import test_success_basis
from demo_mutations import Invalid
from goal_contract import validate_plan

class RegistrationTests(unittest.TestCase):
 def setUp(self):self.f=Fixture();self.helper=test_success_basis.SuccessBasisTests()
 def call(self,a,p,who='bea'):return self.helper.call(self.f,a,who,p)
 def create(self,owner='bea',parent=None,actor='bea'):
  code,r,_=self.call('create_goal',dict(owner_id=uid(owner),title='Synthetic registration validation',level='team',parent_id=parent),actor);self.assertEqual(code,200,r)
  return next(g for g in self.f.db['goals'] if g['id']==r['goal_id']),self.f.db['versions'][-1]
 def payload(self,g,v):
  p=self.helper.payload(self.f,g,v);p.update(registration_contract=2,success_basis='metric',description='Synthetic audit contract',starts_on='2026-10-27',ends_on='2026-12-18',measures=[dict(title='Audit pass rate',unit='%',direction='increase',baseline=60,target=95,weight=100,source='Fixed 20 datasets weekly audit')]);return p
 def test_metric_no_deliverables_submit_approve_observe(self):
  g,v=self.create();p=self.payload(g,v);self.assertEqual(self.call('save_draft',p)[0],200)
  self.assertEqual(self.call('submit',dict(goal_id=g['id']))[0],200)
  self.assertEqual(self.call('approve',dict(goal_id=g['id'],decision='approved',reason='Synthetic approval'),'ada')[0],200)
  s=self.f.state(uid('bea'));metric=next(m for m in s['measures'] if m['version_id']==v['id'])
  self.assertEqual(self.call('reading',dict(goal_id=g['id'],measure_id=metric['id'],value=95,observed_on='2026-10-27',evidence_note='Synthetic fixed population weekly audit report.'))[0],200)
  progress=next(p for p in self.f.state(uid('bea'))['progress'] if p['root_id']==g['id'])
  self.assertEqual(progress['objective_state'],'achieved');self.assertIsNone(progress['delivery_pct'])
  self.assertFalse(any(x['id']==g['id'] for x in self.f.state(uid('dan'))['goals']))
  self.assertEqual(self.call('save_draft',p,'dan')[0],403)
 def test_combined_requires_delivery_and_separate_gates(self):
  g,v=self.create();p=self.payload(g,v);p['success_basis']='combined';self.call('save_draft',p)
  self.assertEqual(self.call('submit',dict(goal_id=g['id']))[0],400)
 def test_assignment_pushback_resend_accept_and_pass_through(self):
  parent,pv=self.create(owner='ada',actor='ada');pv.update(description='Synthetic parent',starts_on='2026-10-27',ends_on='2026-12-18',success_basis='delivery')
  child,cv=self.create(parent=parent['id'],actor='ada');self.assertEqual(child['assignment_state'],'pending')
  p=self.payload(child,cv);self.assertEqual(self.call('save_draft',p)[0],400)
  self.assertEqual(self.call('pushback_assignment',dict(goal_id=child['id'],reason='Need a clarified scope and resource agreement.'))[0],200)
  self.assertEqual(self.call('accept_assignment',dict(goal_id=child['id']))[0],403)
  self.assertEqual(self.call('resend_assignment',dict(goal_id=child['id'],reason='Remit confirmed; owner can now define the plan.'),'ada')[0],200)
  self.assertEqual(self.call('accept_assignment',dict(goal_id=child['id']))[0],200)
  self.assertEqual(self.call('save_draft',p)[0],200)
  # Parent does not need to fill unstarted descendant forms.
  cv['starts_on']='';cv['ends_on']='';validate_plan(self.f,pv)
 def test_resource_identity_survives_save_and_revision(self):
  parent,pv=self.create();g,v=self.create(parent=parent['id']);p=self.payload(g,v);p['success_basis']='combined'
  p['deliverables']=[dict(client_id='local-leaf',title='Verified audit tool',owner_id=uid('bea'),due_on='2026-12-10',effort_days=3,definition_of_done='Verified test report and handover',checkpoints=[dict(title='Acceptance',weight=100,due_on='2026-12-10',acceptance_criteria='Report passes agreed scenarios')])]
  p['allocations']=[dict(worker_id=uid('ana'),deliverable_id='local-leaf',starts_on='2026-11-01',ends_on='2026-11-20',month='2026-11-01',allocation_pct=10)]
  code,r,_=self.call('save_draft',p);self.assertEqual(code,200,r)
  leaf=next(d for d in self.f.db['deliverables'] if d['version_id']==v['id']);allocation=next(a for a in self.f.db['allocations'] if a['version_id']==v['id']);self.assertEqual(allocation['deliverable_id'],leaf['id'])
  self.assertEqual(self.call('submit',dict(goal_id=g['id']))[0],200)
  self.assertEqual(self.call('approve',dict(goal_id=g['id'],decision='approved',reason='Approved resource-linked contract'),'ada')[0],200)
  self.assertEqual(self.call('new_version',dict(goal_id=g['id']))[0],200)
  nv=self.f.db['versions'][-1];na=next(a for a in self.f.db['allocations'] if a['version_id']==nv['id']);nd=next(d for d in self.f.db['deliverables'] if d['version_id']==nv['id']);self.assertEqual(na['deliverable_id'],nd['id']);self.assertNotEqual(na['deliverable_id'],leaf['id'])
  self.assertEqual(self.call('reading',dict(goal_id=g['id'],measure_id=next(m for m in self.f.db['measures'] if m['version_id']==v['id'])['id'],value=95,evidence_note='Synthetic current audit confirms all required targets.'))[0],200)
  prog=next(p for p in self.f.state(uid('bea'))['progress'] if p['root_id']==g['id']);self.assertEqual(prog['objective_state'],'target_met_delivery_open')
 def test_partial_draft_and_resource_rejection(self):
  g,v=self.create();p=self.payload(g,v);p.update(description='',starts_on='',ends_on='',measures=[])
  self.assertEqual(self.call('save_draft',p)[0],200);self.assertEqual(self.call('submit',dict(goal_id=g['id']))[0],400)
  p['edit_revision']=1;p['allocations']=[dict(deliverable_id='outside',worker_id=uid('dan'),month='2026-11-01',allocation_pct=10)]
  self.assertEqual(self.call('save_draft',p)[0],400)
 def test_alignment_rejects_corporate_child_and_peer_assignment(self):
  g,v=self.create()
  self.assertEqual(self.call('create_goal',dict(owner_id=uid('bea'),title='Invalid',level='corporate',parent_id=g['id']))[0],400)
  self.assertEqual(self.call('create_goal',dict(owner_id=uid('dan'),title='Invalid',level='team',parent_id=g['id']))[0],403)
if __name__=='__main__':unittest.main()
