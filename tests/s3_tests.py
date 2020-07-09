import contextlib
import unittest
import os
import pandas as pd
import nordypy

class S3Tests(unittest.TestCase):
    def test_s3_get_matching_objects(self):
        bucket = 'data-scientist-share'
        objs = []
        for i, o in enumerate(nordypy.s3_get_matching_objects(bucket=bucket)):
            objs.append(o)
            if i == 10:
                break
        assert type(objs) == list 
        assert type(objs[0]['Key']) == str

    def test_s3_get_matching_keys(self):
        bucket = 'data-scientist-share'
        keys = []
        for i, k in enumerate(nordypy.s3_get_matching_keys(bucket=bucket, prefix='nordypy')):
            keys.append(k)
            if i == 10:
                break
        assert type(keys) == list 

    def test_upload_list(self):
        bucket = 'data-scientist-share'
        s3_folderpath = ['data/test/', 'data/test1/']
        local_filepath = ['abc{}.txt'.format(str(i)) for i, s in enumerate(s3_folderpath)]
        # Creating dummy files
        for f in local_filepath:
            if not os.path.isfile(f):
                open(f, 'w').close()
        with self.assertRaises(ValueError):
            self.assertEqual(nordypy.s3_upload(bucket = bucket, 
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
        
        self.assertEqual(nordypy.s3_upload(bucket = bucket, 
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

        self.assertEqual(nordypy.s3_upload(bucket = bucket, 
                                                s3_folderpath = s3_folderpath, 
                                                local_filepath = local_filepath), True)
        # Remove dummy files
        for l in local_filepath:
            os.remove(l)

    def test_s3_folderpath_datatype_check(self):
        bucket = 'data-scientist-share'
        s3_folderpath = ['data/test']
        local_filepath = ['abc.txt', 'abc1.txt']
        with self.assertRaises(ValueError):
            nordypy.s3_upload(bucket = bucket, 
                                   s3_folderpath = s3_folderpath, 
                                   local_filepath = local_filepath)

    def test_local_filepath_valid(self):
        bucket = 'data-scientist-share'
        s3_folderpath = ['data/test']
        local_filepath = ['aabc.txt']
        with self.assertRaises(ValueError):
            nordypy.s3_upload(bucket = bucket, 
                                   s3_folderpath = s3_folderpath, 
                                   local_filepath = local_filepath)

    def test_file_folder_isNone(self):
        bucket = 'data-scientist-share'
        s3_filepath = None
        s3_folderpath = None
        local_filepath = ['abc.txt', 'abc1.txt']
        with self.assertRaises(ValueError):
            nordypy.s3_upload(bucket = bucket, 
                            s3_filepath = None,
                            s3_folderpath = None, 
                            local_filepath = local_filepath)


    def test_length_check_s3filepath(self):
        bucket = 'data-scientist-share'
        s3_filepath = ['data/test/test.txt']
        local_filepath = ['abc.txt', 'abc1.txt']
        with self.assertRaises(ValueError):
            nordypy.s3_upload(bucket = bucket, 
                                   s3_filepath = s3_filepath, 
                                   local_filepath = local_filepath)

    def test_upload_list_s3filepath(self):
        bucket = 'data-scientist-share'
        s3_filepath = ['data/test/test1.txt', 'data/test1/test2.txt']
        local_filepath = ['abc{}.txt'.format(str(i)) for i, s in enumerate(s3_filepath)]
        # Creating dummy files
        for f in local_filepath:
            if not os.path.isfile(f):
                open(f, 'w').close()

        self.assertEqual(nordypy.s3_upload(bucket = bucket, 
                                                s3_filepath = s3_filepath, 
                                                local_filepath = local_filepath), True)
        # Removing dummy files
        for l in local_filepath:
            os.remove(l)

    def test_upload_single_file_s3filepath(self):
        bucket = 'data-scientist-share'
        s3_filepath = 'data/test/test.txt'
        local_filepath = 'abc.txt'
        # Create dummy file
        if not os.path.isfile(local_filepath):
            open(local_filepath, 'w').close()
        
        self.assertEqual(nordypy.s3_upload(bucket = bucket, 
                                                s3_filepath = s3_filepath, 
                                                local_filepath = local_filepath), True)
        # Remove dummy file
        os.remove(local_filepath)


if __name__ == '__main__':
	unittest.main()

