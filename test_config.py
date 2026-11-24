import unittest, tempfile, json, base64
from pathlib import Path
from unittest.mock import patch
import src.config as mod

class ConfigTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
  self.path=Path(self.tmp.name)/'config.json'
  self.a=patch.object(mod,'CONFIG_DIR',Path(self.tmp.name)); self.a.start(); self.addCleanup(self.a.stop)
  self.b=patch.object(mod,'CONFIG_FILE',self.path); self.b.start(); self.addCleanup(self.b.stop)
 def test_migration(self):
  self.path.write_text(json.dumps({'server_url':'https://example.test','username':'test','password_b64':base64.b64encode(b'secret').decode()}))
  with patch.object(mod.keyring,'set_password') as store, patch.object(mod.keyring,'get_password',return_value='secret'):
   c=mod.Config(); self.assertTrue(c.is_configured); store.assert_called_once_with('tecnomata-hifi','navidrome','secret')
  self.assertNotIn('password_b64',json.loads(self.path.read_text()))
 def test_failed_migration_keeps_original(self):
  self.path.write_text(json.dumps({'password_b64':base64.b64encode(b'secret').decode()}))
  with patch.object(mod.keyring,'set_password',side_effect=RuntimeError('unavailable')): mod.Config()
  self.assertIn('password_b64',json.loads(self.path.read_text()))
 def test_new_credentials(self):
  with patch.object(mod.keyring,'set_password') as store:
   c=mod.Config(); c.set_credentials('https://example.test','test','secret')
   store.assert_called_once_with('tecnomata-hifi','navidrome','secret')
  self.assertNotIn('secret',self.path.read_text())

if __name__=='__main__': unittest.main()
