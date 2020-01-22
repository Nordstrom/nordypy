import contextlib
import pandas as pd
import boto3
from ._s3 import s3_to_pandas
from ._s3 import s3_delete
from ._s3 import s3_list_objects
import time
import numpy as np
import re


'''
Make sure aws-okta is active
'''
                                           
def athena_to_pandas(sql, bucket, s3_filepath=None, 
                     profile_name='nordstrom-federated', 
                     region_name='us-west-2'):
    """
    Run a query on an athena table that returns data to a local pandas dataframe. 
    The bucket and filepath is the destination where the query result will reside 
    prior to being pulled as a pandas dataframe. If no s3_filepath is specified, 
    a temporary filepath will be written to then destoyed after the dataframe is pulled. 
    
    Parameters
    ----------
    sql : str [REQUIRED]
        your presto sql query
    bucket : str [REQUIRED]
        destination bucket for athena results
    s3_filepath : 
        s3 filepath of athena query results. If no specified s3 filepath a 'temp_*' will be created.
    profile_name : str
        default 'nordstrom-federated'
    region_name : str
        name of AWS region (default value 'us-west-2')
    Returns
    -------
    df: pandas dataframe

    Examples
    --------
    sql = 'SELECT * FROM TABLE LIMIT 10'
    df = nordypy.athena_to_pandas(sql=sql, bucket='yourbucket')
    """

    if not s3_filepath:
        s3_filepath = 'temp_' + str(np.abs(hash(str(np.random.randint(10000000)))))
        folder = s3_filepath
    session = boto3.session.Session(region_name=region_name, profile_name=profile_name)
    client = session.client(service_name='athena', region_name=region_name)
    
    execution = client.start_query_execution(QueryString=sql, 
                                 ResultConfiguration={'OutputLocation': 's3://' + bucket + '/' + s3_filepath})

    execution_id = execution['QueryExecutionId']
    state = 'RUNNING'
        
    while state in ['RUNNING']:
        response = client.get_query_execution(QueryExecutionId = execution_id)

        state = response['QueryExecution']['Status']['State']
        if state == 'FAILED':
            return False
        elif state == 'RUNNING':
            continue
        elif state == 'SUCCEEDED':
            time.sleep(1)
            s3_filepath = response['QueryExecution']['ResultConfiguration']['OutputLocation']
            filename = re.findall('.*\/(.*)', s3_filepath)[0]
            s3_filepath = s3_filepath.replace('s3://' + bucket + '/', '')
            if folder.startswith('temp'):
                df = s3_to_pandas(bucket=bucket, s3_filepath=s3_filepath)
                files = s3_list_objects(bucket=bucket, max_keys=100, prefix=folder, only_keys=True)
                s3_delete(bucket=bucket, s3_filepath=files)
                return df
            else:
                print(s3_filepath)
                return s3_to_pandas(bucket=bucket, s3_filepath=s3_filepath)
