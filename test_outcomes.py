import unittest
import test_editable_demo as helpers
from fixture_server import Fixture,uid
from scenarios import seed
class OutcomeTests(unittest.TestCase):
 def setUp(self):
  self.f=Fixture();seed(self.f,'walkthrough');self.g=self.f.state(uid('bea'))['goals'][0];self.m=self.f.db['measures'][0]
 def state(self):return self.f.state(uid('bea'))
 def reading(self,value,leader='bea',date='2026-10-27',measure=None):
  return helpers.EditableDemo().call(self.f,'reading',leader,dict(goal_id=self.g['id'],measure_id=measure or self.m['id'],value=value,evidence_note='Synthetic weekly audit of the same 20 datasets; source report QA-027.',observed_on=date))
 def test_no_measurement_baseline_improvement_target_and_regression(self):
  self.assertIsNone(self.state()['outcomes'][0]['outcome_pct'])
  for val,pct,state in [(60,0,'no_improvement'),(85,71.43,'improving'),(95,100,'target_met'),(50,0,'below_baseline')]:
   self.assertEqual(self.reading(val)[0],200)
   o=self.state()['outcomes'][0];self.assertEqual(o['outcome_pct'],pct);self.assertEqual(o['measurement_state'],state)
   self.assertEqual(self.state()['progress'][0]['delivery_pct'],0)
  self.assertNotEqual(self.state()['progress'][0]['objective_state'],'achieved')
 def test_missing_and_stale_do_not_achieve(self):
  self.reading(95,date='2026-10-01');o=self.state()['outcomes'][0]
  self.assertEqual(o['outcome_pct'],100);self.assertEqual(o['measurement_state'],'stale');self.assertFalse(o['target_met'])
 def test_validation_and_scope(self):
  for value in ['NaN','Infinity',-1,101]:self.assertEqual(self.reading(value)[0],400)
  self.assertEqual(self.reading(95,leader='ada')[0],403)
  self.assertEqual(self.reading(95,measure='wrong')[0],400)
  self.assertEqual(self.reading(95,date='2026-11-01')[0],400)
  self.assertEqual(self.state()['readings'],[])
 def test_decreasing_weighted_and_missing_measure(self):
  self.m.update(baseline=100,target=20,direction='decrease',unit='hours',weight=50)
  self.f.db['measures'].append(dict(self.m,id='second',weight=50))
  self.reading(60);self.assertIsNone(self.state()['outcomes'][0]['outcome_pct'])
  self.reading(20,measure='second');self.assertEqual(self.state()['outcomes'][0]['outcome_pct'],75)
 def test_achievement_requires_both_and_does_not_round_up(self):
  for d in self.state()['deliverables']:
   _,r,_=helpers.EditableDemo().call(self.f,'demo_evidence_note',data=dict(deliverable_id=d['id'],text='Synthetic implementation tests passed against all agreed functional criteria.'))
   for c in self.state()['checkpoints']:
    if c['deliverable_id']==d['id']:helpers.EditableDemo().call(self.f,'accept_checkpoint','ada',dict(goal_id=self.g['id'],checkpoint_id=c['id'],evidence_id=r['evidence_id'],accepted=True,reason='Verified functional test evidence',file_safety_acknowledged=True))
  self.assertEqual(self.state()['progress'][0]['objective_state'],'outcome_pending')
  self.reading(94.9999);self.assertFalse(self.state()['outcomes'][0]['target_met'])
  self.reading(95);self.assertEqual(self.state()['progress'][0]['objective_state'],'achieved')
if __name__=='__main__':unittest.main()
