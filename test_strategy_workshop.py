import unittest,copy,tempfile
from pathlib import Path
from fixture_server import Fixture,uid
from goal_contract import validate_plan
from demo_mutations import Invalid
class StrategyWorkshopTests(unittest.TestCase):
 def setUp(self):self.f=Fixture(default_scenario='strategy')
 def test_complete_contracts_and_leaves(self):
  self.assertEqual(len(self.f.db['goals']),11)
  self.assertEqual(len(self.f.db['deliverables']),11)
  self.assertEqual(len(self.f.db['pillars']),3)
  for v in self.f.db['versions']:validate_plan(self.f,v)
  for d in self.f.db['deliverables']:
   v=next(v for v in self.f.db['versions'] if v['id']==d['version_id'])
   g=next(g for g in self.f.db['goals'] if g['id']==v['goal_id'])
   self.assertEqual(g['node_kind'],'workstream')
   self.assertFalse(any(g['parent_id']==d['id'] for g in self.f.db['goals']))
 def test_scope_and_rollup(self):
  ada=self.f.state(uid('ada'));dan=self.f.state(uid('dan'));ana=self.f.state(uid('ana'))
  self.assertEqual((len(ada['goals']),len(dan['goals']),len(ana['goals'])),(8,3,1))
  self.assertFalse({g['id'] for g in ada['goals']}&{g['id'] for g in dan['goals']})
  self.assertEqual(len(ada['pillars']),2);self.assertEqual(len(dan['pillars']),1)
  for key,value in [('quality',round(8.2/18*100,2)),('reporting',32),('onboarding',round(5.2/9*100,2))]:
   p=next(p for p in self.f.state(uid('sam'))['progress'] if p['root_id']==uid('strategy-'+key))
   self.assertAlmostEqual(p['delivery_pct'],value,places=1)
 def test_workstream_may_have_both_subworkstreams_and_direct_deliverables(self):
  child=next(g for g in self.f.db['goals'] if g['id']==uid('strategy-operating'))
  child['parent_id']=uid('strategy-ownership')
  v=next(v for v in self.f.db['versions'] if v['goal_id']==child['parent_id'])
  validate_plan(self.f,v)
  self.assertTrue(any(d['version_id']==v['id'] for d in self.f.db['deliverables']))
 def test_objective_cannot_have_direct_deliverable(self):
  v=next(v for v in self.f.db['versions'] if v['goal_id']==uid('strategy-quality'))
  self.f.db['deliverables'][0]['version_id']=v['id']
  with self.assertRaisesRegex(Invalid,'workstream'):validate_plan(self.f,v)
 def test_manager_and_reports_can_own_workstream_leaves(self):
  v=next(v for v in self.f.db['versions'] if v['goal_id']==uid('strategy-ownership'))
  self.assertEqual({d['owner_id'] for d in self.f.db['deliverables'] if d['version_id']==v['id']},{uid('ada'),uid('bea')})
  validate_plan(self.f,v)
 def test_restore_strategy_and_people(self):
  with tempfile.TemporaryDirectory() as d:
   self.f.storage=Path(d)/'state.json';self.f.persist();restored=Fixture(self.f.storage)
   self.assertEqual(restored.state(uid('ada')),self.f.state(uid('ada')))
if __name__=='__main__':unittest.main()
