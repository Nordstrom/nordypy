import pkg_resources


def rock_it(size='large'):
    if size == 'small':
        with open(pkg_resources.resource_filename('nordypy', 'package_resources/assets/default/therock25.txt')) as f:
            therock = f.read()
    else:
        with open(pkg_resources.resource_filename('nordypy', 'package_resources/assets/default/therock.txt')) as f:
            therock = f.read()
    print(therock)
