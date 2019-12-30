import os
import pkg_resources
from shutil import copyfile
from nordypy import _nordstrom_rock_it
import yaml


def _unpack_folder_structure(structure):
    """Private function that determines the folder structure from a given
    template in the package_resources part of nordypy."""
    high_level = [folder for folder in structure if '/' not in folder]
    low_level = {}
    for folder in structure:
        if '/' in folder:
            directory, subdirectory = folder.split('/')
            if directory in low_level:
                low_level[directory].append(subdirectory)
            else:
                low_level[directory] = [subdirectory]
    return high_level, low_level

def create_config_file(path = './', ask_me = False):
    '''
    Write config.yaml. Takes user input and generates a config.yaml
    file in the directory indicated.
    path: str
        path to send config file
    ask_me: bool
        If true, function will prompt user for details and build the config file
        If false, function copies config file from 
        nordypy/package_resources/assets/default/config.yaml
    '''
    filename = path + 'config.yaml'
    if ask_me:
        print(' --- Create your config.yaml by answering a series of questions: ---')
        print(" --- NOTE: Do NOT wrap your answers with '' ")
        def get_params():
            database = input('YAML database_key (ex. dsa): ')
            secret = input('Do you have an AWS secret name? (y/n): ')
            if secret in ['y', 'Y', 'yes', 'Yes', 'True']:
                secret_name = input('Secret name: ')
                region_name = input('Region name (default = us-west-2): ')
                if region_name == '':
                    region_name = 'us-west-2'
                blob = {database: {'secret_name': secret_name,
                                   'region_name': region_name}
                }
            else: 
                host = input('Host: ')
                user = input('Username: ')
                password = input('Password: ')
                dbtype = input('Database type (redshift, mysql or teradata): ').lower()
                while dbtype not in ['redshift', 'mysql', 'teradata']:
                    dbtype = input('Try again: dbtype can be either redshift, mysql or teradata: ')
                if dbtype == 'redshift' or dbtype == 'mysql':
                    port = input('Port (ex. 5439): ')
                    while not port.isdigit():
                        port = input('Port must be an integer (ex. 5439): ')
                    dbname = input('dbname (ex. analytics_prd): ')
                    blob = {database : {'host': host,
                                        'port': int(port),
                                        'dbname': dbname,
                                        'user': user,
                                        'password': password,
                                        'dbtype': dbtype}
                    }
                elif dbtype == 'teradata':
                    use_ldap = input('Use Ldap (true/false):')
                    blob = {database : {'host': host,
                                        'user': user,
                                        'password': password,
                                        'use_ldap': use_ldap,
                                        'dbtype': dbtype}
                    }
                else:
                    blob = {}
            return blob
        i = 1
        config_dict = {}
        while i == 1:
            config_dict.update(get_params())
            add_another = input('Add another database? (y/n): ')
            print('\n')
            if add_another in ['n', 'N', 'No', 'no', 'False']:
                i = 0
        if os.path.isfile(filename):  # check if file exists already
            overwrite = input('File already exists at {}, overwrite? (y/n): '.format(filename))
            if overwrite in ['y', 'Y', 'yes', 'Yes', 'True']:
                pass
            else:  # change filename to not overwrite old one
                newfilename = input('New filename? ex. updated_config.yaml: ')
                filename = path + newfilename
        with open(filename, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)
        print('Thanks! Config file {0} created.'.format(filename))

    else:
        if os.path.isfile(filename):
            overwrite = input('File already exists at {}, overwrite? (y/n): '.format(filename))
            if overwrite in ['y', 'Y', 'yes', 'Yes', 'True']:
                copyfile(pkg_resources.resource_filename('nordypy',
                                                         'package_resources/assets/default/config.yaml'), filename)
                print('Thanks! Config file {0} created.'.format(filename))
            else:  # change filename to not overwrite old one
                print('File already exists at fake/config.yaml, please remove.')


def display_available_templates():
    """Helper function to display available templates"""
    print('Available Folder Structures: ')
    print("-- default, marketing\n")


def initialize_project(structure=None, create_folders=True, create_files=True,
                       path='.', ask_me=False):
    """Create standard folder structure for analytics and data science
    projects. Generate template files as well.

    Parameters
    ----------
    structure : str
        key to the type of structure to create, ex. 'default',
        'marketing/default'
    create_folders : bool
        create folder tree
    create_files : bool
        create template files for project
    path : str
        relative path where files and folders should be built from

    Returns
    -------
    True

    Examples
    --------
    >>> nordypy.initialize_project('default')
    """
    yaml_root = 'package_resources/assets/{}/folder_structure.yaml'
    if not structure:
        print('Please provide a valid folder structure to be used.\n')
        display_available_templates()
        structure = str(input('Which structure would you like?: '))
    if type(structure) is not str:
        raise ValueError('Structure argument must be of type str')
    if '/' in structure:
        asset, structure = structure.split('/')
        yaml_location = yaml_root.format(asset)
    else:  # if only a single key is given
        yaml_location = yaml_root.format(structure)
        if pkg_resources.resource_exists('nordypy', yaml_location):
            structure = 'default'
        else:
            yaml_location = yaml_root.format('default')
    if path != '.':
        current_dir = os.getcwd()
        try:
            os.chdir(path)
        except OSError as e:  # handles both python 2 and 3
            raise (e)

    # load up official structures
    yaml_location = pkg_resources.resource_filename('nordypy', yaml_location)
    with open(yaml_location, 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    files = cfg[structure]['files']  # files to build
    structure = cfg[structure]['structure']  # folder structure to build
    high_level, low_level = _unpack_folder_structure(structure)

    if create_folders:
        for directory in high_level:
            if not os.path.exists(directory):
                os.makedirs(directory)
        for directory in low_level.keys():
            for subdirectory in low_level[directory]:
                subdirectory = str(directory) + '/' + subdirectory
                if not os.path.exists(subdirectory):
                    os.makedirs(subdirectory)
    if create_files:
        for file in files:
            print(file['name'])
            if not os.path.isfile(file['name']):
                if (file['name'] == 'config.yaml') & (ask_me is True):
                    os.chdir(current_dir)
                    create_config_file(path=path, ask_me=True)
                    os.chdir(path)
                else:
                    copyfile(pkg_resources.resource_filename('nordypy',
                             'package_resources/' + file['file']), file['name'])
                    print('Created {} file'.format(file['name']))
    print('Ready to Rock!!!!')
    _nordstrom_rock_it.rock_it('small')
    if path != '.':
        os.chdir(current_dir)
    return True


def _undo_create_project(really=False, path='.'):
    """Private function to remove files and folders generated on initialization.

    Parameters
    ----------
    really : bool
        do you really want to do this?
    path : filepath
        the root directory

    Returns
    -------
    bool
    """
    if not really:
        print('Do you really want to remove files and folders?')
        return really
    if path != '.':
        current_dir = os.getcwd()
        os.chdir(path)
    if os.path.isfile('.gitignore'):
        os.remove('.gitignore')
    if os.path.isfile('README.md'):
        os.remove('README.md')
    if os.path.isfile('config.yaml'):
        os.remove('config.yaml')
    for directory in ['code/python', 'code/R', 'code/SQL', 'code', 'sandbox',
                      'data', 'logs', 'output', 'docs']:
        if os.path.exists(directory):
            os.rmdir(directory)
    if path != '.':
        os.chdir(current_dir)
    return really


def hello():
    print("Hi, I'm the Nordypy package and I'm here to help you!")
