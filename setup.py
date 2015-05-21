from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup


setup(
    author='Chuck Jones, Ronak Parpani, Tom Elliott',
    author_email='chuck.jones@nyu.edu, parpanironak@gmail.com, tom.elliott@nyu.edu',
    data_files=[('data', ['data/awol_colon_prefixes.csv', 'awol_title_strings.csv']),],
    description='The Ancient World Online: from blog to bibliographic data',
    install_requires=['pyzotero', 'django', 'beautifulsoup4'],
    license='See LICENSE.txt',
    long_description=open('README.md').read(),
    name='isaw.awol',
    packages=['isaw.awol'],
    url='https://github.com/isawnyu/isaw.awol',
    version='0.1',
)
