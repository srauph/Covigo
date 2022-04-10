from django.test import TestCase
from messaging.utils import (RSAEncryption)
import tempfile
from pathlib import Path


class RSAEncryptionTests(TestCase):
    def setUp(self):
        # with tempfile.TemporaryDirectory() as keydir:
        keydir = tempfile.mkdtemp()
        keydir = Path(keydir)
        self.encryption = RSAEncryption(keydir)
        self.encryption.generate_keys()

    def test_encryption_roundtrip(self):
        message = "Hello World!"
        encrypted_message = self.encryption.encrypt(message)
        decrypted_message = self.encryption.decrypt(encrypted_message)
        self.assertEqual(message, decrypted_message)
