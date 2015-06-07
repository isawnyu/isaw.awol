#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test code in the article module."""

import logging
import os
import sys

from nose import with_setup
from nose.tools import *

from isaw.awol.parse.awol_parsers import AwolParsers


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

