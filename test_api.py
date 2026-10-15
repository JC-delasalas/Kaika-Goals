import unittest,tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from api import create_app
class BoundaryTests(unittest.TestCase):
 def test_host_origin_nonce_and_private_config(self):
  with tempfile.TemporaryDirectory() as root:
   c=TestClient(create_app(Path(root),8788,True),base_url='http://127.0.0.1:8788');n=c.get('/api/bootstrap').json()['nonce']
   self.assertEqual(c.post('/api/command',json={}).status_code,403)
   self.assertEqual(c.post('/api/command',headers={'X-Kaika-Nonce':n,'Origin':'https://evil.example'},json={}).status_code,403)
   self.assertEqual(c.get('/api/bootstrap',headers={'Host':'evil.example'}).status_code,403)
   self.assertEqual(c.get('/.workshop-config.json').status_code,404)
   r=c.post('/api/command',headers={'X-Kaika-Nonce':n},json={'action':'leaders'});self.assertEqual(r.status_code,200)
   self.assertIn('Server-Timing',r.headers);self.assertEqual(r.headers['Cache-Control'],'no-store')
