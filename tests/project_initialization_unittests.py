import nordypy
import unittest
import os
import sys

class ProjectInitializationTests(unittest.TestCase):
	def test_initializate_project_root(self):
		if not os.path.exists('testing_dir'):
			os.mkdir('testing_dir')
		os.chdir('testing_dir')
		self.assertEqual(nordypy.initialize_project('default'), True)
		for file in files:
			self.assertEqual(os.path.isfile(file), True)
		for folder in folders:
			self.assertEqual(os.path.exists(folder), True)
	
	def test_initialize_project_chdir(self):
		# check if dir exists
		# are we back at starting dir
		# were files and folders created
		pass
	
	def test_initialize_project_chdir_not_exists(self):
		dir = 'fake_dir/'
		current_dir = os.getcwd()
		if sys.version[0] == '3':
			print(sys.version)
			self.assertRaises(FileNotFoundError, lambda: nordypy.initialize_project(structure='default', path=dir)) # dir doesn't exist
		elif sys.version[0] == '2':
			self.assertRaises(OSError, lambda: nordypy.initialize_project(structure='default', path=dir)) # dir doesn't exist
		os.makedirs(dir)
		self.assertEqual(nordypy.initialize_project(structure='default', path=dir), True) # create folders in different dir
		self.assertEqual(os.getcwd(), current_dir) # make sure that we moved back to the current dir
		os.chdir(dir)
		for file in files:
			self.assertEqual(os.path.isfile(file), True)
		for folder in folders:
			self.assertEqual(os.path.exists(folder), True)
	
	def test_initialize_project_old_files(self):
		pass
	
	def test_initialize_only_folders(self):
		# remove files and folders
		self.assertEqual(nordypy._init_methods._undo_create_project(really=True), True)
		for file in files:
			self.assertEqual(os.path.isfile(file), False)
		for folder in folders:
			self.assertEqual(os.path.exists(folder), False)
		self.assertEqual(nordypy.initialize_project(structure='default', create_folders=True, create_files=False), True)
		for file in files:
			self.assertEqual(os.path.isfile(file), False)
		for folder in folders:
			self.assertEqual(os.path.exists(folder), True)
	
	def test_initialize_only_files(self):
		# remove files and folders
		self.assertEqual(nordypy._init_methods._undo_create_project(really=True), True)
		for file in files:
			self.assertEqual(os.path.isfile(file), False)
		for folder in folders:
			self.assertEqual(os.path.exists(folder), False)
		# create only files
		self.assertEqual(nordypy.initialize_project(structure='default', create_folders=False, create_files=True), True)
		for file in files:
			self.assertEqual(os.path.isfile(file), True)
		for folder in folders:
			self.assertEqual(os.path.exists(folder), False)
	
	def test_make_rock(self):
		pass
	
	def test_uninitialize(self):
		# make sure there are files here
		for file in files:
			self.assertEqual(os.path.isfile(file), True)
		for folder in folders:
			self.assertEqual(os.path.exists(folder), True)
		# test that it won't run unless really=True
		self.assertEqual(nordypy._init_methods._undo_create_project(), False)
		self.assertEqual(nordypy._init_methods._undo_create_project(really=True), True)
		# make sure those files are gone
		for file in files:
			self.assertEqual(os.path.isfile(file), False)
		for folder in folders:
			self.assertEqual(os.path.exists(folder), False)
		# go to the testing_dir and remove those files
		os.chdir('..')
		self.assertEqual(nordypy._init_methods._undo_create_project(really=True), True)
		for file in files:
			self.assertEqual(os.path.isfile(file), False)
		for folder in folders:
			self.assertEqual(os.path.exists(folder), False)
		# clean up
		dir = 'fake_dir/'
		os.rmdir(dir)
		os.chdir('..')
		os.rmdir('testing_dir')
	
if __name__ == '__main__':
	files = ['README.md', 'config.yaml', '.gitignore']
	folders = ['code', 'data', 'logs', 'sandbox', 'output', 'docs', 'code/python', 'code/R', 'code/SQL']
	unittest.main()