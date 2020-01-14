import contextlib
import unittest
import os
import pandas as pd
import nordypy
from teradatasql import TeradataConnection

class TeradataTests(unittest.TestCase):
    def test_teradata_get_data(self):
        # pull some data from data
        sql = nordypy._get_secret('nordypy_teradata')['get_data']
        data = nordypy.database_get_data(database_key=database_key, yaml_filepath=yaml_filepath, sql=sql, as_pandas=True)  
        assert len(data) == 10 

    def test_teradata_execute(self):
        # create temp table from select and pull the data and check the length
        sql = nordypy._get_secret('nordypy_teradata')['execute']
        data = nordypy.database_execute(database_key=database_key, yaml_filepath=yaml_filepath, sql=sql, 
                                         return_data=True, as_pandas=True)  
        assert len(data) == 10 

    def test_teradata_connect(self):
        # test connection to teradata
        conn = nordypy.database_connect(database_key=database_key, yaml_filepath=yaml_filepath)
        assert isinstance(conn, TeradataConnection)
        conn.close()

if __name__ == '__main__':
    database_key = 'teradata'
    yaml_filepath = '~/config.yaml'
    unittest.main()
