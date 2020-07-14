import unittest
import os
import nordypy

class SecretsTest(unittest.TestCase):
    def test_get_secrets(self):
        secrets = nordypy._get_secret('redshift/dsa')
        assert type(secrets) == dict

if __name__ == '__main__':
	unittest.main()
