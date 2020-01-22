# Changelog

All notable changes to this project will be documented in this file.

## Version 2.0.0 - 2020-01-22

### Added

- `s3_get_matching_keys()` generator function to return matching s3 keys (MR !56)
- `s3_get_matching_objects()` generator function to return matching s3 objects (MR !56)
- **Teradata Support**: for `database_connect()`, `database_get_data()`, and `database_execute()` (MR !58)
- `database_list_tables()` to list redshift tables based on search criteria (MR !54)

### Changed

- Improved `_create_table_statement()` to use more appropriate datatypes between pandas and redshift (MR !62)
- added `autocommit=True` to `database_connect()` for redshift, mysql and teradata (MR !59)

### Fixed

- fixed `_create_table_statement()` function to not fail on column names with quotes, spaces, dashes, etc. (MR !62)
- fixed bug in `database_execute()` where commented out SQL was still executed by adding `_datasource._strip_sql()` which uses RegEx (MR !59)
- fixed `YAMLLoadWarning` by using the `yaml.FullLoader` (MR !54)

## Version 1.3.1 - 2019-12-19

### Added

- `athena_to_pandas()` function added which runs an athena query and pulls the data into a local pandas dataframe (MR !50)

## Version 1.2.2 - 2019-11-22

### Changed

- Development structure was changed so that any changes made to the `public-github` branch inside of *gitlab* will automatically flow to `public-github` on Nordstrom's public-facing *github* acccount (MR !49)

## Version 1.2.1 - 2019-02-11

### Changed

- Nordypy is now in Github and PyPi! You can install with `pip install nordypy`.

## Version 1.1.2

### Changed

- `render_post()` has new `output_path` parameter that lets the user set where the final file is written

## Version 1.1.1

### Added

- Added function `nordypy.create_config_file()` to make just the config file where you want it

### Fixed

- Fixed bug where the `config.yaml` file wasn't found in the `package_resources/` folder

## Version 1.1.0

### Added

- `database_get_column_names()` returns a list of columns and their datatypes in a redshift table
- `database_insert()` append new records onto already existing redshift tables
- `s3_delete()` provide a bucket and a single file or list of files to delete from s3
- `render_post()` prepares a markdown file to be rendered on the Knowledge Repo Jekyll Site
- added to change read-write permissions to objects uploaded using `s3_upload()`
- added timestamps as a datatype in `database_create_table()`

### Changed

- Can now pass a connection object to `redshift_to_s3()` so you can create temporary tables and then move them to s3

### Removed

- **Removed submodule dependency**, this should reduce the size of the package and reduce gitlab errors on installation.

## Version 1.0.2

### Added

- QUERY_GROUP selection is available using the `query_group` parameter in the following functions
    - [`database_execute()`](#database-execute)
    - [`database_get_data()`](#database-get-data)
    - [`database_to_pandas()`](#database-to-pandas)
    - [`redshift_to_redshift()`](#redshift-to-redshift)
    - [`redshift_to_s3()`](#redshift-to-s3)
- MySQL support

## Updates Version 1.0.1

### Added

- automated selection of `local` vs. `aws`
- added json functionality to pandas_to_s3 method

### Added

- new [`s3_to_pandas()`](#s3-to-pandas) function
- new  [`s3_list_buckets()`](#s3-list-buckets) function
