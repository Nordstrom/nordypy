import pkg_resources
import datetime
import pystache

def make_one_pager(title='Analytics Project', author=None, author_email=None, team='NORDACE, DSA', date='today', stakeholder=None, jira=None,
                   reviewer=None, reviewer_email=None):
	"""
	Create one pager.

	Parameters
	----------
	author (str)
		- author name
	author_email (str)
		- author email
	team (str)
		- author team
	date (str)
		- date report published
	stakeholder (str)
		- stakeholder name or team
	jira (int or list)
		- jira story id(s)
	reviewer (str)
		- reviewer name
	reviewer_email
		- reviewer email

	Returns
	-------
	Builds one-pager markdown

	Examples
	--------
	>>> nordypy.make_one_pager(author='Chuan Chen', jira='2037')
	"""
	with open(pkg_resources.resource_filename('nordypy', 'nordstrom_package_resources/one-pager.md')) as f:
		template = f.read()
	
	if date == 'today':
		date = str(datetime.datetime.today().date())
	if jira:
		jira_dict = {'story': []}
		for story in jira:
			jira_dict['story'].append({'jira': story})
			
	context = {'title': title, 'author': author, 'author_email': author_email, 'reviewer': reviewer,
	        'reviewer_email': reviewer_email,'date': date, 'stakeholder': stakeholder, 'story': jira_dict}
	
	template = pystache.render(template, context)
	with open('one-pager.md', 'w') as outfile:
		outfile.write(template)
		
	
	
	print('One Pager Built')
