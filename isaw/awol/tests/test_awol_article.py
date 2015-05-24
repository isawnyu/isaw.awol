#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test code in the article module."""

import logging
import os
import re

from nose import with_setup
from nose.tools import *

from isaw.awol import awol_article

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
    """Ensure class parse method gets all desired fields."""

    file_name = os.path.join(PATH_TEST_DATA, 'post-capitale-culturale.xml')
    a = awol_article.AwolArticle(atom_file_name=file_name)
    a.parse_atom_resources()
    assert_equals(len(a.resources), 1)    
    r = a.resources[0]
    assert_equals(r.description, u'Il capitale culturale (ISSN: 2039-2362) \xe8 la rivista del Dipartimento di Beni Culturali dell\u2019Universit\xe0 di Macerata con sede a Fermo, che si avvale di molteplici competenze disciplinari (archeologia, archivistica, diritto, economia aziendale, informatica, museologia, restauro, storia, storia dell\u2019arte) unite dal comune obiettivo della implementazione di attivit\xe0 di studio, ricerca e progettazione per la valorizzazione del patrimonio culturale.')
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
    rx = awol_article.RX_MATCH_DOMAIN
    m = rx.match(url)
    assert_equals(m.group(1), domain)
