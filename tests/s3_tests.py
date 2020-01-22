import contextlib
import unittest
import os
import pandas as pd
import nordypy

class S3Tests(unittest.TestCase):
    def test_s3_get_matching_objects(self):
        bucket = 'nordypy'
        objs = [obj for obj in nordypy.s3_get_matching_objects(bucket=bucket)]
        assert type(objs) == list 
        assert type(objs[0]['Key']) == str

    def test_s3_get_matching_keys(self):
        bucket = 'nordypy'
        keys = [key for key in nordypy.s3_get_matching_keys(bucket=bucket, prefix='nordypy')]
        print(keys)
        assert type(keys) == list 

if __name__ == '__main__':
	unittest.main()
