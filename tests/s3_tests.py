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
        s3_folderpath = ['data/test/', 'data/test1/']
        local_filepath = ['abc{}.txt'.format(str(i)) for i, s in enumerate(s3_folderpath)]
        # Creating dummy files
        for f in local_filepath:
            if not os.path.isfile(f):
                open(f, 'w').close()

        self.assertEqual(nordypy.s3_upload_test(bucket = bucket, 
                                                s3_folderpath = s3_folderpath, 
                                                local_filepath = local_filepath), True)
        # Removing dummy files
        for l in local_filepath:
            os.remove(l)

    def test_upload_single_file(self):
        bucket = 'data-scientist-share'
        s3_folderpath = 'data/test/'
        local_filepath = 'abc.txt'
        # Create dummy file
        if not os.path.isfile(local_filepath):
            open(local_filepath, 'w').close()
        
        self.assertEqual(nordypy.s3_upload_test(bucket = bucket, 
                                                s3_folderpath = s3_folderpath, 
                                                local_filepath = local_filepath), True)
        # Remove dummy file
        os.remove(local_filepath)

    def test_upload_single_s3path_multiple_files(self):
        bucket = 'data-scientist-share'
        s3_folderpath = 'data/test/'
        local_filepath = ['abc.txt', 'abc1.txt']
        # Create dummy files
        for f in local_filepath:
            if not os.path.isfile(f):
                open(f, 'w').close()

        self.assertEqual(nordypy.s3_upload_test(bucket = bucket, 
                                                s3_folderpath = s3_folderpath, 
                                                local_filepath = local_filepath), True)
        # Remove dummy files
        for l in local_filepath:
            os.remove(l)

    def test_length_check(self):
        bucket = 'data-scientist-share'
        s3_folderpath = ['data/test']
        local_filepath = ['abc.txt', 'abc1.txt']
        with self.assertRaises(ValueError):
            nordypy.s3_upload_test(bucket = bucket, 
                                   s3_folderpath = s3_folderpath, 
                                   local_filepath = local_filepath)

    def test_local_filepath_valid(self):
        bucket = 'data-scientist-share'
        s3_folderpath = ['data/test']
        local_filepath = ['aabc.txt']
        with self.assertRaises(ValueError):
            nordypy.s3_upload_test(bucket = bucket, 
                                   s3_folderpath = s3_folderpath, 
                                   local_filepath = local_filepath)

if __name__ == '__main__':
	unittest.main()

