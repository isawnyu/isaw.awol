#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test code in the article module."""

import logging
import os
import re

from nose import with_setup
from nose.tools import *

from isaw.awol import article

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
def test_article_init():
    """Ensure class constructor can open and extract XML from file."""

    file_name = os.path.join(PATH_TEST_DATA, 'dummy.xml')
    a = article.Article(file_name)
    assert_is_not_none(a.doc)
    assert_is_not_none(a.root)
    root = a.root
    assert_equals(root.tag, 'dummy')
    assert_equals(root[0].tag, 'head')
    assert_equals(root[1].tag, 'body')
    assert_equals(root[2].tag, 'tail')

def test_article_parse():
    """Ensure class parse method gets all desired fields."""

    file_name = os.path.join(PATH_TEST_DATA, 'post-capitale-culturale.xml')
    a = article.Article(file_name)
    root = a.root
    assert_equals(root.tag, '{http://www.w3.org/2005/Atom}entry')
    a.parse()
    assert_equals(a.id, 
        'tag:blogger.com,1999:blog-116259103207720939.post-107383690052898357')          
    assert_equals(a.title, u'Open Access Journal: Il capitale culturale')      
    assert_equals(a.url, 
        u'http://ancientworldonline.blogspot.com/2011/02/new-open-access-journal-il-capitale.html')   
    assert_equals(
        a.categories, 
        [
            {
                'term': 
                    'http://schemas.google.com/blogger/2008/kind#post',
                'vocabulary':
                    'http://schemas.google.com/g/2005#kind'
            }
        ])    
    assert_is_not_none(a.content)       
    assert_is_not_none(a.resources) 
    assert_equals(len(a.resources), 1)    
    r = a.resources[0]
    assert_is_none(r.description)
    assert_equals(len(r.identifiers), 1)
    assert_equals(r.identifiers['issn'], u'2039-2362')
    assert_equals(r.domain, 'www.unimc.it')
    assert_is_instance(r.subordinate_resources, list)
    assert_is_instance(r.keywords, list)
    assert_is_none(r.language)
    assert_is_instance(r.related_resources, list)
    assert_equals(r.title, 'Il capitale culturale')
    assert_equals(r.url, 'http://www.unimc.it/riviste/index.php/cap-cult/index')


def test_match_domain_in_url():
    """Ensure regular expression to match domain string in URL works."""

    domain = 'isaw.nyu.edu'
    url = 'http://isaw.nyu.edu/news/'
    rx = article.RX_MATCH_DOMAIN
    m = rx.match(url)
    assert_equals(m.group(1), domain)
