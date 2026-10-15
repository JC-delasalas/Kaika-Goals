import unittest,copy
import test_editable_demo as helpers
from fixture_server import Fixture,uid
from scenarios import seed
class SuccessBasisTests(unittest.TestCase):
 def call(self,f,a,who='bea',p=None):return helpers.EditableDemo().call(f,a,who,p)
 def prepare(self,preset):
  f=Fixture();seed(f,preset);s=f.state(uid('bea'));return f,s['goals'][0],s['versions'][0]
 def accept_all(self,f,g):
  for d in f.state(uid('bea'))['deliverables']:
   _,e,_=self.call(f,'demo_evidence_note',p=dict(deliverable_id=d['id'],text='Synthetic implementation evidence meets the agreed functional acceptance criteria.'))
   for c in f.state(uid('bea'))['checkpoints']:
    if c['deliverable_id']==d['id']:self.assertEqual(self.call(f,'accept_checkpoint','ada',dict(goal_id=g['id'],checkpoint_id=c['id'],evidence_id=e['evidence_id'],accepted=True,reason='Verified against functional criteria.',file_safety_acknowledged=True))[0],200)
 def payload(self,f,g,v):
  s=f.state(uid('bea'))
  return dict(goal_id=g['id'],edit_revision=v['edit_revision'],**{k:v[k] for k in ['title','description','starts_on','ends_on','priority','category','cadence','success_basis']},measures=[dict(m,source=m['source_definition']) for m in s['measures'] if m['version_id']==v['id']],deliverables=[dict(d,checkpoints=[c for c in s['checkpoints'] if c['deliverable_id']==d['id']]) for d in s['deliverables'] if d['version_id']==v['id']],allocations=[])
 def test_delivery_completes_without_measure_and_revocation_reopens(self):
  f,g,v=self.prepare('delivery_walkthrough');self.assertEqual(f.state(uid('bea'))['outcomes'][0]['measurement_state'],'not_applicable')
  self.accept_all(f,g);s=f.state(uid('bea'));self.assertEqual(s['progress'][0]['objective_state'],'achieved');self.assertEqual(s['progress'][0]['delivery_pct'],100)
  a=s['acceptances'][0];p={k:a[k] for k in ['checkpoint_id','evidence_id','reason','file_safety_acknowledged']};p.update(goal_id=g['id'],accepted=False)
  self.call(f,'accept_checkpoint','ada',p);self.assertNotEqual(f.state(uid('bea'))['progress'][0]['objective_state'],'achieved')
 def test_outcome_still_requires_measurement(self):
  f,g,v=self.prepare('walkthrough');self.accept_all(f,g);self.assertEqual(f.state(uid('bea'))['progress'][0]['objective_state'],'outcome_pending')
 def test_revision_does_not_change_approved_basis_until_approval(self):
  f,g,v=self.prepare('walkthrough');self.accept_all(f,g)
  self.assertEqual(self.call(f,'new_version',p=dict(goal_id=g['id']))[0],200)
  nv=f.db['versions'][-1];p=self.payload(f,g,nv);p.update(success_basis='delivery',measures=[])
  self.assertEqual(self.call(f,'save_draft',p=p)[0],200)
  self.assertEqual(f.state(uid('bea'))['progress'][0]['success_basis'],'outcome')
  self.assertEqual(self.call(f,'submit',p=dict(goal_id=g['id']))[0],200)
  self.assertEqual(self.call(f,'approve','ada',dict(goal_id=g['id'],decision='approved',reason='Approve delivery-based scope'))[0],200)
  s=f.state(uid('bea'));self.assertEqual(s['progress'][0]['success_basis'],'delivery');self.assertEqual(s['progress'][0]['delivery_pct'],0)
  self.assertEqual(self.call(f,'save_draft',p=p)[0],403)
 def test_submit_requires_criteria_matching_basis(self):
  f,g,v=self.prepare('delivery_walkthrough');self.call(f,'new_version',p=dict(goal_id=g['id']));nv=f.db['versions'][-1]
  p=self.payload(f,g,nv);p['success_basis']='outcome';self.call(f,'save_draft',p=p)
  self.assertEqual(self.call(f,'submit',p=dict(goal_id=g['id']))[0],400)
  self.assertEqual(nv['state'],'draft')
  # Invalid checkpoint contract cannot be approved merely because no KPI is required.
  p=self.payload(f,g,f.db['versions'][-1]);p['success_basis']='delivery';p['deliverables'][0]['checkpoints'][0]['weight']=0
  self.call(f,'save_draft',p=p);self.assertEqual(self.call(f,'submit',p=dict(goal_id=g['id']))[0],400)
 def test_delivery_rejects_outcome_readings(self):
  f,g,v=self.prepare('delivery_walkthrough')
  self.assertEqual(self.call(f,'reading',p=dict(goal_id=g['id'],measure_id='anything',value=100,evidence_note='This goal has no business outcome metric.'))[0],400)
 def test_child_delivery_rolls_up_without_claiming_parent_outcome(self):
  f,g,v=self.prepare('delivery_walkthrough');self.accept_all(f,g)
  parent=f.new_goal(uid('bea'),'Improve quality','department',None);pv=f.db['versions'][-1];parent['active_version_id']=pv['id']
  next(x for x in f.db['goals'] if x['id']==g['id'])['parent_id']=parent['id']
  p=next(p for p in f.state(uid('bea'))['progress'] if p['root_id']==parent['id'])
  self.assertEqual(p['delivery_pct'],100);self.assertEqual(p['objective_state'],'outcome_pending')
if __name__=='__main__':unittest.main()
