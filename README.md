# Nordypy

The Nordypy package is a set of tools to make python-based analysis and data science at Nordstrom more streamlined and consistent.
This package is being developed in conjunction with the R-based packages ElmeR and nordyR.

## What can Nordypy do for you
- Manipulate data on your local system, Redshift, MySQL, and in S3
- Create a fresh repo structure with folders, readme, config.yaml, .gitignore, and more...
- Render jupyter notebooks and markdown for the Nordstrom knowledge-repo.

### Installing Nordypy

```bash
pip install nordypy
```

### Setting up your Database Connections

Nordypy uses **yaml** files to configure your database connection. You can create your template yaml file by running the following from an ipython session.

```python
In [1]: import nordypy

In [2]: nordypy.create_config_file(path='./')

In [3]: exit
```

A template `config.yaml` file will be created where you specify. Make sure to update the config.yaml with your required credentials.

```yaml
my_redshift:
  host: <DB ADDRESS>
  port: <DB PORT>
  dbname: <DB NAME>
  user: <USER NAME>
  password: <PASSWORD>
  dbtype: <DB TYPE>
my_mysql:
  host: <DB ADDRESS>
  port: <DB PORT>
  dbname: <DB NAME>
  user: <USER NAME>
  password: <PASSWORD>
  dbtype: <DB TYPE>
```

Don't want to keep your user name and password in plain text on some random config file?  Use AWS secret manager! Directions:

1. Sign into your AWS account and go to Secrets Manager.  
2. Store your secret.  For the purposes of Nordypy, set it up in the 'API' format, and enter the keys and values like you would in the yaml example above.
3. Give your key a name that you can easily remember.
4. On your local machine, configure your yaml file to look like:

```yaml
my_redshift:
  secret_name: your/super/my_redshift_secret
  region_name: us-west-2
my_mysql:
  secret_name: your/super/my_mysql_secret
  region_name: us-west-2
```
Also keep in mind, if you have a secret_name in your yaml, nordypy will use those credentials, and ignore any host, port, dbname, user, password or dbtype that you have in your local yaml file.  If secrets is used, AWS creds must be running in the background, or nordypy must be run on EC2 instance.

### Nordypy Functions

#### General Project Tools
- [initialize_project](#initialize-project)
- [create_config_file](#create-config-file)

#### Database Functions
- [database_analyze_table](#database-analyze-table)
- [database_connect](#database-connect)
- [database_create_table](#database-create-table)
- [database_drop_table](#database-drop-table)
- [database_execute](#database-execute)
- [database_get_data](#database-get-data)
- [database_get_column_names](#database-get-column-names)
- [database_insert](#database-insert)
- [data_to_redshift](#data-to-redshift)
- [read_sql_file](#read-sql-file)

#### S3 Functions
- [pandas_to_s3](#pandas-to-s3)
- [redshift_to_s3](#redshift-to-s3)
- [s3_change_permissions](#s3-change-permissions)
- [s3_delete](#s3-delete)
- [s3_download](#s3-download)
- [s3_get_bucket](#s3-get-bucket)
- [s3_get_permissions](#s3-get-permissions)
- [s3_list_buckets](#s3-list-buckets)
- [s3_list_objects](#s3-list-objects)
- [s3_rename_file](#s3-rename-file)
- [s3_to_pandas](#s3-to-pandas)
- [s3_upload](#s3-upload)

#### Knowledge Repo Functions
- [render_post](#render-post)

#### Upcoming Functions
- Dynamo Functions
- Report Templating
- One pagers Export
- Plotting Style Presets


## Starting an Analytics or Data Science Project
Executing analytics requests within a structured environment can reduce time spent on mundane setup tasks, promotes good practices, facilitates collaboration, and is critical to reproducible research. You can use the `nordypy.initialize_project()` function to add boilerplate files and folders to any project folder (defaults to the current working directory).

<a name="initialize-project">

### `nordypy.initialize_project()`

</a>

```python
import nordypy

# generate standard folders and files
nordypy.initialize_project('default')
```

```bash
root/
  | - README.md
  | - config.yaml
  | - code/
        | - python
        | - R
        | - SQL
  | - data
  | - docs
  | - logs
  | - output
  | - sandbox
```

---

<a name="create-config-file">

### `nordypy.create_config_file()`

</a>

Creates a template `config.yaml` file that contains your database connections.  The command will prompt the user for connection details and automagically create the config.yaml file.

```python
nordypy.create_config_file(path='~/connections/', ask_me=False)
```
path specifies the path you would like the config file.  If ask_me = False will copy a default template that you will need to modify.  If ask_me = True, then you will be asked a few questions about your credentials, and the config file will be automagically generated.  


## Datasource Tooling


Nordypy lets you easily move manipulate data locally, in S3, and in Redshift.

---

<a name="database-analyze-table">

### `nordypy.database_analyze_table()`

</a>

Analyzes the compression and skew on the specified table in redshift.

```python
nordypy.database_analyze_table(database_key='my_redshift',
                               yaml_filepath='config.yaml',
                               table='analytics_user_vws.my_table')
```

---

<a name="database-connect">

### `nordypy.database_connect()`

</a>

Returns a DBconnection to the database of your choosing.

```python
conn = nordypy.database_connect(database_key='my_redshift',
                                yaml_filepath='config.yaml')

cur = conn.cursor()
cur.execute(sql)
cur.commit()
conn.close()
```
<a name="database-create-table">

---

### `nordypy.database_create_table()`

</a>

The Nordypy `database_create_table` method can create a table using two different methods.

1. Nordypy can read the data types of pandas dataframe and generate a CREATE statement automatically.
2. Provide a pre-written CREATE statement.


```python
# with a dataframe
df = pd.read_csv('my_data.csv')

nordypy.database_create_table(data=df,
                              table_name='public.my_table',
                              make_public=True
                              database_key='my_redshift',
                              yaml_filepath='config.yaml')

# using a prewritten statement
create = "CREATE TABLE public.my_table (age FLOAT4,name VARCHAR(200));"

nordypy.database_create_table(create_statement=create,
                              database_key='my_redshift',
                              yaml_filepath='config.yaml')
```

---
<a name="database-drop-table">

### `nordypy.databases_drop_table()`

</a>

Drops table if exists.

```python
nordypy.database_drop_table(table_name='public.my_table',
                            database_key='my_redshift',
                            yaml_filepath='config.yaml')
```
---

<a name="database-execute">

### `nordypy.database_execute()`

</a>

This function will execute multiple queries as long as they are each separated by a `';'`. If the final query should return data, that can be specified with `return_data=True`. Additionally, if the data should be returned as a pandas databframe that can be specified with the `as_pandas=True` argument. You can choose to select your `query_group` with an optional parameter to be either `['default', 'small', 'medium', 'large']`

```python
sql = nordypy.read_sql_file('my_queries.sql')
nordypy.database_execute(database_key='my_redshift',
                         yaml_filepath='config.yaml',
                         sql=sql,
                         query_group='medium')
```

---
<a name="database-get-data">

### `nordypy.database_get_data()`

</a>

Run a single query and return data as records or as a pandas dataframe. The query_group parameter can optionally be provided to choose where your query is run.

```python
sql = 'select top 10 * from public.my_table;'
data = nordypy.database_get_data(database_key='my_redshift',
                                 yaml_filepath='config.yaml',
                                 sql=sql,
                                 as_pandas=True,
                                 query_group='default')
```

---
<a name="database-get-column-names">

### `nordypy.database_get_column_names()`

</a>

Return the column names and data types (optional) from a Redshift table.

```python
data = nordypy.database_get_column_names(database_key='my_redshift',
                                         yaml_filepath='config.yaml',
                                         table='public.my_table'
                                         data_type=True)
```

---
<a name="database-insert">

### `nordypy.database_insert()`

</a>

Insert data into an already existing table. Can insert a full csv, a full
pandas dataframe, a single tuple of data, or run an insert statement on
tables already in the database.

```python
data = {'A':1, 'B':2, 'C':3, 'D':4}
nordypy.database_insert(data=data,
                        database_key='my_redshift',
                        yaml_filepath='config.yaml',
                        table_name='public.my_table')
```

---

<a name="data-to-redshift">

### `nordypy.data_to_redshift()`

</a>

Uploads a csv or pandas dataframe to redshift via S3.

```python
df = pd.read_csv('my_data.csv')
nordypy.data_to_redshift(data=df,
                         table_name='public.my_table',
                         bucket='mybucket',
                         s3_filepath='my_data',
                         database_key='my_redshift',
                         yaml_filepath='config.yaml',
                         delimiter=',',
                         drop_table=True)
```

---
<a name="read-sql-file">

### `nordypy.read_sql_file()`

</a>

Reads in a SQL file as a string.
```python
sql = nordypy.read_sql_file('queries.sql')
```

---

## S3 Functions

**Update:** S3 functions no longer require you to specify the `environment` or `profile_name`. These will automatically be configured for you. If you wish to specify your environment or profile name, you are still able to do so by setting `environment` to `'local` and specifying your `profile_name` to what ever you need.

If running locally, you must also be running `awscreds` on your system in the account where your S3 buckets are located.  

---

<a name="pandas-to-s3">

### `nordypy.pandas_to_s3()`

</a>

Upload a pandas dataframe to S3 as a csv or json.

```python
# with awscreds running
df = pd.read_csv('data.csv')

# as a csv
nordypy.pandas_to_s3(data=df,
                     bucket='mybucket',
                     s3_filepath='pandas_data.csv',
                     delimiter=',')

# as json
df = pd.read_csv('data.csv')
nordypy.pandas_to_s3(data=df,
                    bucket='mybucket',
                    s3_filepath='pandas_data.json',
                    orient='records')
```
---

<a name="redshift-to-s3">

### `nordypy.redshift_to_s3()`

</a>

Unload redshift data to S3 using a select statement.

```python
# with awscreds running
nordypy.redshift_to_s3(select_sql='select * from public.mytable',
                       database_key='my_redshift',
                       bucket='mybucket',
                       s3_filepath='redshift_s3_table')
```
---

<a name="s3-change-permissions">

### `nordypy.s3_change_permissions()`

</a>

Change the access permissions to an object in S3.

```python
# with awscreds running
nordypy.s3_change_permissions(bucket='mybucket',
                              s3_filepath='myfile.txt',
                              permission='public-read')
```
---

<a name="s3-delete">

### `nordypy.s3_delete()`

</a>
Delete one or many objects from s3.

```python
# with awscreds running

# delete a single object from s3
nordypy.s3_delete(bucket='mybucket', s3_filepath='my_data.txt')

# delete multiple objects from s3 with a list
nordypy.s3_delete(bucket='mybucket',
                    s3_filepath=['my_data.txt', 'my_data2.txt', 'my_data3.txt'])
```
---

<a name="s3-download">

### `nordypy.s3_download()`

</a>
Download one or many files locally from S3.

```python
# with awscreds running
nordypy.s3_download(bucket='mybucket',
                    s3_filepath='my_data.txt',
                    local_filepath='data/my_local_data.txt')

# download multiple files quickly
nordypy.s3_download(bucket='mybucket',
                    s3_filepath=['my_data.txt', 'my_data2.txt', 'my_data3.txt'],
                    local_filepath=['data/local1.txt', 'data/local2.txt', 'data/local3.txt'])
```

---
<a name="s3-get-bucket">

### `nordypy.s3_get_bucket()`

</a>
Gain access to an S3 bucket object.

```python
# with awscreds running
bucket = nordypy.s3_get_bucket(bucket='mybucket')
```
---

<a name="s3-get-permissions">

### `nordypy.s3_get_permissions()`

</a>

Get the access permissions to an object in S3.

```python
# with awscreds running
nordypy.s3_get_permissions(bucket='mybucket',
                           s3_filepath='myfile.txt')
```
---

<a name="#s3-list-buckets">

### `nordypy.s3_list_buckets()`

</a>

Return a list of S3 buckets in an account.

```python
# while running awscreds
resp = nordypy.s3_list_buckets()
```

---


<a name="s3-list-objects">

### `nordypy.s3_list_objects()`

</a>

List the keys in an S3 bucket. Returns the response from the boto3.list_objects_v2 method.

```python
# while running awscreds
resp = nordypy.s3_list_objects(bucket='mybucket',
                               max_keys=100,
                               prefix='data/')

# returns only the keys, no metadata
keys = nordypy.s3_list_objects(bucket='mybucket',
                               max_keys=100,
                               prefix='data/',
                               only_keys=True)
```

---

<a name="s3-rename-file">

### `nordypy.s3_rename_file()`

</a>

Rename a file in an S3 bucket.

```python
# while running awscreds
nordypy.s3_rename_file(bucket='mybucket',
                       old_filepath='old_file.txt',
                       new_filepath='new_file.txt')
```

---


<a name="s3-to-pandas">

### `nordypy.s3_to_pandas()`

</a>

Read file directly from S3 into a pandas dataframe using a file buffer.

```python
# while running awscreds
df = nordypy.s3_to_pandas(bucket='mybucket',
                          s3_filepath='my_data.csv')
```

---

<a name="s3-upload">

### `nordypy.s3_upload()`

</a>
Upload a file to S3.

```python
# while running awscreds
nordypy.s3_upload(bucket='mybucket',
                  s3_filepath='cloud.txt',
                  local_filepath='data/local.txt',
                  permission='public-read')
```

---

## Knowledge Repo Functions

*Note these functions only work on the Nordstorm VPN*

This function will take a markdown document including links and pictures and prepare it to be hosted on the Nordstrom Knowledge Repo Jekyll Site.

**Please Note** Content can only be added to the Knowledge Repo by members of the NordACE org:
Digital, Marketing, Supply Chain, or Corporate Analytics

<a name="render-post">

### `nordypy.render_post()`

</a>
Reformats markdown file to be added to Knowledge Repo including adding a yaml header, uploading any images to s3, and replacing local image refs
with s3 location. If no `output_path` is given, the file will be written to the same directory as the original markdown.

```python
# awscreds needs to be running so that images can be uploaded to s3
nordypy.render_post(file_to_render='my_algorithm_doc.md',
                    post_title='Awesome Nordstrom Algorithm',
                    post_description='A walkthrough of a Nordstrom Algorithm',
                    post_category='marketing',
                    post_tags=['segmentation', 'python', 'tensorflow'],
                    output_path='~/Documents/')
```

---


## Contributors

- Aaron Lichtner 
- Christine Buckler 
- Chuan Chen
- Julie Creamer
- Nick Buker
- Gina Schmalzle

Please direct questions, bugs, and feature requests to Aaron Lichtner (aaron.lichtner@nordstrom.com)
