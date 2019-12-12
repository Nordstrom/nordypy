import contextlib
import unittest
import os
import pandas as pd
import nordypy

class AthenaTests(unittest.TestCase):
    def test_get_athena_data(self):
        sql = nordypy._get_secret('nordyathena')['nordyathenasql']
        bucket = nordypy._get_secret('nordyathena')['bucket']
        data = nordypy.athena_to_pandas(sql=sql, bucket=bucket)  
        assert len(data) == 10 

if __name__ == '__main__':
	unittest.main()
