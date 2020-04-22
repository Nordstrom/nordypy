import contextlib
import unittest
import os
import pandas as pd
import nordypy

class S3Tests(unittest.TestCase):
    # def test_s3_get_matching_objects(self):
    #     bucket = 'data-scientist-share'
    #     objs = [obj for obj in nordypy.s3_get_matching_objects(bucket=bucket)]
    #     assert type(objs) == list 
    #     assert type(objs[0]['Key']) == str

    # def test_s3_get_matching_keys(self):
    #     bucket = 'data-scientist-share'
    #     keys = [key for key in nordypy.s3_get_matching_keys(bucket=bucket, prefix='nordypy')]
    #     print(keys)
    #     assert type(keys) == list 

    def test_upload_list(self):
        bucket = 'data-scientist-share'
        s3_filepath = ['data/test/', 'data/test1/']
        local_filepaths = ['abc2.txt', 'sales_events.csv']
        self.assertEqual(nordypy.s3_upload_test(bucket, s3_filepath, local_filepaths), True)

    def test_upload_single_file(self):
        bucket = 'data-scientist-share'
        s3_filepath = 'data/test/'
        local_filepath = 'abc3.txt'
        self.assertEqual(nordypy.s3_upload_test(bucket, s3_filepath, local_filepath), True)

    def test_upload_single_s3path_multiple_files(self):
        bucket = 'data-scientist-share'
        s3_filepath = 'data/test/'
        local_filepaths = ['abc4.txt', 'abc5.txt']
        self.assertEqual(nordypy.s3_upload_test(bucket, s3_filepath, local_filepaths), True)

    def test_length_check(self):
        bucket = 'data-scientist-share'
        s3_filepath = ['data/test']
        local_filepaths = ['abc.txt', 'abc1.txt']
        with self.assertRaises(ValueError):
            nordypy.s3_upload_test(bucket, s3_filepath, local_filepaths)

    def test_local_filepath_valid(self):
        bucket = 'data-scientist-share'
        s3_filepath = ['data/test']
        local_filepaths = ['aabc.txt']
        with self.assertRaises(ValueError):
            nordypy.s3_upload_test(bucket, s3_filepath, local_filepaths)

if __name__ == '__main__':
	unittest.main()
