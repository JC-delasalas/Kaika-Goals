import unittest,base64,io,json,uuid
from PIL import Image
from profile_domain import normalize_profile
from demo_mutations import Invalid
from fixture_server import Fixture
class Profiles(unittest.TestCase):
 def test_photo_decoded_resized_and_metadata_removed(self):
  im=Image.new('RGB',(600,400),'teal');out=io.BytesIO();im.save(out,'JPEG',comment=b'private metadata')
  p=normalize_profile('me',{'photo_data_url':'data:image/jpeg;base64,'+base64.b64encode(out.getvalue()).decode()})
  image=Image.open(io.BytesIO(base64.b64decode(p['photo_data_url'].split(',')[1])))
  self.assertEqual(image.size,(160,160));self.assertFalse(image.getexif());self.assertNotIn('comment',image.info)
 def test_cloud_metadata_survives_scoped_projection(self):
  f=Fixture();a=f.people[0];a.update(has_photo=True,profile_revision=2,avatar_style=3)
  p=next(p for p in f.state(a['id'])['people'] if p['id']==a['id'])
  self.assertTrue(p['has_photo']);self.assertEqual(p['profile_revision'],2)
 def test_forgery_unsupported_broken_and_oversize(self):
  for p in [{'person_id':'someoneelse'},{'avatar_style':8},{'avatar_style':True},{'expected_revision':-1},{'photo_data_url':'data:image/svg+xml;base64,PHN2Zz4='},{'photo_data_url':'data:image/jpeg;base64,bm90YW5pbWFnZQ=='},{'photo_data_url':'x'*700001}]:
   with self.assertRaises(Invalid):normalize_profile('me',p)
 def test_fixture_save_scope_and_conflict(self):
  f=Fixture();a=f.people[0]['id'];b=next(p['id'] for p in f.people if a not in f.scope(p['id']))
  def cmd(l,action,p):return f.handle('/api/command','',json.dumps({'action':action,'leader_id':l,'data':p,'mutation_id':str(uuid.uuid4())}).encode(),{})
  self.assertEqual(cmd(a,'profile_save',{'avatar_style':3})[0],200)
  self.assertEqual(cmd(a,'profile_save',{'avatar_style':2})[0],409)
  self.assertEqual(next(p for p in f.state(a)['people'] if p['id']==a)['avatar_style'],3)
  self.assertNotIn('profiles',f.state(a))
  self.assertEqual(cmd(b,'profile_photos',{'person_ids':[a]})[0],403)
if __name__=='__main__':unittest.main()
