import psycopg2
from psycopg2 import sql
import teradatasql
import pymysql
import os, sys, re
import yaml
import pandas as pd
from boto3.exceptions import S3UploadFailedError
from . import _redshift_utils
from ._s3 import _s3_get_temp_creds
from ._s3 import pandas_to_s3, s3_to_redshift
from ._command_generation import _create_table_statement
from ._command_generation import _create_insert_statement
from ._command_generation import _generate_unload_command
from ._command_generation import _assign_query_group
from ._secret import _get_secret


def database_analyze_table(database_key=None, yaml_filepath=None, table=None,
                           schema=None):
    """Analyze table stats in redshift. Will NOT work for teradata.

    Parameters
    ----------
    database_key : str
    yaml_filepath : str
    table : str
        table name in redshift, could also be the schema and table
        together ex. table='public.nordypy_test'
    schema : str
        table schema in redshift (ex. public)
    """
    if table is None:
        raise ValueError('Provide a table name: ex. sessions')
    if '.' in table:
        schema, table = table.split('.')
    if schema is None:
        raise ValueError('Provide a table schema: ex. public')
    sql = _redshift_utils.analyze_table.format(schema, table)
    result = database_get_data(database_key=database_key,
                               yaml_filepath=yaml_filepath,
                               sql=sql,
                               as_pandas=True)
    return result


def database_connect(database_key=None, yaml_filepath=None, autocommit=True):
    """Return a database connection object. Connect with YAML config or bash
    environment variables. Works for redshift, mysql, and teradata.

    Parameters
    ----------
    database_key : str
            indicates which yaml login you plan to use of the bash_variable key
            if no YAML file is provided
    yaml_filepath : str [optional]
            path to yaml file to connect
            if no yaml_file is given, will assume that the database_key is for
            a bash_variable

    Returns
    -------
    conn : Database Connection Object

    Examples
    --------
    # if connection in bash_profile
    conn = nordypy.database_connect('REDSHIFT')

    # yaml file with only one profile
    conn = nordypy.database_connect('config.yaml')

    # yaml file with multiple profiles
    conn = nordypy.database_connect('prod_redshift', 'config.yaml')
    """
    if yaml_filepath:
        try:
            with open(os.path.expanduser(yaml_filepath), 'r') as ymlfile:
                cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
        except (OSError, IOError):  # if out of order (for both python 2 and 3)
            temp_filepath = database_key
            database_key = yaml_filepath
            with open(os.path.expanduser(temp_filepath), 'r') as ymlfile:
                cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
        if _dict_depth(cfg) != 1:
            if database_key:
                cfg = cfg[database_key]
            else:
                raise ValueError(
                    'YAML file contains multiple datasource profiles. Provide a datasource key.')
        if 'secret_name' in cfg:
            if  'region_name' in cfg:
                cfg = _get_secret(cfg['secret_name'], region_name = cfg['region_name'])
            else:
                print("You are trying to access AWS secrets and need region_name.")
                print("Please specify region_name in config.yaml (e.g., us-west-2)")
                print("Exiting now.")
                sys.exit()
        if 'dbtype' not in cfg:
            print("UserWarning: Update config.yaml with 'dbtype' parameter: ['redshift', 'mysql', 'teradata'] -- ")
        if 'dbtype' in cfg:
            if cfg['dbtype'] == 'mysql':
                conn = __mysql_connect(cfg, autocommit=autocommit)
            elif cfg['dbtype'] == 'teradata':
                conn = __teradata_connect(cfg)
            else:
                conn = __redshift_connect(cfg, autocommit=autocommit)
        else:
            # default to redshift database
            conn = __redshift_connect(cfg, autocommit=autocommit)

    elif database_key:
        try:
            try:
                # redshift
                conn = psycopg2.connect(os.environ[database_key], autocommit=autocommit)
            except psycopg2.OperationalError:
                # mysql
                conn = pymysql.connect(os.environ[database_key], autocommit=autocommit)
        except (KeyError, pymysql.err.OperationalError):
            # for the case where positional arguments were used and the
            # datasource was actually the YAML path
            try:
                conn = database_connect(yaml_filepath='config.yaml',
                                        database_key=database_key,
                                        autocommit=autocommit)
            except:
                yaml_filepath = database_key
                conn = database_connect(yaml_filepath=yaml_filepath,
                                        database_key=None,
                                        autocommit=autocommit)
    else:
        raise ValueError('Provide a YAML file path or a connection string via a bash_variable')
    return conn

def __redshift_connect(cfg, autocommit=True):
    con = psycopg2.connect(host=cfg['host'],
                           dbname=cfg['dbname'],
                           password=cfg['password'],
                           port=cfg['port'],
                           user=cfg['user'])
    con.autocommit = autocommit
    
    return con

def __mysql_connect(cfg, autocommit=True):
    return pymysql.connect(host=cfg['host'],
                           db=cfg['dbname'],
                           password=cfg['password'],
                           port=cfg['port'],
                           user=cfg['user'],
                           autocommit=autocommit)

def __teradata_connect(cfg):
    config = {
        'host': cfg['host'],
        'password': cfg['password'],
        'user': cfg['user']
    }

    if cfg['use_ldap']:
        config['logmech'] = 'LDAP'

    if 'port' in cfg.keys():
        config['dbs_port'] = cfg['port']

    if 'database' in cfg.keys():
        config['database'] = cfg['database']

    return teradatasql.connect(**config)

def database_drop_table(table_name=None, database_key=None, yaml_filepath=None,
                        conn=None):
    """
    Drop table in if exists. Will NOT work for teradata.

    Parameters
    ----------
    table_name : str
            - schema.table
    database_key (str)
            - bash or yaml variable
    yaml_filepath (str)
            - where if the yaml file
    conn (psycopg2 connection)

    Returns
    -------
    None

    Examples
    --------
    nordypy.datasource_drop_table('public.nordypy_test', 'REDSHIFT')
    """
    drop_statement = 'DROP TABLE IF EXISTS {};'.format(table_name)
    close_connection = False
    if not conn:
        conn = database_connect(database_key=database_key, yaml_filepath=yaml_filepath)
        close_connection = True
    cursor = conn.cursor()
    try:
        cursor.execute(drop_statement)
        conn.commit()
        cursor.close()
        print('{} table dropped'.format(table_name))
    except psycopg2.ProgrammingError as e:
        print(e)
    if close_connection:
        conn.close()
    return True


def database_create_table(data=None, table_name='', make_public=True,
                          database_key=None, yaml_filepath=None,
                          create_statement=None, conn=None):
    """
    Create blank table. Can use premade statement or autogenerate the create
    statement based on the data input. Will NOT work for teradata.

    Parameters
    ----------
    data (dataframe or filepath)
            - required
    table_name (str)
            - schema.tablename to be built in the database
    make_public (boolean)
            - should the table be made public
    database_key (str)
            - yaml or bash key
    yaml_filepath (str) [optional]
            - path and file name of yaml file
    create_statement (str or filepath)
            - create sql or sql file
    conn (psycopg2 Conn)

    Returns
    -------
    None

    Examples
    --------
    # automatically from pandas dataframe
    nordypy.database_create_table(data=df,
                                  table_name='schema.my_table',
                                  yaml_filepath='~/config.yaml',
                                  database_key='REDSHIFT')

    # using create statement
    create_statement = 'create table public.nordypy_test (name VARCHAR(100), value INT);'
    nordypy.database_create_table(create_statement=create_statement,
                                  database_key='REDSHIFT')
    """
    close_connection = False

    if not conn:
        conn = database_connect(database_key=database_key,
                                yaml_filepath=yaml_filepath)
        close_connection = True

    if not create_statement:
        create_statement = _create_table_statement(data, table_name=table_name, conn=conn)

    cursor = conn.cursor()

    try:
        if create_statement.endswith('.sql'):
            create_statement = read_sql_file(create_statement)

        cursor.execute(create_statement)
        conn.commit()
        print('{} table created'.format(table_name))

        if make_public:
            grant_sql = 'GRANT ALL ON {} TO PUBLIC;'.format(table_name)
            cursor.execute(grant_sql)
            print('Access to {} granted to all'.format(table_name))
            conn.commit()
        cursor.close()
    except psycopg2.ProgrammingError as e:
        print(e)
    if close_connection:
        conn.close()
    return True


def database_insert(data=None, table_name='', database_key=None,
                    yaml_filepath=None, insert_statement=None, conn=None,
                    query_group=None):
    """
    Insert data into an already existing table. Can insert a full csv, a full
    pandas dataframe, a single tuple of data, or run an insert statement on
    tables already in the database. Will NOT work for teradata.

    Parameters
    ----------
    data (dataframe or filepath)
            - required
    table_name (str)
            - schema.tablename of table in the database
    database_key (str)
            - yaml or bash key
    yaml_filepath (str) [optional]
            - path and file name of yaml file
    insert_statement (str or filepath)
            - insert sql or sql file
    conn (psycopg2 Conn)
            - connection
    query_group (str)
            - None, 'small', 'medium', 'large'

    Returns
    -------
    None

    Examples
    --------
    # from single tuple
    data = (1, 2 ,3 ,4)

    # from a tuple of tuples
    data = ((1, 2, 3, 4),
                    (5, 6, 7, 8))

    # from single dictionary
    data = {'A':1, 'B':2, 'C':3, 'D':4}

    # from list of dictionaries
    data = [{'A':1, 'B':2, 'C':3, 'D':4},
                    {'A':5, 'B':6, 'C':7, 'D':8}]

    # from a dictionary of dictionaries
    data = {'bob': {'A':1, 'B':2, 'C':3, 'D':4},
                    'sally': {'A':5, 'B':6, 'C':7, 'D':8}}

    # from a pandas dataframe
    data = pd.DataFrame([(1,2,3, 4), (5, 6, 7, 8)])

    # from csv
    data = 'dir/file.csv'

    # from create statement
    insert_statement = 'insert into schema.my_table (select * from schema.other_table);'
    """
    # convert alternative types to dataframe and create insert_statement
    if not insert_statement:
        insert_statement = _create_insert_statement(data, table_name)
    # execute insert_statement
    database_execute(database_key=database_key,
                     yaml_filepath=yaml_filepath,
                     sql=insert_statement,
                     conn=conn,
                     query_group=query_group,
                     return_data=False,
                     as_pandas=False)
    print('Data inserted into table {}'.format(table_name))
    return None


def database_execute(database_key=None, yaml_filepath=None, sql=None,
                     conn=None, return_data=False, as_pandas=False,
                     query_group=None):
    """Excecute one or more sql statements. Works for redshift, mysql and teradata.

    Parameters

    ----------
    database_key :  str [REQUIRED]
        indicates which yaml login you plan to use of the bash_variable
        key if no YAML file is provided
    yaml_filepath : str [optional]
        path to yaml file to connect
        if no yaml_file is given, will assume that the database_key is
        for a bash_variable
    sql : str or filename
        single or multiple sql statements separated with ";" or filepath to
        sql file to be executed
    conn : connection object [optional]
        can provide a connection, if you want a consistent SQL session
    return_data : bool
        indcates that data should be returned from the final query
    as_pandas : bool
        if data is returned, should it be as a dataframe
    query_group : str
        assign query_group [None, 'default', 'small', 'medium', 'large']

    Returns
    -------

    """
    close_connection = False
    if sql.endswith('.sql'):
        with open(sql, 'r') as infile:
            sqlcode = infile.read()
    else:
        sqlcode = sql
    if ';' not in sqlcode:
        raise ValueError("SQL statements must contain ';'")

    sqlcode = _strip_sql(sqlcode)

    if query_group:
        sqlcode = _assign_query_group(size=query_group) + sqlcode
    sql_statements = sqlcode.split(';')[:-1]

    # get connection if not there
    if not conn:
        conn = database_connect(database_key=database_key, yaml_filepath=yaml_filepath)
        close_connection = True
    cursor = conn.cursor()

    if as_pandas is True:
        # assume if they want a pandas return that data should return too
        return_data = True
    if not return_data:
        for i, stmt in enumerate(sql_statements):
            cursor.execute(stmt)
            conn.commit()
            print('Statement {} finished'.format(i + 1))
        cursor.close()
        print('SQL Execution Finished')
        if close_connection:
            conn.close()
        return True
    else:
        if len(sql_statements) > 1:
            for i, stmt in enumerate(sql_statements[:-1]):
                cursor.execute(stmt)
                conn.commit()
                print('Statement {} finished'.format(i))
        if as_pandas:
            data = pd.read_sql(sql=sql_statements[-1], con=conn)
        else:
            data = database_get_data(conn=conn, sql=sql_statements[-1])
            print('SQL Execution Finished')
        if close_connection:
            conn.close()
        return data


def database_get_column_names(database_key=None, yaml_filepath=None,
                              table=None, schema=None, data_type=False):
    """Determine column names on a particular table. Will NOT work for teradata.

    Parameters
    ----------
    database_key : str
    yaml_filepath : str
    table : str
        table name in redshift, could also be the schema and table together
        ex. table='public.nordypy_test'
    schema : str
        table schema in redshift (ex. public)
    data_type : bool
        return column type
    """
    if table is None:
        raise ValueError('Provide a table name: ex. sessions')
    if '.' in table:
        schema, table = table.split('.')
    if schema is None:
        raise ValueError('Provide a table schema: ex. public')
    if data_type:
        sql = _redshift_utils.table_columns.format(', data_type ', schema, table)
    else:
        sql = _redshift_utils.table_columns.format('', schema, table)
    result = database_get_data(database_key=database_key,
                               yaml_filepath=yaml_filepath, sql=sql,
                               as_pandas=True)
    return result


def database_get_data(database_key=None, yaml_filepath=None, sql=None,
                      as_pandas=False, conn=None, query_group=None):
    """
    Helper function to connect to a datasource, run the specified sql
    statement(s), close the connection and return the result(s). 
    Works for redshift, mysql and teradata.

    Parameters
    ----------
    database_key : str [REQUIRED]
        indicates which yaml login you plan to use or the bash_variable
        key if no YAML file is provided
    yaml_filepath : str
        path to yaml file to connect
        if no yaml_file is given, will assume that the database_key is
        for a bash_variable
    sql : str or filename
        SQL to execute in redshift, can be single string or multiple
        statements
    conn : database connection
        database connection object if you want to pass in an already
        established connection
    as_pandas : bool
        return data as a pandas dataframe
    query_group : str
        assign query_group [None, 'default', 'small', 'medium', 'large']


    Returns
    -------
    data (Records from redshift)

            Examples
    --------
    sql = "select top 10 * public.my_table;"

    # yaml file with multiple profiles
    data = nordypy.database_get_data('dsa', 'config.yaml', sql)
    """
    # assign sql to proper variable if positional arguments used
    close_connection = False
    if not conn:
        # open a connection if not already
        if type(yaml_filepath) is str:
            if len(yaml_filepath.split()) > 1:
                sql = yaml_filepath
                yaml_filepath = None
        conn = database_connect(database_key, yaml_filepath)
        close_connection = True
    if as_pandas:
        if query_group:
            sql = _assign_query_group(size=query_group) + sql
        data = pd.read_sql(sql=sql, con=conn)
    else:
        cursor = conn.cursor()
        try:
            if query_group:
                query_group_sql = _assign_query_group(size=query_group)
                cursor.execute(query_group_sql)
                conn.commit()
            cursor.execute(sql)
            data = cursor.fetchall()
            cursor.close()
        except psycopg2.ProgrammingError as e:
            raise (e)
    if close_connection:
        conn.close()
    return data


def database_list_tables(schemaname=None, tableowner=None, searchstring=None,
                        database_key=None, yaml_filepath=None, conn=None):
    """
    List table names by schema and optionally by tableowner or tablename searchstring.
    Will NOT work for teradata.

    Parameters
    ----------
    schemaname : str
        schema name to search in
    tableowner : str
        description
    searchstring : str
        description
    database_key : str [REQUIRED]
        indicates which yaml login you plan to use or the bash_variable
        key if no YAML file is provided
    yaml_filepath : str
        path to yaml file to connect
        if no yaml_file is given, will assume that the database_key is
        for a bash_variable
    conn : database connection
        database connection object if you want to pass in an already
        established connection

    Returns
    -------
    tables : dataframe
        query results that includes schema name, table name and owner name

    Examples
    --------
    table_names = nordypy.database_list_tables(schemaname='analytics_user_vws',
                                               tableowner='clhq',
                                               searchstring=None,
                                               database_key='dsa',
                                               yaml_filepath='~/config.yaml')
    """
    sql = """SELECT schemaname, tablename, tableowner FROM pg_tables WHERE 1=1"""
    if schemaname:
        sql += """ AND schemaname = '{}'""".format(schemaname)
    if tableowner:
        sql += """ AND tableowner = '{}'""".format(tableowner)
    if searchstring:
        sql +=""" AND tablename LIKE '{}'""".format(searchstring)
    print('Running query: """{}"""'.format(sql))
    tables = database_get_data(database_key=database_key,
                                 yaml_filepath=yaml_filepath,
                                 sql=sql,
                                 conn=conn,
                                 as_pandas=True)
    return tables


def database_to_pandas(database_key=None, yaml_filepath=None, sql=None,
                       conn=None, query_group=None):
    """Convenience wrapper for for database_get_data to pandas function. 
    Works for redshift, mysql and teradata.
    """
    return database_get_data(database_key=database_key,
                             yaml_filepath=yaml_filepath,
                             sql=sql,
                             conn=conn,
                             as_pandas=True,
                             query_group=query_group)


def data_to_redshift(data, table_name, bucket, s3_filepath='temp',
                     database_key=None, yaml_filepath=None,
                     copy_command=None, create_statement=None, delimiter=None,
                     drop_table=False, environment=None,
                     region_name='us-west-2', profile_name=None):
    """
    Move data from pandas dataframe or csv to redshift. This function will automatically create a table in redshift if
    none exists, move the files up to s3 and then copy them to redshift from there. If a table already exists, the
    default behavior is to INSERT into the table.

    Parameters
    ----------
    data : dataframe or csv filepath [REQUIRED]
    table_name : str [REQUIRED]
            schema.tablename to be built in the database
    bucket : str [REQUIRED]
            name of S3 bucket to be used
    s3_filepath : str [required]
            upload location in s3
    database_key : str [REQUIRED]
            yaml or bash key
    yaml_filepath : str
            path and file name of yaml file
    copy_command : str or filepath
            copy command or path to copy command, will be generated if None
    create_statement : str or filepath
            prebuilt create sql or path to sql file, will be generated if None
    delimiter : None or str, default='|', ',', '\t'
            data delimiter
    drop_table : bool
            drop table if exists?
    environment : str, 'aws', 'local'
            where is this running?
    region_name : str
    profile_name : str

    Returns
    -------
    None

    Examples
    --------
    nordypy.data_to_redshift(data=df, table_name='public.my_table',
                             bucket='my_bucket',
                             s3_filepath='my_data/data_',
                             database_key='REDSHIFT')
    """

    if drop_table:
        database_drop_table(table_name=table_name, database_key=database_key,
                            yaml_filepath=yaml_filepath)
        database_create_table(data=data, table_name=table_name,
                              database_key=database_key,
                              yaml_filepath=yaml_filepath,
                              create_statement=create_statement)
    else:
        try:
            schema, name = table_name.split('.')
        except ValueError:
            schema = 'public'
            name = table_name
        table_exists = "select exists(select * from information_schema.tables where table_schema='{}' and table_name='{}');".format(
            schema, name)
        if not database_get_data(database_key=database_key,
                                 yaml_filepath=yaml_filepath, sql=table_exists,
                                 query_group='small')[0][0]:
            database_create_table(data=data,
                                  table_name=table_name,
                                  database_key=database_key,
                                  yaml_filepath=yaml_filepath,
                                  create_statement=create_statement)
    # upload data to s3
    pandas_to_s3(data=data, delimiter=delimiter, bucket=bucket,
                 s3_filepath=s3_filepath, environment=environment,
                 profile_name=profile_name)

    # copy from s3 to redshift
    s3_to_redshift(copy_command=copy_command, database_key=database_key,
                   yaml_filepath=yaml_filepath, environment=environment,
                   bucket=bucket, s3_filepath=s3_filepath,
                   redshift_table=table_name, delimiter=delimiter,
                   region_name=region_name, profile_name=profile_name)
    print('Data upload to Redshift via S3')
    return None


def read_sql_file(sql_filename=None):
    """
    Read in a SQL file as a string.

    Parameters
    ----------
    sql_filename : filename [REQUIRED]
        relative path to sql file

    Returns
    -------
    string containing the sql script

    Examples
    --------
    >>> sql = nordypy.read_sql_file('../SQL/myquery.sql')
    """
    with open(sql_filename) as sql_file:
        sql = sql_file.read()
    return sql


def redshift_to_redshift(yaml_filepath=None, database_key_from=None,
                         database_key_to=None, select_sql=None,
                         query_group=None, to_redshift_table=None, bucket=None,
                         s3_filepath=None, unload_command=None,
                         environment=None, region_name='us-west-2',
                         profile_name=None, delimiter='|', parallel=True,
                         gzip=True, manifest=False, allowoverwrite=True):
    """Move data from one redshift database to another."""
    try:
        redshift_to_s3(yaml_filepath=yaml_filepath,
                       database_key=database_key_from, select_sql=select_sql,
                       query_group=query_group, bucket=bucket,
                       s3_filepath=s3_filepath, environment=environment,
                       region_name=region_name, profile_name=profile_name,
                       unload_command=unload_command, delimiter=delimiter,
                       parallel=parallel, gzip=gzip, manifest=manifest,
                       allowoverwrite=allowoverwrite)
    except S3UploadFailedError as e:
        raise (e)
    try:
        s3_to_redshift()
    except:
        pass


def redshift_to_s3(database_key=None, yaml_filepath=None, select_sql=None,
                   query_group=None, conn=None, bucket=None, s3_filepath=None,
                   environment=None, region_name='us-west-2',
                   profile_name=None, unload_command=None, delimiter='|',
                   parallel=True, gzip=None, manifest=False,
                   allowoverwrite=True):
    """
    Select data from redshift and move to s3. You can provide your own unload
    command or have one generated for you.

    When the file gets written to S3, a 3-digit code will be appended ex. 000
    This is so it doesn't overwrite other files.

    Parameters
    ----------
    database_key : str [REQUIRED]
        bash or yaml variable
    yaml_filepath : str [REQUIRED]
        where if your yaml file
    select_sql : str or filename [REQUIRED]
        selection sql statement or just the table_name if you want to
        select * from table
    bucket : str [REQUIRED]
        s3 bucket to move things to
    s3_filepath : str [REQUIRED]
            - s3 file location in bucket
    query_group : str
        assign query_group [None, 'default', 'small', 'medium', 'large']
    conn : database connection
        database connection object if you want to pass in an already
        established connection
    environment : str
        where if the script running
    region_name : str
        where in AWS
    profile_name : str
        default 'nordstrom-federated'
    unload_command : str or filename
        unload sql
    delimiter : ('|', ',' or '\t')
        delimiter character for unloading
    parallel : bool
        unload into multiple files (parallel=True) or single file (False)
    gzip : bool
        apply compression
    manifest : bool
        include manifest when unloading

    Returns
    -------
    None

    Examples
    --------
    nordypy.redshift_to_s3(select_sql='public.nordypy_test',
                   database_key=key, environment=env, bucket=bucket,
                   s3_filepath='my_data/latest.csv')
    """
    close_connection = False
    cred_str = _s3_get_temp_creds(region_name=region_name,
                                  environment=environment,
                                  profile_name=profile_name)
    unload_command = _generate_unload_command(cred_str, select_sql, bucket,
                                              s3_filepath, delimiter, parallel,
                                              gzip, unload_command, manifest,
                                              allowoverwrite)
    if not conn:
        # open a connection if not already
        if type(yaml_filepath) is str:
            if len(yaml_filepath.split()) > 1:
                sql = yaml_filepath
                yaml_filepath = None
        conn = database_connect(database_key, yaml_filepath)
        close_connection = True
    cursor = conn.cursor()
    if query_group:
        query_group_sql = _assign_query_group(size=query_group)
        cursor.execute(query_group_sql)
        conn.commit()
    cursor.execute(unload_command)
    conn.commit()
    cursor.close()
    if close_connection:
        conn.close()
    print('Redshift data unloaded to S3')
    return None


# ------- HELPER FUNCTIONS --------

def _dict_depth(d):
    if isinstance(d, dict):
        return 1 + (max(map(_dict_depth, d.values())) if d else 0)
    return 0

def _strip_sql(sql):
    """returns sql string stripped of comments and empty lines"""

    sql = re.sub(r"/\*.*?\*/", '', sql, flags=re.DOTALL) # /* multiline comments */
    sql = re.sub(r"--.*\n", '', sql) # -- single line comments
    sql = re.sub(r"\n\n+", '\n', sql) # remove empty lines

    return sql
