#### Updates Version 2.0.0

- new functions, bug fixes, ....

#### Updates Version 1.3.1

#### Updates Version 1.2.2

- Development structure was changed so that any changes made to the `public-github` branch inside of *gitlab* will automatically flow to `public-github` on Nordstrom's public-facing *github* acccount

#### Updates Version 1.2.1

- Nordypy is now in Github and PyPi! You can install with `pip install nordypy`.

#### Updates Version 1.1.2

- [`render_post()`]() has new `output_path` parameter that lets the user set where the final file is written

#### Updates Version 1.1.1

- Fixed bug where the `config.yaml` file wasn't found in the `package_resources/` folder
- Added function `nordypy.create_config_file()` to make just the config file where you want it

#### Updates Version 1.1.0

 - **Removed submodule dependency**, this should reduce the size of the package and reduce gitlab errors on installation.

#### New functions

 - [`database_get_column_names()`]() returns a list of columns and their datatypes in a redshift table
 - [`database_insert()`]() append new records onto already existing redshift tables
 - [`s3_delete()`]() provide a bucket and a single file or list of files to delete from s3
 - [`render_post()`]() prepares a markdown file to be rendered on the Knowledge Repo Jekyll Site

#### Updated Functions

 - Apply read-write permissions to objects uploaded using `s3_upload()`
 - Added timestamps as a datatype in `database_create_table()`
 - Can now pass a connection object to `redshift_to_s3()` so you can create temporary tables and then move them to s3

#### Updates Version 1.0.2

- QUERY_GROUP selection is available using the `query_group` parameter in the following functions
    - [`database_execute()`](#database-execute)
    - [`database_get_data()`](#database-get-data)
    - [`database_to_pandas()`](#database-to-pandas)
    - [`redshift_to_redshift()`](#redshift-to-redshift)
    - [`redshift_to_s3()`](#redshift-to-s3)
- MySQL support

#### Updates Version 1.0.1

- automated selection of `local` vs. `aws`
- added json functionality to pandas_to_s3 method


#### New functions

- new [`s3_to_pandas()`](#s3-to-pandas) function
- new  [`s3_list_buckets()`](#s3-list-buckets) function
