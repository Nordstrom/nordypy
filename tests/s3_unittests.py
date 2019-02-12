import nordypy
import unittest
import pandas as pd
import json
from boto3.session import Session

class S3Tests(unittest.TestCase):
	def test_get_bucket(self):
		test_bucket = nordypy.s3_get_bucket(bucket=bucket, environment=env)
		self.assertEqual(test_bucket.name, bucket)

	def test_s3_put(self):
		nordypy.s3_upload(bucket=bucket, environment=env, s3_filepath='test_s3_upload', local_filepath='titanic_data.csv')

	def test_s3_get(self):
		pass

	def test_s3_delete(self):
		s3_filepath='test_s3_delete/titanic_data.csv'
		nordypy.s3_upload(bucket=bucket, s3_filepath=s3_filepath, local_filepath='titanic_data.csv')
		resp = nordypy.s3_delete(bucket=bucket, s3_filepath=s3_filepath)
		self.assertIsInstance(resp, list)
		self.assertEqual(resp[0]['Key'], s3_filepath)

	def test_s3_rename(self):
		pass

	def test_s3_list_objects(self):
		self.assertIsInstance(nordypy.s3_list_objects(bucket=bucket, environment=env, max_keys=100), dict)
		self.assertIsInstance(nordypy.s3_list_objects(bucket=bucket, max_keys=100, only_keys=True), list)
		self.assertIsInstance(nordypy.s3_list_objects(bucket=bucket, max_keys=100), dict)
		keys = nordypy.s3_list_objects(bucket=bucket, prefix='nordypy', only_keys=True)
		self.assertEqual(False in [True if k.startswith('nordypy') else False for k in keys], False)


	def test_s3_list_buckets(self):
		self.assertIsInstance(nordypy.s3_list_buckets(environment=env), list)

	def test_pandas_to_s3(self):
		# test pushing a dataframe to s3 as a csv
		df = pd.read_csv('titanic_data.csv')
		shape = df.shape
		f = 'nordypy/pandas_titanic_upload.csv'
		nordypy.pandas_to_s3(df, bucket=bucket, s3_filepath=f, header=True, index=True)
		self.assertEqual(shape, nordypy.s3_to_pandas(bucket=bucket, s3_filepath=f).shape)
		f = 'nordypy/pandas_titanic_upload_delim.csv'
		nordypy.pandas_to_s3(df, bucket=bucket, s3_filepath=f, header=True, index=True, delimiter=',')
		self.assertEqual(shape, nordypy.s3_to_pandas(bucket=bucket, s3_filepath=f).shape)
		f = 'nordypy/pandas_titanic_upload'
		nordypy.pandas_to_s3(df, bucket=bucket, s3_filepath=f, header=True, index=True, delimiter=',')
		self.assertEqual(shape, nordypy.s3_to_pandas(bucket=bucket, s3_filepath=f).shape)

	def test_pandas_to_s3_json(self):
		# test all the ways you can write a json to s3 from a pandas df
		def read_json(file):
			with open(file, 'r') as infile:
				return json.load(infile)

		df = pd.read_csv('titanic_data.csv')
		f = 'nordypy/pandas_titanic_upload.json'
		local_f = 'test.json'
		nordypy.pandas_to_s3(df, bucket=bucket, s3_filepath=f, orient='split')
		nordypy.s3_download(bucket=bucket, s3_filepath=f, local_filepath=local_f)
		data = read_json(local_f)
		self.assertEqual(3, len(data.keys())) # should be just columns, index, data
		nordypy.pandas_to_s3(df, bucket=bucket, s3_filepath=f, orient='records')
		nordypy.s3_download(bucket=bucket, s3_filepath=f, local_filepath=local_f)
		data = read_json(local_f)
		self.assertEqual(1310, len(data))  # list of each record
		nordypy.pandas_to_s3(df, bucket=bucket, s3_filepath=f, orient='index')
		nordypy.s3_download(bucket=bucket, s3_filepath=f, local_filepath=local_f)
		data = read_json(local_f)
		self.assertEqual(1310, len(data.keys()))  # dictionary keyed on the index of the record
		nordypy.pandas_to_s3(df, bucket=bucket, s3_filepath=f, orient='columns')
		nordypy.s3_download(bucket=bucket, s3_filepath=f, local_filepath=local_f)
		data = read_json(local_f)
		self.assertEqual(14, len(data.keys()))  # dictionary keyed on the different columns
		nordypy.pandas_to_s3(df, bucket=bucket, s3_filepath=f, orient='values')
		nordypy.s3_download(bucket=bucket, s3_filepath=f, local_filepath=local_f)
		data = read_json(local_f)
		self.assertEqual(1310, len(data))  # list of each record




	def test_s3_wildcard_get(self):
		pass

	def test_s3_wildcard_put(self):
		pass

	def test_s3_delete_bucket(self):
		pass

	def test_s3_get_temp_creds(self):
		self.assertIsInstance(nordypy._s3._s3_get_temp_creds(environment=env), str)

	def test_s3_create_session(self):
		self.assertIsInstance(nordypy._s3._s3_create_session(environment=env), Session)

	def test_s3_create_bucket(self):
		pass

	def test_s3_upload_with_permissions(self):
		pass

	def test_s3_change_permissions(self):
		file = 'nordypy/pandas_titanic_upload.csv'
		nordypy.s3_change_permissions(bucket=bucket,s3_filepath=file, permission='public-read-write')
		acl, _ = nordypy.s3_get_permissions(bucket=bucket, s3_filepath=file)
		self.assertEqual(acl[0], 'public-read-write')
		nordypy.s3_change_permissions(bucket=bucket,s3_filepath=file, permission='authenticated-read')
		acl, _ = nordypy.s3_get_permissions(bucket=bucket, s3_filepath=file)
		self.assertEqual(acl[0], 'authenticated-read')

	def test_s3_get_permissions(self):
		acl, grants = nordypy.s3_get_permissions(bucket=bucket, s3_filepath='nordypy/pandas_titanic_upload.csv')
		self.assertIsInstance(acl, list)
		self.assertIsInstance(grants, list)


class S3RedshiftTests(unittest.TestCase):
	def test_s3_to_redshift(self):
		pass

	def test_redshift_to_s3(self):
		pass

	def test_redshift_to_s3_no_copy_command(self):
		pass

	def test_redshift_to_redshift(self):
		pass


if __name__ == '__main__':
	bucket = 'nordypy'
	env = 'local'
	unittest.main()
