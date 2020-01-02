import contextlib
import unittest
import os
import pandas as pd
import nordypy

class S3Tests(unittest.TestCase):
    def test_s3_get_matching_s3_objects(self):
        bucket = 'nordypy'
        objs = [obj for obj in nordypy.get_matching_s3_objects(bucket=bucket)]
        assert type(objs) == list 
        assert type(objs[0]['Key']) == str

    def test_s3_get_matching_s3_keys(self):
        bucket = 'nordypy'
        keys = [key for key in nordypy.get_matching_s3_keys(bucket=bucket)]
        assert type(keys) == list 

if __name__ == '__main__':
	unittest.main()
