#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test code in the article module."""

import logging
import os

from nose import with_setup
from nose.tools import *

from isaw.awol import article

PATH_TEST = os.path.dirname(os.path.abspath(__file__))
PATH_TEST_DATA = os.path.join(PATH_TEST, 'data')
PATH_TEST_TEMP = os.path.join(PATH_TEST, 'temp')

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
    assert_is_not_none(a.id)            
    assert_is_not_none(a.title)         
    assert_is_not_none(a.categories)    
    assert_is_not_none(a.content)       
    assert_is_not_none(a.resources) 
    assert_equals(len(a.resources), 1)    
