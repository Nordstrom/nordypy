import os
import warnings
import datetime
import re
from ._s3 import s3_upload, s3_get_bucket

# TODO: handle .ipynb files


def _post_meta_data(file_to_render=None,
                    post_title=None,
                    post_description=None,
                    post_category=None,
                    post_tags=[]):
    """
    Creates a dictionary of post information to reformat markdown file,
    this is a private function called by the render_post function.

    Parameters
    ----------
    file_to_render : str
        markdown file that you'd like to format for the Knowledge Repo
    post_title : str
        title for Knowledge Repo post
    post_description : str
        description for Knowledge Repo post
    post_category : str
        which category the the post should be under in the Knowledge Repo.
        The category must be one of the following
        four options: "digital", "marketing", "supply_chain", or
        "corporate_analytics".
    post_tags : list of strings
        optional character vector containing tags to attach to the Knowledge
        Repo post. The tags provided are both
        searchable and browsable on the Knowledge Repo.

    Returns
    -------
    A dictionary of meta data for the markdown file to be rendered
    """

    # check args
    if not file_to_render:
        raise ValueError('No file path for file_to_render.')

    if os.path.splitext(file_to_render.lower())[1] != '.md':
        raise ValueError('file_to_render must have a markdown file extension (.md)')

    if not post_title:
        raise ValueError('No post_title given.')

    if not post_description:
        raise ValueError('No post_description given.')

    if post_category not in ['digital', 'marketing', 'supply_chain', 'corporate_analytics']:
        raise ValueError('The post_category must be one of the following four options: '
                         '"digital", "marketing", "supply_chain", or "corporate_analytics".')

    if not post_tags:
        warnings.warn('No post_tags given.')
    elif type(post_tags) is not list:
        raise TypeError('post_tags must be a list.')
    else:
        post_tags = [tag.lower().replace(' ', '-') for tag in post_tags]

    # create meta data dictionary
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    meta_data = {
        'file_to_render': file_to_render,
        'post_title': post_title,
        'post_description': post_description,
        'post_category': post_category,
        'post_tags': post_tags,
        'extension': os.path.splitext(file_to_render)[1],
        'path_to_file': os.path.split(file_to_render)[0],
        'yaml_lines': '\n'.join([
            "---",
            "title: {0}".format(post_title),
            "description: {0}".format(post_description),
            "categories: {0}".format(post_category),
            "tags: {0}".format((', ').join(post_tags)),
            "---"
        ]),
        'rendered_file': current_date + '-' + post_title.replace(' ', '-') + '.md'
    }

    return meta_data


def _image_path_sub(base_text, image_dict):
    """
    Substitutes any local image references in the markdown file with their
    corresponding s3 location. This is a private function called by the
    render_post function.

    Parameters
    ----------
    base_text : str
        original markdown contents
    image_dict : dict
        image dictionary with original refs as keys and s3 refs as values

    Returns
    -------
    A string with the new markdown contents
    """
    for key, val in image_dict.items():
        base_text = base_text.replace(key, val)
    return base_text


def render_post(bucket,
                file_to_render=None,
                post_title=None,
                post_description=None,
                post_category=None,
                post_tags=[],
                output_path=None):
    """
    Reformats markdown file to be added to Knowledge Repo including adding
    a yaml header, uploading any images to s3, and replacing local image refs
    with s3 location.

    Parameters
    ----------
    file_to_render : str [REQUIRED]
        markdown file that you'd like to format for the Knowledge Repo
    post_title : str [REQUIRED]
        title for Knowledge Repo post
    post_description : str [REQUIRED]
        description for Knowledge Repo post
    post_category : str [REQUIRED]
        category the post should be under in the Knowledge Repo. The category
        must be one of the following four options: "digital", "marketing",
        "supply_chain", or "corporate_analytics"
    post_tags : list of strings
        optional character vector containing tags to attach to the Knowledge
        Repo post. The tags provided are both searchable and browsable on the
        Knowledge Repo (e.g. ['personas', 'segmentation', 'clustering', 'python'])
    output_path : str
        desired location of rendered file relative to location where you are running this function
        default location is the same path as the original markdown

    Returns
    -------
    None
    """

    if output_path:
        if not os.path.exists(output_path):
            raise ValueError('output_path is not a valid file location')
    if not bucket:
        raise ValueError('Please specify an S3 bucket')
    s3_bucket = bucket
    # get post meta data
    meta_data = _post_meta_data(file_to_render,
                                post_title,
                                post_description,
                                post_category,
                                post_tags)
    s3_image_url_prefix = 'https://s3-us-west-2.amazonaws.com/' + s3_bucket
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    image_dict = {}

    with open(meta_data['file_to_render']) as old_file:
        for line in old_file:
            # findall image paths in each line (markdown or html format)
            md = re.findall(r'[!]\[.*?\]\((["\'-\/.\\\s\w]+)\)', line)
            html = re.findall(r'<img[-=\/.\\\s\w\'"]+src=[\'"]([-\/.\\\s\w]+)[\'"]', line)
            # create one list of markdown and html refs
            refs = md + html
            if refs:
                # create a dict entry for each image path in file
                for image in refs:
                    # if there is a title after the image path, remove title
                    single_quote_check = image.find('\'')
                    double_quote_check = image.find('\"')
                    if single_quote_check + double_quote_check != -2:
                        image = image[:max([single_quote_check,
                                            double_quote_check])-1]

                    # create hashed image path for s3 image name
                    s3_image = str(hash(image))

                    # upload image to s3
                    s3_file = '/'.join([current_date, meta_data['post_title'].replace(' ', '-'), s3_image])
                    image_dict[image] = '/'.join([s3_image_url_prefix, s3_file])
                    s3_upload(bucket=s3_bucket,
                              s3_filepath=s3_file,
                              local_filepath='/'.join([meta_data['path_to_file'], image]),
                              permission='public-read')

    # default is to write markdown to the same location as the original markdown
    if not output_path:
        output_path = meta_data['path_to_file'] + '/'
    if not output_path.endswith('/'):
        output_path += '/'

    with open(meta_data['file_to_render']) as temp_file:
        new_text = _image_path_sub(temp_file.read(), image_dict)
    with open(output_path + meta_data['rendered_file'], 'w') as new_file:
        new_file.write(meta_data['yaml_lines'] + '\n' + new_text)
