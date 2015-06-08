#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test code in the article module."""

import logging
import os
import sys

from nose import with_setup
from nose.tools import *

from isaw.awol.parse.awol_parsers import AwolParsers
from isaw.awol.awol_article import AwolArticle


PATH_TEST = os.path.dirname(os.path.abspath(__file__))
PATH_TEST_DATA = os.path.join(PATH_TEST, 'data')
PATH_TEST_TEMP = os.path.join(PATH_TEST, 'temp')

logging.basicConfig(level=logging.DEBUG)

def setup_function():
    """Test harness setup."""

    pass

def teardown_function():
    """Test harness teardown."""

    pass

@with_setup(setup_function, teardown_function)
def test_parsers_init():

    parsers = AwolParsers()
    plist = parsers.parsers
    # trap for untested addition of a parser
    assert_equals(len(plist.keys()), 2)    
    # test for known parsers
    assert_true('generic' in plist.keys())
    assert_true('www.persee.fr' in plist.keys())

@with_setup(setup_function, teardown_function)
def test_parsers_get_domains():

    file_name = os.path.join(PATH_TEST_DATA, 'post-capitale-culturale.xml')
    a = AwolArticle(atom_file_name=file_name)
    parsers = AwolParsers()
    # verify generic parser can get domains
    domains = parsers.parsers['generic'].get_domains(a.soup)
    assert_equals(len(domains), 1)
    assert_equals(domains[0], 'www.unimc.it')
    # verify parser collection can do the same (using generic underneath)
    domains = parsers.get_domains(a.soup)
    assert_equals(len(domains), 1)
    assert_equals(domains[0], 'www.unimc.it')

@with_setup(setup_function, teardown_function)
def test_parsers_parse():

    file_name = os.path.join(PATH_TEST_DATA, 'post-capitale-culturale.xml')
    a = AwolArticle(atom_file_name=file_name)
    parsers = AwolParsers()
    resources = parsers.parse(a)


    

