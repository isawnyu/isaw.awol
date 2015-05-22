#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test code in the resource module."""

import os

from nose import with_setup
from nose.tools import *

from isaw.awol import article, resource

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
def test_resource_init():
    """Ensure Resource constructor works."""

    r = resource.Resource()
    assert_is_none(r.description)
    assert_is_none(r.domain)
    assert_is_instance(r.subordinate_resources, list)
    assert_is_none(r.isbn)
    assert_is_none(r.issn)
    assert_is_instance(r.keywords, list)
    assert_is_none(r.language)
    assert_is_instance(r.related_resources, list)
    assert_is_none(r.title)
    assert_is_none(r.url)


