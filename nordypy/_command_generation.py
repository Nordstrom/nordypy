import math
import datetime
import pandas as pd


def _assign_query_group(size='default'):
    """Create query group statement to assign with in your connection."""
    size = size.lower()
    qg_dict = {'small': 'QG_S', 'medium': 'QG_SM',
               'large': 'QG_SML', 'default': 'DEFAULT'}
    if size not in qg_dict.keys():
        raise ValueError('Please use one of the following query group sizes: ' + '\n' + 'small, medium, large, or default')
    print('Using {} query_group'.format(qg_dict[size]))
    return "set query_group to '{}';".format(qg_dict[size])

def _create_table_statement(data,
                            table_name):
    # determine type of columns in table and generate create table statement
    redshift_dtypes = {'float64': 'FLOAT4', 'object': 'VARCHAR',
                       'int64': 'INT', 'bool': 'BOOL', 'uint8': 'INT',
                       'datetime64[ns]': 'TIMESTAMP', 'date': 'DATE'}
    column_data = []
    # distinguish between dates and datetimes since pandas has dates as objects
    for col, dtype in zip(data.columns, data.dtypes):
        if dtype == str('object'):
            if isinstance(data[col].iloc[0], datetime.date):
                dtype = 'date'
        column_data.append((col, redshift_dtypes[str(dtype)]))
        a = "CREATE TABLE " + table_name + ' ('
        b = ''
        for col, dtype in column_data:
            if dtype == 'VARCHAR':
                max_length = data[col].str.len().max()
                max_length = _roundup(max_length * 2)
                if max_length == 0:
                    max_length = 10
                if max_length > 60000:
                    max_length = 'max'
                dtype = 'VARCHAR(' + str(max_length) + ')'
            b = b + col.replace('.', '_') + ' ' + str(dtype) + ','
    return a + b[:-1] + ');'


def _create_insert_statement(data, table_name):
    # create an insert statement using various data formats
    values = ''
    statement = 'INSERT INTO ' + table_name + ' VALUES '
    if type(data) == str:
        if data.endswith('.csv'):
            data = pd.read_csv(data)
    if type(data) == tuple:
        values = str(data)
        values = values.replace('nan', 'DEFAULT')
        values = values.replace('((', '(')
        values = values.replace('))', ')')
    elif type(data) == dict:
        for key, v in data.items():
            values += str(tuple(v.values()))
    elif type(data) == list:
        for v in data:
            values += str(tuple(v))
    elif type(data) == pd.core.frame.DataFrame:
        data = data.to_records(index=False)
        for i in range(len(data)):
            values += str(data[i])
    values = values.replace('nan', 'DEFAULT')
    values = values.replace(')(', '), (')
    return statement + values + ';'


def _generate_copy_command(copy_command=None,
                           cred_str=None,
                           bucket=None,
                           s3_filepath=None,
                           redshift_table=None,
                           delimiter=None,
                           copy_format=None):
    # fill in redshift schema.table, s3 path and credentials

    # build copy_command from scratch
    if not copy_command:
        copy_command = ["copy " + redshift_table,
                        " from 's3://" + bucket + "/" + s3_filepath + "'",
                        " credentials",
                        " '" + cred_str + "'"]
        if delimiter:
            del_str = " delimiter " + "'{}'".format(delimiter)
            copy_command.append(del_str)
        else:
            copy_command.append(' csv')
        if copy_format:
            copy_command.append(copy_format)
        if '.manifest' in s3_filepath:
            copy_command.append(" COMPUPDATE OFF STATUPDATE OFF")
        else:
            copy_command.append(" COMPUPDATE ON")
        return ''.join(copy_command)
    # just fill in some things on the copy command
    # if copy_command.endswith('.sql'):
    #     copy_command = read_sql_file(copy_command)
    if bucket:
        s3 = "s3://" + bucket + "/" + s3_filepath
        copy_command = copy_command.format(redshift_table, s3, cred_str,
                                           delimiter)
        if '.manifest' in s3_filepath:
            copy_command += " COMPUPDATE OFF STATUPDATE OFF"
        else:
            copy_command += " COMPUPDATE ON"
        return copy_command
    # fill in credentials only
    else:
        copy_command = copy_command.format(cred_str)
    return copy_command


def _generate_unload_command(cred_str,
                             select_sql,
                             bucket,
                             s3_filepath,
                             delimiter,
                             parallel,
                             gzip,
                             unload_command,
                             manifest,
                             allowoverwrite):
    # if prebuilt unload_command provided
    if unload_command:
        # if unload_command.endswith('.sql'):
        #     unload_command =  read_sql_file(unload_command)
        unload_command.format(cred_str)
        return unload_command

    # build unload command
    if 'select' not in select_sql.lower():
        select_sql = 'select * from ' + select_sql
    unload_command = ["unload ('" + select_sql + "') ",
                      "to 's3://" + bucket + "/" + s3_filepath + "'",
                      "credentials '" + cred_str + "'"
                      ]
    if delimiter:
        unload_command.append("delimiter as '" + delimiter + "'")
    if not parallel:
        unload_command.append("PARALLEL OFF")
    if gzip:
        unload_command.append("GZIP")
    if manifest:
        unload_command.append('manifest')
    if allowoverwrite:
        unload_command.append("allowoverwrite")
    unload_command.append(';')
    unload_command = " ".join(unload_command)
    return unload_command


# --- HELPER FUNCTIONS ---


def _roundup(x):
    if math.isnan(x):
        return 10
    return int(math.ceil(x / 100.0)) * 100
