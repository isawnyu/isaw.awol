from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup

requirements = [
    line.strip() for line in open('REQUIREMENTS.txt')
    if line.strip() and not line.strip().startswith('--')
    ]


setup(
    author='Chuck Jones, Ronak Parpani, Tom Elliott',
    author_email='chuck.jones@nyu.edu, parpanironak@gmail.com, tom.elliott@nyu.edu',
    description='The Ancient World Online: from blog to bibliographic data',
    install_requires=requirements,
    license='See LICENSE.txt',
    long_description=open('README.md').read(),
    name='isaw.awol',
    package_data={
        '': ['*.csv']
    },
    packages=['isaw.awol'],
    url='https://github.com/isawnyu/isaw.awol',
    version='0.1',
)
