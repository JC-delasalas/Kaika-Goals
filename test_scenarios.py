import unittest,json
from fixture_server import Fixture,uid
from scenarios import seed
class Scenarios(unittest.TestCase):
 def test_mixed_status_coverage_and_progress(self):
  f=Fixture();s=f.state(uid('ada'))
  self.assertEqual(len(s['goals']),11)
  self.assertEqual({p['calculated_health'] for p in s['delivery_progress']},{'complete','in_progress','blocked','at_risk','overdue','not_started','awaiting_review','unknown','draft'})
  self.assertTrue({'complete','on_track','blocked','at_risk','not_started','awaiting_review','unknown'}<={p['calculated_health'] for p in s['progress']})
  monitor=next(v for v in s['versions'] if v['title']=='Launch the monitoring service')
  self.assertEqual(next(p['delivery_pct'] for p in s['progress'] if p['root_id']==monitor['goal_id']),62.5) # (3*100+5*40)/8
  self.assertFalse(any(v['owner_id']==uid('dan') for v in s['versions']))
 def test_completed_and_empty(self):
  f=Fixture();seed(f,'finished');s=f.state(uid('ada'))
  self.assertEqual(len(s['goals']),3)
  self.assertTrue(all(p['delivery_pct']==100 for p in s['progress']))
  self.assertTrue(all(p['outcome_pct']==100 for p in s['outcomes']))
  for e in s['evidence']:self.assertEqual(len(f.files[e['id']]),e['byte_size'])
  seed(f,'empty');s=f.state(uid('ada'))
  self.assertEqual(len(s['people']),3);self.assertEqual(s['goals'],[]);self.assertEqual(s['evidence'],[])
 def test_partial_is_not_fake_zero(self):
  f=Fixture();seed(f,'partial');s=f.state(uid('ada'))
  self.assertTrue(all(p['delivery_pct'] is None for p in s['progress']))
  self.assertTrue(any(not v['description'] for v in s['versions']))
 def test_scenario_endpoint(self):
  f=Fixture()
  code,result,_=f.handle('/api/command','',json.dumps({'action':'demo_scenario','leader_id':uid('ada'),'data':{'preset':'empty'}}).encode(),{})
  self.assertEqual(code,200);self.assertEqual(f.state(uid('ada'))['goals'],[])
if __name__=='__main__':unittest.main()
