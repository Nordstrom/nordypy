# -*- coding: utf-8 -*-
from ._command_generation import _generate_copy_command, _assign_query_group
import boto3
import botocore
from boto3.exceptions import S3UploadFailedError
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import NoCredentialsError, ProfileNotFound
import glob
from io import StringIO
from io import BytesIO
import os
import pandas as pd
import psycopg2
import pymysql
import subprocess


def s3_download_all(bucket=None, local_filepath='/.', environment=None,
                    profile_name=None):
    """Download all files from a bucket using the AWSCLI interface.
    Defaults to placing the files in the current directory."""
    if environment == 'local':
        bashCommand = "aws s3 sync --profile_name={} s3://{} {}".format(profile_name, bucket, local_filepath)
    else:
        bashCommand = "aws s3 sync s3://{} {}".format(bucket, local_filepath)
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()


def database_connect(database_key=None, yaml_filepath=None):
    """Return a database connection object. Connect with YAML config or bash
    environment variables.

    Parameters
    ----------
    database_key : str [REQUIRED]
        indicates which yaml login you plan to use of the bash_variable key if
        no YAML file is provided
    yaml_filepath : str [REQUIRED]
        path to yaml file to connect if no yaml_file is given, will assume
        that the datasource_key is for a bash_variable

    Returns
    -------
    conn : Redshift Connection Object

    Examples
    --------
    # if connection in bash_profile
    solr = nordypy.redshift_connect('PROD_REDSHIFT')

    # yaml file with only one profile
    solr = nordypy.redshift_connect('config.yaml')

    # yaml file with multiple profiles
    solr = nordypy.redshift_connect('prod_redshift', 'config.yaml')
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
                raise ValueError('YAML file contains multiple datasource profiles. Provide a datasource key.')
        if 'dbtype' not in cfg:
            print("UserWarning: Please update your config.yaml with 'dbtype': ['redshift', 'mysql', 'teradata'] -- ")
        if cfg['dbtype'] == 'mysql':
            conn = pymysql.connect(
                host=cfg['host'],
                db=cfg['dbname'],
                password=cfg['password'],
                port=cfg['port'],
                user=cfg['user']
            )
        else:
            # if redshift database
            conn = psycopg2.connect(
                host=cfg['host'],
                dbname=cfg['dbname'],
                password=cfg['password'],
                port=cfg['port'],
                user=cfg['user']
            )

    elif database_key:
        try:
            try:
                # redshift
                conn = psycopg2.connect(os.environ[database_key])
            except psycopg2.OperationalError:
                # mysql
                conn = pymysql.connect(os.environ[database_key])
        except (KeyError, pymysql.err.OperationalError):
            # for the case where positional arguments were used and the datasource was actually the YAML path
            try:
                conn = database_connect(yaml_filepath='config.yaml',
                                        database_key=database_key)
            except:
                yaml_filepath = database_key
                conn = database_connect(yaml_filepath=yaml_filepath,
                                        database_key=None)
    else:
        raise ValueError('Provide a YAML file path or a connection string via a bash_variable')
    return conn


def s3_to_redshift(copy_command=None, database_key=None, yaml_filepath=None,
                   bucket=None, s3_filepath=None, redshift_table=None,
                   query_group=None, delimiter=None, region_name='us-west-2',
                   environment=None, profile_name=None):
    """
    Copy data from s3 to redshift. Requires a blank table to be built.

    Parameters
    ----------
    copy_command (str or filename)
        - copy command template to be filled in prior to exexcuting
    database_key (str) [REQUIRED]
        - bash or yaml key
    yaml_filepath (filename) [REQUIRED]
        - location of yaml file
    bucket (str)
        - which bucket are you using
    s3_filepath (str)
        - s3 file to be copied to redshift
    redshift_table (str)
        - schema.table of prebuilt table in redshift to be filled in
    query_group (str)
        - which query_group ['default', 'small', 'medium', 'large']
    delimiter ('|', ',', '\t')
        - delimiter to use when copying
    region_name (str)
        - where in AWS
    environment ('aws' or 'local')
        - where is the script running
    profile_name (str)
        - default 'nordstrom-federated'

    Returns
    -------
    None

    Examples
    --------
    copy_command = 'copy {} from '{}' credentials '{}' delimiter '{}' escape EMPTYASNULL

    nordypy.s3_to_redshift(copy_command=copy_command, bucket='nordypy',
                           s3_filepath='nordypy/mydata_',
                           redshift_table='public.nordypy_test,
                           database_key=key,
                           environment='local', delimiter='|')

    """
    from nordypy._datasource import database_connect  # so no circular imports

    cred_str = _s3_get_temp_creds(region_name=region_name,
                                  environment=environment,
                                  profile_name=profile_name)
    copy_command = _generate_copy_command(copy_command, cred_str,
                                          bucket=bucket,
                                          s3_filepath=s3_filepath,
                                          redshift_table=redshift_table,
                                          delimiter=delimiter)
    conn = database_connect(database_key=database_key,
                            yaml_filepath=yaml_filepath)
    cursor = conn.cursor()
    if query_group:
        query_group_sql = _assign_query_group(size=query_group)
        cursor.execute(query_group_sql)
        conn.commit()
    cursor.execute(copy_command)
    conn.commit()
    cursor.close()
    conn.close()
    print('S3 Data copied to Redshift'.format(s3_filepath, redshift_table))
    return None


def s3_to_pandas(bucket, s3_filepath, encoding='utf8', index_col=0,
                 header='infer', delimiter=',', region_name='us-west-2',
                 environment=None, profile_name=None):
    """Read file directly from S3 into a pandas dataframe using a file buffer.

    Parameters
    ----------
    bucket : str [REQUIRED]
        s3 bucket where file is located
    s3_filepath : str [REQUIRED]
        filepath of file to read in
    encoding : str
        encoding of file (default is utf8)
    index_col : int, False, or None
        column to use for row labels (default is 0)
    header : None or int
        if int, which row is the header
    delimiter : str
        how is the file delimited
    region_name : str
        name of AWS region (default value 'us-west-2')
    environment : str
        'aws' or 'local' depending on whether the script is running locally or in AWS
    profile_name : str
        profile name for credential purposes when running locally,
        typically 'nordstrom-federated'

    Returns
    -------
    df : pandas dataframe

    Example uses
    -----------
    df = nordypy.s3_to_pandas(bucket=bucket, s3_filepath=s3_filepath)
    """

    response = s3_get(bucket=bucket, s3_filepath=s3_filepath,
                      region_name=region_name, environment=environment,
                      profile_name=profile_name)
    return pd.read_csv(BytesIO(response['Body'].read()), encoding=encoding,
                       index_col=index_col, header=header,
                       sep=delimiter)


def s3_create_bucket():
    pass


def s3_delete_bucket():
    pass


def s3_list_buckets(region_name='us-west-2', environment=None, profile_name=None):
    """List S3 buckets available from current AWS account.

    Parameters
    ----------
    region_name : str
        name of AWS region (default value 'us-west-2')
    environment : str
        'aws' or 'local' depending on whether the script is running locally or in AWS
    profile_name : str
        profile name for credential purposes when running locally

    Returns
    -------
    buckets : list
        list of bucket names

    Example use
    -----------
    buckets = nordypy.s3_list_buckets()
    """
    session = _s3_create_session(region_name=region_name,
                                 environment=environment,
                                 profile_name=profile_name)
    s3 = session.resource('s3')
    buckets = []
    try:
        for bucket in s3.buckets.all():
            buckets.append(bucket.name)
        return buckets
    except botocore.exceptions.ClientError as e:
        raise NameError('If running locally, you must run aws-okta in the background. ')


def s3_list_objects(bucket=None, max_keys=10, prefix='', only_keys=False,
                    region_name='us-west-2', environment=None,
                    profile_name=None, **kwargs):
    """List data in S3 bucket. Uses boto3 list_objects_v2 API.

     Parameters
    ----------
    bucket : str
        S3 bucket to search
    max_keys : int
        number of objects to return, maximum of 1000
    prefix : str
        filter objects with a prefix
    only_keys : bool
        if True will process the json returned into a list of s3 keys
    region_name : str
        name of AWS region (default value 'us-west-2')
    environment : str
        'aws' or 'local' depending on whether the script is running locally or in AWS
    profile_name : str
        profile name for credential purposes when running locally
    Returns
    -------
    data : json or list
        returns the objects in the specified s3 bucket, if only_keys is True, then a list of key names is returned

    Example use
    -----------
    keys = nordypy.s3_list_objects(bucket='nordypy', max_keys=100)
    """
    session = _s3_create_session(region_name=region_name,
                                 environment=environment,
                                 profile_name=profile_name)
    client = session.client('s3')
    try:
        data = client.list_objects_v2(Bucket=bucket,
                                      Prefix=prefix,
                                      MaxKeys=max_keys,
                                      **kwargs)
        if only_keys:
            data = [k['Key'] for k in data['Contents']]
        return data
    except botocore.exceptions.ClientError as e:
        raise NameError('If running locally, you must run aws-okta in the background. ')


def _s3_create_session(region_name='us-west-2',
                       environment=None,
                       profile_name='nordstrom-federated'):
    """
    Creates boto3 session

    Parameters
    ----------
    region_name : str
        name of AWS region (default value 'us-west-2')
    environment : str
        'aws' or 'local' depending on whether the script is running locally or in AWS
    profile_name : str
        profile name for credential purposes when running locally

    Returns
    -------
    boto3 session object

    Example use
    -----------
    N/A: this function is not intended to be called directly by user
    """
    if not profile_name:
        profile_name = 'nordstrom-federated'
    if not environment:
        try:
            session = boto3.session.Session(region_name=region_name,
                                            profile_name=profile_name)
        except (NoCredentialsError, ProfileNotFound):
            session = boto3.session.Session(region_name=region_name)
        return session
    if environment == 'aws':
        session = boto3.session.Session(region_name=region_name)
    else:
        session = boto3.session.Session(region_name=region_name,
                                        profile_name=profile_name)
    return session


def _s3_get_temp_creds(region_name='us-west-2',
                       environment=None,
                       profile_name=None):
    """
    Gets temporary credentials for COPY and LOAD Redshift commands

    If running locally you should have the aws-okta running

    Parameters
    ----------
    region_name : str
        name of AWS region (default value 'us-west-2')
    environment : str
        'aws' or 'local' depending on whether the script is running locally or in AWS
    profile_name : str
        profile name for credential purposes when running locally,
        typically 'nordstrom-federated'

    Returns
    -------
    str
        string containing temporary credentials

    Example use
    -----------
    temp_creds = _get_temp_creds(region_name='us-west-2',
                                 environment='local',
                                 profile='nordstrom-federated')
    """
    session = _s3_create_session(region_name, environment, profile_name)
    ak = session.get_credentials().access_key
    sk = session.get_credentials().secret_key
    tkn = session.get_credentials().token
    cred_str = 'aws_access_key_id={0};aws_secret_access_key={1};token={2}'.format(ak, sk, tkn)
    return cred_str


def s3_get_bucket(bucket,
                  region_name='us-west-2',
                  environment=None,
                  profile_name=None):
    """ Retrieves S3 bucket

    If running locally you should have aws-okta running

    Parameters
    ----------
    bucket : str [REQUIRED]
        S3 bucket name
    region_name : str
        name of AWS region (default value 'us-west-2')
    environment : str
        'aws' or 'local' depending on whether the script is running locally or in AWS
    profile_name : str
        profile name for credential purposes when running locally,
        typically 'nordstrom-federated'

    Returns
    -------
    bucket object

    Example use
    -----------
    mybucket = s3_get_bucket(bucket='my_bucket',
                             region_name='us-west-2',
                             environment='local',
                             profile='nordstrom-federated')
    """
    session = _s3_create_session(region_name, environment, profile_name)
    s3 = session.resource('s3')
    mybucket = s3.Bucket(bucket)
    try:
        s3.meta.client.head_bucket(Bucket=bucket)
    except botocore.exceptions.ClientError as e:
        # Check if bucket exists, if not raise error
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            raise NameError('404 bucket does not exist')
        if error_code == 400:
            raise NameError('If running locally, you must run aws-okta in the background.')
    return mybucket


def pandas_to_s3(data=None, bucket=None, s3_filepath=None, delimiter=None, orient=None,
                 index=False, header=False, region_name='us-west-2',
                 environment=None, profile_name=None):
    """
    Upload a dataframe to an S3 bucket. Can write to both csv or json formats, based on the filename given.
    Default format is csv if file extension is not explicit and `delimiter` or `orient` is not specified.

    If running locally you should have the aws-okta running

    Parameters
    ----------
    data : pandas.DataFrame [REQUIRED]
        dataframe to be uploaded
    bucket : str [REQUIRED]
        S3 bucket name
    s3_filepath : str [REQUIRED]
        path and filename within the bucket for the file to be uploaded
    delimiter : ('|', ',', '\t')
        how should the dataframe be delimited
    orient : ('split','records','index','columns','values')
        expected JSON string format, see python docs for examples
        index=False only supported for 'split and 'table' formats
    index : True or False
        whether to include the index values
    header : True or False
        whether to include the header values
    region_name : str
        name of AWS region (default value 'us-west-2')
    environment : str
        'aws' or 'local' depending on whether running locally or in AWS
    profile_name : str
        profile name for credential purposes when running locally,
        typically 'nordstrom-federated'

    Returns
    -------
    None

    Example use
    -----------
    pandas_to_s3(data=df, bucket='nordypy', s3_filepath='mydata.csv', delimiter=',')
    pandas_to_s3(data=df, bucket='nordypy', s3_filepath='mydata.json', orient='records')
    """
    mybucket = s3_get_bucket(bucket, region_name, environment, profile_name)
    try:
        buffer = StringIO()
        if delimiter:
            data.to_csv(buffer, sep=delimiter, encoding='utf-8', index=index, header=header)
        elif s3_filepath.endswith('json'):
            if not orient:
                orient = 'index'
            if orient != 'split' or orient != 'table':
                index = True
            data.to_json(buffer, orient=orient, index=index)
        else:
            data.to_csv(buffer, encoding='utf-8', index=index, header=header)
    except:
        buffer = BytesIO()
        if delimiter:
            data.to_csv(buffer, sep=delimiter, encoding='utf-8', index=index, header=header)
        elif s3_filepath.endswith('json'):
            if not orient:
                orient = 'index'
            if orient != 'split' or orient != 'table':
                index = True
            data.to_json(buffer, orient=orient, index=index)
        else:
            data.to_csv(buffer, encoding='utf-8', index=index, header=header)
    try:
        mybucket.put_object(Key=s3_filepath, Body=buffer.getvalue())
        print('{} upload complete'.format(s3_filepath))
        return 'success'
    except:
        print(s3_filepath + " failed to upload to s3")
        return 'failed'


def s3_rename_file(bucket,
                   old_filepath,
                   new_filepath,
                   region_name='us-west-2',
                   environment=None,
                   profile_name=None):
    """
    Renames (or moves) a file within an S3 bucket.

    If running locally you should have the aws-okta running.

    Parameters
    ----------
    bucket : str [REQUIRED]
        S3 bucket name
    old_filepath : str [REQUIRED]
        s3 path and old file name
    new_filepath : str [REQUIRED]
        s3 path and new file name
    region_name : str
        name of AWS region (default value 'us-west-2')
    environment : str
        'aws' or 'local' depending on whether running locally or in AWS
    profile_name : str
        profile name for credential purposes when running locally,
        typically 'nordstrom-federated'

    Returns
    -------
    None

    Example use
    -----------
    s3_rename_file(bucket='nordypy',
                   old_filepath='tmp/old_file.csv',
                   new_filepath='tmp/new_file.csv')
    """
    session = _s3_create_session(region_name, environment, profile_name)
    s3 = session.resource('s3')
    try:
        s3.Object(bucket, new_filepath).copy_from(CopySource=bucket + '/' + old_filepath)
        s3.Object(bucket, old_filepath).delete()
    except botocore.exceptions.ClientError as e:
        if '(ExpiredToken)' in str(e):
            raise NameError('If running locally, you must run aws-okta in the background. ' + str(e))
        else:
            raise e
    print('{} renamed to {}'.format(old_filepath, new_filepath))


def s3_get(bucket, s3_filepath, region_name='us-west-2', environment=None,
           profile_name=None):
    session = _s3_create_session(region_name=region_name, environment=environment, profile_name=profile_name)
    client = session.client('s3')
    object = client.get_object(Bucket=bucket, Key=s3_filepath)
    return object


def s3_delete(bucket, s3_filepath, region_name='us-west-2', environment=None,
              profile_name=None):
    """Delete an object(s) from an S3 bucket.

    If running locally you should have aws-okta running at the same time.

    Parameters
    ----------
    bucket : str [REQUIRED]
        S3 bucket name
    s3_filepath : str or list [REQUIRED]
        path and filename within the bucket to delete
    region_name : str
        name of AWS region (default value 'us-west-2')
    environment : str
        'aws' or 'local' depending on whether running locally or in AWS
    profile_name : str
        profile name for credential purposes when running locally,
        typically 'nordstrom-federated'

    Returns
    -------
    List of deleted keys

    Example use
    -----------
    to_delete = ['file1.txt', 'nordypy.png', 'model.pkl']

    resp = nordypy.s3_delete(bucket='mybucket', s3_filepath=to_delete)
    """

    if type(s3_filepath) is str:
        s3_filepath = [s3_filepath]
    del_dict = {}
    objects = []
    for key in s3_filepath:
        objects.append({'Key': key})
    del_dict['Objects'] = objects

    mybucket = s3_get_bucket(bucket, region_name, environment, profile_name)

    response = mybucket.delete_objects(Delete=del_dict)
    return response['Deleted']


def s3_download(bucket,
                s3_filepath,
                local_filepath,
                region_name='us-west-2',
                environment=None,
                profile_name=None,
                multipart_threshold=8388608,
                multipart_chunksize=8388608):
    """
    Downloads file(s) from an S3 bucket

    If running locally you should have aws-okta running at the same time.

    Parameters
    ----------
    bucket : str [REQUIRED]
        S3 bucket name
    s3_filepath : str or list [REQUIRED]
        path and filename within bucket to file(s) you would like to download
    local_filepath : str or list [REQUIRED]
        path and filename for file(s) to be saved locally
    region_name : str
        name of AWS region (default value 'us-west-2')
    environment : str
        'aws' or 'local' depending on whether running locally or in AWS
    profile_name : str
        profile name for credential purposes when running locally,
        typically 'nordstrom-federated'
    multipart_threshold : int
        minimum filesize to initiate multipart download
    multipart_chunksize : int
        chunksize for multipart download

    Returns
    -------
    None

    Example use
    -----------
    # to download a single file
    s3_download(bucket='mybucket',
                s3_filepath='tmp/myfile.csv',
                filepath='..data/myfile.csv',
                environment='local')

    # to download all files in a directory (will not upload contents of subdirectories)
    s3_download(bucket='mybucket',
                s3_filepath='tmp/*',
                filepath='..data/',
                environment='local')

    # to download all files in a directory matching a wildcard (will not download contents of subdirectories)
    s3_download(bucket='mybucket',
                s3_filepath='tmp/*.csv',
                filepath='..data/',
                environment='local')
    """
    if type(s3_filepath) == list:
        if len(s3_filepath) != len(local_filepath):
            raise ValueError('Length of s3_filepath arguments must equal length of local_filepath arguments')
    else:
        # if s3 and local paths are a single string
        s3_filepath = [s3_filepath]
        local_filepath = [local_filepath]
    mybucket = s3_get_bucket(bucket, region_name, environment, profile_name)
    # multipart_threshold and multipart_chunksize defaults = Amazon defaults
    config = TransferConfig(multipart_threshold=multipart_threshold,
                            multipart_chunksize=multipart_chunksize)
    if '*' in s3_filepath:
        # use left and right for pattern matching
        left = s3_filepath.split('*')[0]
        right = s3_filepath.split('*')[-1]
        # construct s3_filepath without wildcard
        s3_filepath = '/'.join(s3_filepath.split('/')[:-1]) + '/'
        # get keys, filter out directories, match wildcard, get filenames
        keys = [item.key for item in mybucket.objects.filter(Prefix=s3_filepath)
                if item.key[-1] != '/' and left in item.key and right in item.key]
        filenames = [key.split('/')[-1] for key in keys]
    else:
        keys = s3_filepath
        filenames = local_filepath

    for key, local in zip(keys, filenames):
        try:
            mybucket.download_file(key,
                                   local,
                                   Config=config)
        except botocore.exceptions.ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 400:
                raise NameError('If running locally, you must run aws-okta in the background. ' + str(e))
            else:
                raise e
        print('{} download complete'.format(key))


def s3_upload(bucket,
              s3_filepath,
              local_filepath,
              permission=None,
              region_name='us-west-2',
              environment=None,
              profile_name=None,
              multipart_threshold=8388608,
              multipart_chunksize=8388608):
    """
    Uploads a file to an S3 bucket, allows you to set permssions on upload.

    If running locally you should have the aws-okta running.

    Parameters
    ----------
    bucket : str
        S3 bucket name
    s3_filepath : str or list
        path and filename within the bucket for the file to be uploaded
    local_filepath : str or list
        path and filename for file to be uploaded
    permission : str
        'private'|'public-read'|'public-read-write'|'authenticated-read'
        'aws-exec-read'|'bucket-owner-read'|'bucket-owner-full-control'
    region_name : str
        name of AWS region (default value 'us-west-2')
    environment : str
        'aws' or 'local' depending on whether running locally or in AWS
    profile_name : str
        profile name for credential purposes when running locally,
        typically 'nordstrom-federated'
    multipart_threshold : int
        minimum filesize to initiate multipart upload
    multipart_chunksize : int
        chunksize for multipart upload

    Returns
    -------
    None

    Example use
    -----------
    # to upload a single file
    s3_upload(bucket='mybucket',
              s3_filepath='tmp/myfile.csv',
              filepath='..data/myfile.csv',
              environment='local')

    # to upload all files in a directory (will not upload contents of subdirectories)
    s3_upload(bucket='mybucket',
              s3_filepath='tmp/',
              filepath='..data/*',
              environment='local')

    # to upload all files in a directory matching a wildcard (will not upload contents of subdirectories)
    s3_upload(bucket='mybucket',
              s3_filepath='tmp/',
              filepath='../data/*.csv')
    """
    # TODO check that permission is a proper type
    if type(s3_filepath) == list:
        if len(s3_filepath) != len(local_filepath):
            raise ValueError('Length of s3_filepath arguments must equal length of local_filepath arguments')

    mybucket = s3_get_bucket(bucket, region_name, environment, profile_name)
    # multipart_threshold and multipart_chunksize defaults = Amazon defaults
    config = TransferConfig(multipart_threshold=multipart_threshold,
                            multipart_chunksize=multipart_chunksize)
    if '*' in local_filepath:
        items = glob.glob(local_filepath)
        # filter out directories
        filepaths = [item for item in items if os.path.isfile(item)]
        filenames = [f.split('/')[-1] for f in filepaths]
    else:
        filepaths = [local_filepath]
        filenames = ['']
    for i, filepath in enumerate(filepaths):
        try:
            mybucket.upload_file(filepath,
                                 s3_filepath + filenames[i],
                                 Config=config)
            if permission:
                obj = mybucket.Object(s3_filepath + filenames[i])
                obj.Acl().put(ACL=permission)
        except boto3.exceptions.S3UploadFailedError as e:
            if '(ExpiredToken)' in str(e):
                raise S3UploadFailedError('If running locally, you must run aws-okta in the background. ' + str(e))
            else:
                raise e
        print('{} upload complete'.format(filepath))


def s3_change_permissions(bucket, s3_filepath, permission=None,
                          region_name='us-west-2', environment=None,
                          profile_name=None):
    """
    Change the permissions of an object in S3.

    Parameters
    ----------
    bucket : str
        S3 bucket name
    s3_filepath : str or list
        path and filename within the bucket for the file to be uploaded
    permission : str
        'private'|'public-read'|'public-read-write'|'authenticated-read'
        'aws-exec-read'|'bucket-owner-read'|'bucket-owner-full-control'

    Returns
    -------
    None
    """
    perms = ['private', 'public-read', 'public-read-write', 'authenticated-read', 'aws-exec-read', 'bucket-owner-read',
             'bucket-owner-full-control']
    if permission not in perms:
        raise ValueError('permission can be: {}'.format(perms))
    object = s3_get_bucket(bucket, environment=environment).Object(s3_filepath)
    object.Acl().put(ACL=permission)

def s3_get_permissions(bucket, s3_filepath, region_name='us-west-2',
                       environment=None, profile_name=None):
    """
    Get the permissions on a specified object in an S3 bucket.

    Parameters
    ----------
    bucket : str
        S3 bucket name
    s3_filepath : str or list
        path and filename within the bucket for the file to be uploaded
    region_name : str
        name of AWS region (default value 'us-west-2')
    environment : str
        'aws' or 'local' depending on whether running locally or in AWS
    profile_name : str
        profile name for credential purposes when running locally,
        typically 'nordstrom-federated'

    Returns
    -------
    tuple
        (current_acl, grants) inferred acl of the specified object and list of grant information

    Example Use:
    -----------
    current_acl, grants = nordypy.s3_get_permissions(bucket='nordypy', s3_filepath='example.csv')
    """
    object = s3_get_bucket(bucket, environment=environment).Object(s3_filepath)
    acl = object.Acl()
    grants = acl.grants
    if len(grants) == 1:
        possible_current_acl = ['private', 'bucket-owner-read', 'bucket-owner-full-control']
        return possible_current_acl, grants
    for g in grants:
        if g['Permission'] == 'WRITE':
            possible_current_acl = ['public-read-write']
            return possible_current_acl, grants
        try:
            if g['Grantee']['URI'].endswith('AuthenticatedUsers'):
                possible_current_acl = ['authenticated-read']
                return possible_current_acl, grants
        except KeyError:
            pass
    for g in grants:
        try:
            if g['Grantee']['URI'].endswith('AllUsers'):
                possible_current_acl = ['public-read']
                return possible_current_acl, grants
        except KeyError:
            pass
    possible_current_acl = ['aws-exec-read']
    return possible_current_acl, grants

def s3_get_matching_objects(bucket, prefix="", suffix="", 
                            region_name='us-west-2', environment=None, profile_name='nordstrom-federated'):
    """
    Generate objects in an S3 bucket.

    Parameters
    ----------
    bucket : str [REQUIRED]
        S3 bucket name
    prefix : str or list
        Only fetch objects whose key starts with this prefix (optional)
    suffix : str
        Only fetch objects whose keys end withthis suffix (optional)
    region_name : str
        name of AWS region (default value 'us-west-2')
    environment : str
        'aws' or 'local' depending on whether running locally or in AWS
    profile_name : str
        profile name for credential purposes when running locally,
        typically 'nordstrom-federated'

    Example Use:
    ------------
    for obj in s3_get_matching_objects(bucket='nordypy', prefix='temp'):
        print(obj['Size'])
    """
    s3 = _s3_create_session(region_name=region_name, environment=environment, profile_name=profile_name).client('s3')
    paginator = s3.get_paginator("list_objects_v2")

    kwargs = {'Bucket': bucket}

    # We can pass the prefix directly to the S3 API.  If the user has passed
    # a tuple or list of prefixes, we go through them one by one.

    if isinstance(prefix, str):
        prefixes = (prefix, )
    else:
        prefixes = prefix

    for key_prefix in prefixes:
        kwargs["Prefix"] = key_prefix

        for page in paginator.paginate(**kwargs):
            try:
                contents = page["Contents"]
            except KeyError:
                return

            for obj in contents:
                key = obj["Key"]
                if key.endswith(suffix):
                    yield obj


def s3_get_matching_keys(bucket, prefix="", suffix="",
                         region_name='us-west-2', environment=None, profile_name='nordstrom-federated'):
    """
    Generate keys in an S3 bucket matching certain criteria.

        Parameters
    ----------
    bucket : str [REQUIRED]
        S3 bucket name
    prefix : str or list
        Only fetch objects whose key starts with this prefix (optional)
    suffix : str
        Only fetch objects whose keys end withthis suffix (optional)
    region_name : str
        name of AWS region (default value 'us-west-2')
    environment : str
        'aws' or 'local' depending on whether running locally or in AWS
    profile_name : str
        profile name for credential purposes when running locally,
        typically 'nordstrom-federated'
        
    Example Use:
    ------------
    all_keys_in_bucket = [k for k in s3_get_matching_keys(bucket='nordypy)]
    """
    for obj in s3_get_matching_objects(bucket, prefix, suffix):
        yield obj["Key"]

