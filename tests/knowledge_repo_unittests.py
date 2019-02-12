import nordypy
import unittest
import os
import datetime

class KnowledgeRepoTests(unittest.TestCase):
    def test_render_post_markdown(self):
        nordypy.render_post(file_to_render=markdown_file,
                            post_title=post_title,
                            post_description=post_description,
                            post_category=post_category)
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        self.assertTrue(os.path.isfile(os.path.split(markdown_file)[0] + '/' + current_date + '-' + '-'.join(post_title.split(' ')) + '.md'))
        # upload images
        # check for yaml header
        # check for new markdown file
        os.remove(os.path.split(markdown_file)[0] + '/' + current_date + '-' + '-'.join(post_title.split(' ')) + '.md')

    def test_render_post_markdown_without_slash(self):
        for output_path in ['.', 'knowledge_repo_output']:
            nordypy.render_post(file_to_render=markdown_file,
                                post_title=post_title,
                                post_description=post_description,
                                post_category=post_category,
                                output_path=output_path)
            current_date = datetime.datetime.now().strftime('%Y-%m-%d')
            self.assertTrue(os.path.isfile(output_path + '/' + current_date + '-' + '-'.join(post_title.split(' ')) + '.md'))
            # upload images
            # check for yaml header
            # check for new markdown file
            os.remove(output_path + '/' + current_date + '-' + '-'.join(post_title.split(' ')) + '.md')

    def test_render_post_markdown_new_location(self):
        for output_path in ['./', 'knowledge_repo_output/']:
            nordypy.render_post(file_to_render=markdown_file,
                                post_title=post_title,
                                post_description=post_description,
                                post_category=post_category,
                                output_path=output_path)
            current_date = datetime.datetime.now().strftime('%Y-%m-%d')
            self.assertTrue(os.path.isfile(output_path + current_date + '-' + '-'.join(post_title.split(' ')) + '.md'))
            # upload images
            # check for yaml header
            # check for new markdown file
            os.remove(output_path + current_date + '-' + '-'.join(post_title.split(' ')) + '.md')

    def test_render_post_markdown_bad_path(self):
        output_path = 'no_directory/'
        self.assertRaises(ValueError, lambda : nordypy.render_post(file_to_render=markdown_file,
                            post_title=post_title,
                            post_description=post_description,
                            post_category=post_category,
                            output_path=output_path))

    def test_render_post_ipython(self):
        # upload images
        # check for yaml header
        # check for new markdown file
        pass


    def test_render_post_wrong_metadata(self):
        self.assertRaises(ValueError,
                          lambda : nordypy.render_post(file_to_render=markdown_file))
        self.assertRaises(ValueError,
                          lambda : nordypy.render_post(file_to_render=markdown_file,
                                                       post_title=post_title,
                                                       post_description=post_description,
                                                       post_category='wrong thing'))


if __name__ == '__main__':
    markdown_file = 'test_markdown/test.md'
    post_title = 'nordypy test'
    post_description = "a test for nordypy's knowledge repo render function"
    post_category = 'digital'
    unittest.main()
