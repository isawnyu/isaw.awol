#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test code in the article module."""

import logging
import os

from nose import with_setup
from nose.tools import *

from isaw.awol.awol_article import *

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
def test_awol_article_init():
    """Ensure class parse method gets all desired fields."""

    file_name = os.path.join(PATH_TEST_DATA, 'post-capitale-culturale.xml')
    a = AwolArticle(atom_file_name=file_name)

def test_match_domain_in_url():
    """Ensure regular expression to match domain string in URL works."""

    domain = 'isaw.nyu.edu'
    url = 'http://isaw.nyu.edu/news/'
    rx = RX_MATCH_DOMAIN
    m = rx.match(url)
    assert_equals(m.group(1), domain)

def test_xml():
    """Ensure we can load and parse problematic XML."""

    file_name = os.path.join(PATH_TEST_DATA, 'post-doaks-online.xml')
    a = AwolArticle(atom_file_name=file_name)
    del a

