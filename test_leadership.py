import unittest,json,copy,tempfile
from pathlib import Path
from fixture_server import Fixture,uid
import test_editable_demo as helper
class LeadershipTests(unittest.TestCase):
 def setUp(self):self.f=Fixture();self.g=next(g for g in self.f.state(uid('bea'))['goals'] if g['id']==uid('mixed-progress'))
 def call(self,a,p={},who='bea',mid=None):return helper.EditableDemo().call(self.f,a,who,p,mid)
 def test_private_saved_views_and_persistence(self):
  _,r,_=self.call('save_view',{'name':'My risk view','filters':{'health':'attention','scope':'all','display':'board'}})
  self.assertEqual(len(self.f.state(uid('bea'))['saved_views']),1);self.assertEqual(self.f.state(uid('ada'))['saved_views'],[])
  self.assertEqual(self.call('delete_view',{'id':r['id']},'ada')[0],403)
  with tempfile.TemporaryDirectory() as t:
   self.f.storage=Path(t)/'state.json';self.f.persist();self.assertEqual(Fixture(self.f.storage).state(uid('bea'))['saved_views'][0]['name'],'My risk view')
 def test_question_reply_resolution_scope(self):
  p={'goal_id':self.g['id'],'text':'Who verifies the final audit?','assigned_to':uid('bea')};_,q,_=self.call('record_question',p,'ada')
  self.assertEqual(self.call('reply_question',{'goal_id':self.g['id'],'question_id':q['id'],'text':'The independent reviewer verifies the test log.'})[0],200)
  self.assertEqual(self.call('close_question',{'goal_id':self.g['id'],'question_id':q['id'],'text':'Reviewer confirmed.'})[0],200)
  self.assertTrue(next(x for x in self.f.db['questions'] if x['id']==q['id'])['resolved_at'])
  self.assertEqual(self.call('reply_question',{'goal_id':self.g['id'],'question_id':q['id'],'text':'Outside scope'},'dan')[0],403)
  self.assertFalse(any(x['goal_id']==self.g['id'] for x in self.f.state(uid('dan'))['replies']))
 def test_learning_owner_and_followup(self):
  p={'goal_id':self.g['id'],'result':'Still in progress','text':'Access approvals need more lead time.','next_step':'Request access at planning.'}
  self.assertEqual(self.call('record_learning',p,'ada')[0],403);self.assertEqual(self.call('record_learning',p)[0],200)
  _,a,_=self.call('create_followup',{'goal_id':self.g['id'],'text':'Confirm access','owner_id':uid('bea'),'due_on':'2026-10-28'},'ada')
  self.assertEqual(self.call('complete_followup',{'goal_id':self.g['id'],'id':a['id']})[0],200)
 def test_snapshot_frozen_and_rejects_outside_scope(self):
  p={'goal_ids':[self.g['id']],'title':'Weekly review','text':'Narrative based on current evidence.'}
  _,result,_=self.call('publish_snapshot',p,'ada');snapshot=copy.deepcopy(next(r for r in self.f.db['reviews'] if r['id']==result['id'])['snapshot'])
  m=next(m for m in self.f.db['measures'] if m['version_id']==self.g['active_version_id'])
  self.call('reading',{'goal_id':self.g['id'],'measure_id':m['id'],'value':95,'evidence_note':'New independent measurement after publishing.'})
  self.assertEqual(next(r for r in self.f.db['reviews'] if r['id']==result['id'])['snapshot'],snapshot)
  self.assertEqual(self.call('publish_snapshot',p,'dan')[0],403)
  self.assertFalse(any(r['id']==result['id'] for r in self.f.state(uid('dan'))['reviews']))
 def test_summary_capture_scope_and_metadata(self):
  p={'goal_ids':[self.g['id']],'title':'Summary baseline','text':'Frozen summary.','summary_capture':True,'filters':{'scope':'all','display':'cards'}}
  code,r,_=self.call('publish_snapshot',p,'ada');self.assertEqual(code,200)
  saved=next(x for x in self.f.db['reviews'] if x['id']==r['id']);meta=saved['snapshot']['summary_meta']
  self.assertEqual(meta['leader_id'],uid('ada'));self.assertEqual(meta['method'],'goals-pulse-v1');self.assertNotIn('display',meta['filters'])
  self.assertEqual(self.f.state(uid('bea'))['reviews'],[])
  self.assertEqual(self.call('publish_snapshot',{**p,'filters':[]},'ada')[0],400)
  # Revoking current reporting scope withholds the whole historical snapshot.
  owner=next(v for v in self.f.db['versions'] if v['id']==self.g['active_version_id'])['owner_id']
  next(x for x in self.f.people if x['id']==owner)['manager_id']=uid('dan')
  self.assertFalse(any(x['id']==r['id'] for x in self.f.state(uid('ada'))['reviews']))
 def test_kpi_history_does_not_change_progress(self):
  k=next(k for k in self.f.db['kpis'] if k['version_id']==self.g['active_version_id']);before=copy.deepcopy(self.f.state(uid('bea'))['progress'])
  for val in [220,180]:self.assertEqual(self.call('record_kpi',{'goal_id':self.g['id'],'kpi_id':k['id'],'value':val,'observed_on':'2026-10-27','evidence_note':'Synthetic cost statement with fixed scope.'})[0],200)
  self.assertEqual(self.f.state(uid('bea'))['progress'],before)
  self.assertEqual(len([r for r in self.f.db['kpi_readings'] if r['kpi_id']==k['id']]),3)
  self.assertEqual(self.call('record_kpi',{'goal_id':self.g['id'],'kpi_id':k['id'],'value':999},'dan')[0],403)
 def test_assignment_handoff_and_levels(self):
  parent=next(g for g in self.f.state(uid('ada'))['goals'] if g['id']==uid('mixed-complete'))
  self.assertEqual(self.call('create_goal',{'title':'Bad alignment','owner_id':uid('ada'),'level':'corporate','parent_id':parent['id']},'ada')[0],400)
  code,result,_=self.call('create_goal',{'title':'Implement agreed data monitoring','owner_id':uid('bea'),'level':'team','parent_id':parent['id']},'ada')
  self.assertEqual(code,200);g=next(g for g in self.f.state(uid('bea'))['goals'] if g['id']==result['goal_id']);self.assertEqual(g['origin'],'inherited');self.assertEqual(g['assignment_state'],'pending')
  self.assertEqual(self.call('accept_assignment',{'goal_id':g['id']},'ada')[0],403)
  self.assertEqual(self.call('accept_assignment',{'goal_id':g['id']})[0],200)
 def test_scope_snapshot_and_cross_goal_questions(self):
  q=self.f.db['questions'][0]
  self.assertEqual(self.call('close_question',{'goal_id':self.g['id'],'question_id':q['id'],'text':'Wrong goal'})[0],404)
  self.assertEqual(self.call('save_view',{'name':'Blank-safe','filters':{}})[0],200)
  self.assertEqual(self.call('save_view',{'name':'Blank-safe','filters':{}})[0],400)
 def test_snapshot_captures_delivery_contract_and_child_evidence(self):
  parent=uid('mixed-complete');next(g for g in self.f.db['goals'] if g['id']==self.g['id'])['parent_id']=parent
  p={'goal_ids':[parent],'title':'Parent snapshot','text':'Evidence freezes with its contribution records.'}
  code,r,_=self.call('publish_snapshot',p,'ada');self.assertEqual(code,200)
  snap=next(x for x in self.f.db['reviews'] if x['id']==r['id'])['snapshot']
  self.assertIn(self.g['id'],[g['id'] for g in snap['contributing_goals']]);self.assertTrue(snap['deliverables']);self.assertTrue(snap['checkpoints']);self.assertTrue(snap['acceptances']);self.assertTrue(snap['delivery_progress'])
 def test_allocation_rejects_overcommitment_and_invalid_month(self):
  from goal_contract import validate_plan
  from demo_mutations import Invalid
  v=next(v for v in self.f.db['versions'] if v['id']==self.g['active_version_id'])
  a=next(a for a in self.f.db['allocations'] if a['version_id']==v['id'])
  a['allocation_pct']=100
  with self.assertRaises(Invalid):validate_plan(self.f,v)
  a['allocation_pct']=10;a['month']='2027-01-01'
  with self.assertRaises(Invalid):validate_plan(self.f,v)

 def test_checkin_clock_does_not_reorder_after_midnight(self):
  from unittest.mock import patch
  self.f.db['checkins'].append(dict(id='late',goal_id=self.g['id'],author_id=uid('bea'),health='on_track',reason='Earlier save late in the day',created_at='2026-10-27T23:59:00+00:00'))
  with patch('fixture_server.now',return_value='2026-10-27T01:00:00+00:00'):
   status,_,_=self.call('checkin',dict(goal_id=self.g['id'],health='on_track',reason='Newest update after real midnight',eta='2026-11-01'))
  self.assertEqual(status,200)
  latest=max((c for c in self.f.db['checkins'] if c['goal_id']==self.g['id']),key=lambda c:c['created_at'])
  self.assertEqual(latest['reason'],'Newest update after real midnight');self.assertIn('recorded_at',latest)

if __name__=='__main__':unittest.main()
