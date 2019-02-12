import nordypy
import unittest
import psycopg2.extensions
from psycopg2 import ProgrammingError
import pandas as pd

# check that the redshift make table won't create VARCHAR(0) or any VARCHAR over 60000
class DataSourceConnectionTests(unittest.TestCase):
    def test_database_connect_bash(self):
        # connect with bash variable
        conn = nordypy.database_connect('TEST_CREDS')
        self.assertIsInstance(conn, psycopg2.extensions.connection)
        conn.close()

    def test_database_connect_YAML(self):
        # connect with YAML variable
        conn = nordypy.database_connect(database_key, yaml_filepath)
        self.assertIsInstance(conn, psycopg2.extensions.connection)
        conn.close()

    def test_database_connect_YAML_assume_config_yaml(self):
        conn = nordypy.database_connect(database_key)
        self.assertIsInstance(conn, psycopg2.extensions.connection)
        conn.close()

    def test_database_connect_YAML_change_order(self):
        conn = nordypy.database_connect(yaml_filepath, database_key)
        self.assertIsInstance(conn, psycopg2.extensions.connection)
        conn.close()

    def test_database_connect_YAML_kwargs(self):
        conn = nordypy.database_connect(yaml_filepath=yaml_filepath,
                                        database_key=database_key)
        self.assertIsInstance(conn, psycopg2.extensions.connection)
        conn.close()

    def test_database_connect_YAML_need_key(self):
        self.assertRaises(ValueError, lambda: nordypy.database_connect(yaml_filepath=yaml_filepath))

    def test_database_connect_need_args(self):
        self.assertRaises(ValueError, lambda: nordypy.database_connect())

    def test_database_connect_YAML_wrong_key(self):
        self.assertRaises(KeyError, lambda: nordypy.database_connect(yaml_filepath=yaml_filepath,
                                                                     database_key='wrong_key'))

    def test_database_connect_YAML_change_directory(self):
        conn = nordypy.database_connect(database_key=database_key,
                                        yaml_filepath='~/config.yaml')
        self.assertIsInstance(conn, psycopg2.extensions.connection)
        conn.close()

    def test_database_connect_YAML_teradata(self):
        pass

    def test_database_connect_bash_teradata(self):
        pass

    def test_database_connect_yaml_mysql(self):
        pass

    def test_database_connect_bash_mysql(self):
        pass

    def test_database_connect_no_dbtype(self):
        pass

class QueryGroupMethods(unittest.TestCase):

    def test_database_get_data_assign_query_group(self):
        pass

    def test_assign_query_group(self):
        self.assertEqual("set query_group to 'QG_S';", nordypy._command_generation._assign_query_group('small'))
        self.assertEqual("set query_group to 'QG_S';", nordypy._command_generation._assign_query_group('Small'))
        self.assertRaises(ValueError, lambda: nordypy._command_generation._assign_query_group('smaladsf'))


class DatabaseMethods(unittest.TestCase):

    def test_read_SQL_file(self):
        sql = 'SELECT TOP 100 *\nFROM ANALYTICS_USER_VWS.NORDYPY_TEST;'
        self.assertIsInstance(nordypy.read_sql_file('test.sql'), str)
        self.assertEqual(nordypy.read_sql_file('test.sql'), sql)

    def test_database_get_data(self):
        sql = 'select top 10 * from {};'.format(table)
        data = nordypy.database_get_data(database_key=database_key,
                                         yaml_filepath=yaml_filepath,
                                         sql=sql)
        self.assertEqual(len(data), 10)

    def test_database_execute(self):
        finished = nordypy.database_execute(database_key=database_key,
                                            yaml_filepath=yaml_filepath,
                                            sql=multi_sql)
        self.assertEqual(finished, True)

    def test_database_execute_pandas(self):
        data = nordypy.database_execute(database_key=database_key,
                                        yaml_filepath=yaml_filepath,
                                        sql=multi_sql,
                                        as_pandas=True)
        self.assertEqual(data.columns[0], 'pclass')
        self.assertEqual(data.shape, (3, 3))

    def test_database_execute_return_data(self):
        data = nordypy.database_execute(database_key=database_key,
                                        yaml_filepath=yaml_filepath,
                                        sql=multi_sql,
                                        return_data=True)
        self.assertEqual(len(data), 3)

    def test_database_analyze_table(self):
        analysis = nordypy.database_analyze_table(database_key=database_key,
                                                  yaml_filepath=yaml_filepath,
                                                  table='nordypy_test',
                                                  schema='analytics_user_vws')
        self.assertEqual(len(analysis), 1)
        self.assertEqual(len(analysis.columns), 11)

    def test_database_analyze_table_missing_parameters(self):
        # no table
        self.assertRaises(ValueError, lambda: nordypy.database_analyze_table(database_key= database_key,
                                                                             yaml_filepath=yaml_filepath,
                                                                             schema='analytics_user_vws'))
        # no schema
        self.assertRaises(ValueError, lambda: nordypy.database_analyze_table(database_key=database_key,
                                                                             yaml_filepath=yaml_filepath,
                                                                             table='nordypy_test'))
    def test_database_analyze_schema_dot_table(self):
        analysis = nordypy.database_analyze_table(database_key= database_key,
                                                  yaml_filepath=yaml_filepath,
                                                  table='public.nordypy_test')
        self.assertEqual(len(analysis), 0) # table doesn't actually exist
        self.assertEqual(len(analysis.columns), 11)

    def test_database_get_data_with_conn(self):
        sql = 'select top 10 * from {};'.format(table)
        conn = nordypy.database_connect(database_key=database_key,
                                        yaml_filepath=yaml_filepath)
        data = nordypy.database_get_data(conn=conn, sql=sql)
        conn.close()
        self.assertEqual(len(data), 10)

    def test_database_get_data_pandas(self):
        sql = 'select top 10 * from {};'.format(table)
        data = nordypy.database_get_data(yaml_filepath=yaml_filepath,
                                         database_key=database_key,
                                         sql=sql,
                                         as_pandas=True)
        print(data.shape)
        print(data.columns)
        print(type(data))
        self.assertEqual(data.shape, (10, 14))

    def test_redshift_to_s3(self):
        redshift_data = nordypy.database_get_data(database_key=database_key,
                                          yaml_filepath=yaml_filepath,
                                          sql='select * from {}'.format(table),
                                          as_pandas=True)
        nordypy.redshift_to_s3(database_key=database_key,
                               yaml_filepath=yaml_filepath,
                               select_sql="select * from {};".format(table),
                               bucket=bucket, s3_filepath='redshift_to_s3_test',
                               parallel=False,
                               delimiter='|')
        s3_data = nordypy.s3_to_pandas(bucket=bucket,
                                       s3_filepath='redshift_to_s3_test000',
                                       delimiter='|')
        self.assertEqual(redshift_data.shape, s3_data.shape)

    def test_redshift_to_s3_with_conn(self):
        # create a connection
        conn = nordypy.database_connect(database_key=database_key,
                                        yaml_filepath=yaml_filepath)
        # create a temporary table using the connection
        nordypy.database_execute(conn=conn,
                                 sql='create table #temp as (select top 100 * from {});'.format(table))
        # access that same connection to move data to s3
        nordypy.redshift_to_s3(select_sql="select * from #temp;",
                               conn=conn,
                               bucket=bucket,
                               s3_filepath='redshift_to_s3_test_conn',
                               parallel=False,
                               delimiter='|')
        # pull the temp data from redshift
        redshift_data = nordypy.database_get_data(conn=conn,
                                         sql='select * from #temp',
                                         as_pandas=True)
        self.assertEqual(redshift_data.shape, (100, 14))
        s3_data = nordypy.s3_to_pandas(bucket=bucket,
                                    s3_filepath='redshift_to_s3_test_conn000',
                                    delimiter='|')
        self.assertEqual(redshift_data.shape, s3_data.shape)


if __name__ == '__main__':
    create_statement = "CREATE TABLE analytics_user_vws.nordypy_test (pclass FLOAT4,survived FLOAT4,name VARCHAR(200),sex VARCHAR(100),age FLOAT4,sibsp FLOAT4,parch FLOAT4,ticket VARCHAR(100),fare FLOAT4,cabin VARCHAR(100),embarked VARCHAR(100),boat VARCHAR(100),body FLOAT4,home_dest VARCHAR(100));"
    get_columns = "SELECT column_name FROM information_schema.columns WHERE table_schema = 'analytics_user_vws' AND table_name = 'nordypy_test' ORDER BY ordinal_position"
    table = 'analytics_user_vws.nordypy_test'
    multi_sql = 'create table #temporary as (select pclass, survived, count(*) from analytics_user_vws.nordypy_test group by pclass, survived); select * from #temporary where survived = 1;'
    database_key = 'test_redshift'
    yaml_filepath = 'test_config.yaml'
    bucket = 'nordypy'
    unittest.main()
