import contextlib
import unittest
import os
import pandas as pd
import numpy as np
import nordypy
import textwrap
from teradatasql import TeradataConnection
from sqlalchemy.engine.base import Engine
from psycopg2.extensions import connection

'''
For whatever reason, you can't run the redshift tests in the same run as the Teradata tests. 

So to test redshift, comment out all other tests.
To test everything but redshift, comment out redshift tests.
'''

# class TeradataTests(unittest.TestCase):
#     def test_teradata_get_data(self):
#         # pull some data from data
#         sql = nordypy._get_secret('nordypy_teradata')['get_data']
#         data = nordypy.database_get_data(database_key=database_key_teradata, yaml_filepath=yaml_filepath, sql=sql, as_pandas=True)  
#         assert len(data) == 10 

#     def test_teradata_execute(self):
#         # create temp table from select and pull the data and check the length
#         sql = nordypy._get_secret('nordypy_teradata')['execute']
#         data = nordypy.database_execute(database_key=database_key_teradata, yaml_filepath=yaml_filepath, sql=sql, 
#                                          return_data=True, as_pandas=True)  
#         assert len(data) == 10 

#     def test_teradata_connect(self):
#         # test connection to teradata
#         conn = nordypy.database_connect(database_key=database_key_teradata, yaml_filepath=yaml_filepath)
#         assert isinstance(conn, TeradataConnection)
#         conn.close()

#     def test_ENV_teradata_get_data(self):
#         # pull some data from data
#         sql = nordypy._get_secret('nordypy_teradata')['get_data']
#         data = nordypy.database_get_data(database_key=database_key_teradata_ENV, sql=sql, as_pandas=True)  
#         assert len(data) == 10 

#     def test_ENV_teradata_execute(self):
#         # create temp table from select and pull the data and check the length
#         sql = nordypy._get_secret('nordypy_teradata')['execute']
#         data = nordypy.database_execute(database_key=database_key_teradata_ENV, sql=sql, 
#                                          return_data=True, as_pandas=True)  
#         assert len(data) == 10 

#     def test_ENV_teradata_connect(self):
#         # test connection to teradata
#         conn = nordypy.database_connect(database_key=database_key_teradata_ENV)
#         assert isinstance(conn, TeradataConnection)
#         conn.close()

#     def test_ENV_teradata_get_data_with_connection(self):
#         sql = nordypy._get_secret('nordypy_teradata')['get_data']
#         conn = nordypy.database_connect(database_key=database_key_teradata_ENV)
#         data = nordypy.database_get_data(conn=conn, sql=sql, as_pandas=True)  
#         assert len(data) == 10 
#         conn.close()

# class PrestoTest(unittest.TestCase):
#     # presto needs aws-okta to be
#     def test_presto_get_data(self):
#         sql = nordypy._get_secret('nordypy_presto')['get_data']
#         data = nordypy.database_get_data(database_key=database_key_presto, yaml_filepath=yaml_filepath, sql=sql, as_pandas=True)  
#         assert len(data) == 10 

#     def test_presto_execute(self):
#         sql = nordypy._get_secret('nordypy_presto')['execute']
#         data = nordypy.database_execute(database_key=database_key_presto, yaml_filepath=yaml_filepath, sql=sql, as_pandas=True, return_data=True)
#         assert data.shape == (0, 2)

#     def test_presto_connect(self):
#         conn = nordypy.database_connect(database_key=database_key_presto, yaml_filepath=yaml_filepath)
#         assert conn.dbtype == 'presto'
#         conn.dispose()

class RedshiftTest(unittest.TestCase):
    def test_redshift_get_data(self):
        sql = nordypy._get_secret('nordypy_redshift')['get_data']
        data = nordypy.database_get_data(database_key=database_key_redshift, yaml_filepath=yaml_filepath, sql=sql, as_pandas=True)  
        assert len(data) == 10 

    def test_redshift_execute(self):
        pass

    def test_redshift_connect(self):
        conn = nordypy.database_connect(database_key=database_key_redshift, yaml_filepath=yaml_filepath)
        assert isinstance(conn, connection)
        conn.close()

    def test_redshift_data_to_redshift(self):
        # test moving data to redshfit without a connection, using yaml
        table_name = nordypy._get_secret('nordypy_redshift')['redshift_table']
        n = 10
        data = pd.DataFrame({'index': [i for i in range(n)], 
                             'value': [np.random.choice(['nordypy', 'test', 'data']) for _ in range(n)]})
        nordypy.data_to_redshift(database_key=database_key_redshift, 
                                 yaml_filepath=yaml_filepath, 
                                 data=data, 
                                 bucket=bucket, 
                                 table_name=table_name, 
                                 drop_table=True)
        data = nordypy.database_get_data(database_key=database_key_redshift, 
                                         yaml_filepath=yaml_filepath, 
                                         sql=f'select * from {table_name}', 
                                         as_pandas=True)  
        assert len(data) == n 

    def test_redshift_redshift_to_s3_with_connection(self):
        sql = nordypy._get_secret('nordypy_redshift')['select_sql']
        s3_filepath = 'redshift_to_s3_test'
        nordypy.redshift_to_s3(database_key=database_key_redshift, yaml_filepath=yaml_filepath, 
                               bucket=bucket, select_sql=sql, s3_filepath=s3_filepath, parallel=False)
        data = nordypy.s3_to_pandas(bucket=bucket, s3_filepath=s3_filepath + '000', header=None)
        assert len(data) == 10

    # use ENV variables

    def test_ENV_redshift_get_data(self):
        sql = nordypy._get_secret('nordypy_redshift')['get_data']
        data = nordypy.database_get_data(database_key=database_key_redshift_ENV, sql=sql, as_pandas=True)  
        assert len(data) == 10 

    def test_ENV_redshift_execute(self):
        pass

    def test_ENV_redshift_connect(self):
        conn = nordypy.database_connect(database_key=database_key_redshift_ENV)
        assert isinstance(conn, connection)
        conn.close()

    def test_ENV_redshift_get_data_with_connection(self):
        sql = nordypy._get_secret('nordypy_redshift')['get_data']
        conn = nordypy.database_connect(database_key=database_key_redshift_ENV)
        data = nordypy.database_get_data(conn=conn, sql=sql, as_pandas=True)  
        assert len(data) == 10 
        conn.close()

    def test_ENV_redshift_data_to_redshift_with_connection(self):
        # test moving data to redshift with a connection made from ENV
        table_name = nordypy._get_secret('nordypy_redshift')['redshift_table']
        n = 10
        data = pd.DataFrame({'index': [i for i in range(n)], 
                             'value': [np.random.choice(['nordypy', 'test', 'data']) for _ in range(n)]})
        conn = nordypy.database_connect(database_key=database_key_redshift_ENV)
        nordypy.data_to_redshift(data=data, conn=conn, bucket=bucket, table_name=table_name, drop_table=True)
        data = nordypy.database_get_data(conn=conn, sql=f'select * from {table_name}', as_pandas=True)  
        assert len(data) == n 
        conn.close()

    def test_ENV_redshift_redshift_to_s3_with_connection(self):
        # test moving data to redshift with a connection made from ENV
        sql = nordypy._get_secret('nordypy_redshift')['select_sql']
        s3_filepath = 'redshift_to_s3_test'
        conn = nordypy.database_connect(database_key=database_key_redshift_ENV)
        nordypy.redshift_to_s3(conn=conn, bucket=bucket, select_sql=sql, s3_filepath=s3_filepath, parallel=False)
        data = nordypy.s3_to_pandas(bucket=bucket, s3_filepath=s3_filepath + '000', header=None)
        assert len(data) == 10
        conn.close()


class DatabaseTests(unittest.TestCase):
    def test_sql_stripper(self):
        SQL = """
        /*
        select * from jimbo.jones;
        */

        -- select * from nelson.muntz'

        
        select * from waylon.smithers
        """

        sql = nordypy._datasource._strip_sql(textwrap.dedent(SQL))

        assert sql == '\nselect * from waylon.smithers\n'

    # def test_autocommit(self):
    #     conn = nordypy.database_connect(database_key=database_key_redshift, yaml_filepath=yaml_filepath)
    #     self.assertTrue(conn.autocommit)

if __name__ == '__main__':
    database_key_redshift = 'redshift'
    database_key_teradata = 'teradata'
    database_key_presto = 'presto'
    yaml_filepath = 'config.yaml'
    bucket='nordypy'
    # ENV env
    database_key_redshift_ENV = 'TEST_REDSHIFT'
    database_key_teradata_ENV = 'TEST_TERADATA'
    unittest.main(warnings='ignore')
