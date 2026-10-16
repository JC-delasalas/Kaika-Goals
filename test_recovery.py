import copy,unittest,uuid
from fixture_server import Fixture,uid
import test_success_basis
import test_editable_demo

class RecoveryTests(unittest.TestCase):
 def setUp(self):
  self.f=Fixture();self.h=test_editable_demo.EditableDemo();self.g=self.f.new_goal(uid('bea'),'Recovery test','team',None);self.v=self.f.db['versions'][-1]
 def call(self,action,p,actor='bea',mid=None):return self.h.call(self.f,action,actor,p,mid)
 def payload(self):
  p=test_success_basis.SuccessBasisTests().payload(self.f,self.g,self.v);p['expected_version_id']=self.v['id'];return p
 def test_save_undo_and_stale_undo_do_not_overwrite(self):
  before=self.payload();p=copy.deepcopy(before);p['description']='Changed';self.assertEqual(self.call('save_draft',p)[0],200)
  undo={**before,'edit_revision':1,'undo_of_revision':1};self.assertEqual(self.call('save_draft',undo)[0],200)
  v=self.f.db['versions'][-1];self.assertEqual(v['description'],before['description']);self.assertEqual(v['edit_revision'],2);self.assertEqual(v['edit_events'][-1]['reason'],'undo')
  self.assertEqual(self.call('save_draft',undo)[0],409);self.assertEqual(self.f.db['versions'][-1]['edit_revision'],2)
 def test_wrong_version_and_stale_submit_rejected(self):
  p=self.payload();p['expected_version_id']='old-version';self.assertEqual(self.call('save_draft',p)[0],409)
  self.assertEqual(self.call('submit',dict(goal_id=self.g['id'],expected_version_id=self.v['id'],edit_revision=99))[0],409)
  self.assertEqual(self.call('approve',dict(goal_id=self.g['id'],expected_version_id='old-version',decision='approved',reason='Old form'),'ada')[0],409)
 def test_duplicate_save_only_increments_once_and_actor_is_checked(self):
  p=self.payload();mid=str(uuid.uuid4());self.assertEqual(self.call('save_draft',p,mid=mid)[0],200);self.assertEqual(self.call('save_draft',p,mid=mid)[0],200)
  self.assertEqual(self.f.db['versions'][-1]['edit_revision'],1);self.assertEqual(len(self.f.db['versions'][-1]['edit_events']),1)
  p=self.payload();p['edit_revision']=1;self.assertEqual(self.call('save_draft',p,'dan')[0],403)
if __name__=='__main__':unittest.main()
