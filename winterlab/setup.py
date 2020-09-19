import setuptools

with open('README.md', 'r') as f:
	long_description = f.read()

setuptools.setup(
	name='winterlab',
	version='0.0.1',
	author='Maclean Rouble',
	author_email='m.rouble@gmail.com',
	description='',
	long_description=long_description,
	long_description_content_type='text/markdown',
	url='',
	packages=setuptools.find_packages(),
	classifiers=[''],)