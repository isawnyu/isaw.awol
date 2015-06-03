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
    assert_is_instance(r.identifiers, dict)
    assert_is_instance(r.keywords, list)
    assert_is_none(r.language)
    assert_is_instance(r.provenance, list)
    assert_is_instance(r.related_resources, list)
    assert_is_none(r.title)
    assert_is_none(r.url)
    assert_is_none(r.zotero_id)

@with_setup(setup_function, teardown_function)
def test_json_dumps():
    """Ensure json serialization works."""

    r = resource.Resource()
    r.description = unicode("Il capitale culturale (ISSN: 2039-2362) \u00e8 la rivista del Dipartimento di Beni Culturali dell\u2019Universit\u00e0 di Macerata con sede a Fermo, che si avvale di molteplici competenze disciplinari (archeologia, archivistica, diritto, economia aziendale, informatica, museologia, restauro, storia, storia dell\u2019arte) unite dal comune obiettivo della implementazione di attivit\u00e0 di studio, ricerca e progettazione per la valorizzazione del patrimonio culturale.")
    r.domain = "www.unimc.it"
    r.identifiers = {"issn": "2039-2362"}
    r.keywords = [
    "antiquity", 
        "archaeology", 
        "art", 
        "cultural heritage", 
        "culture", 
        "heritage", 
        "history", 
        "journal", 
        "law", 
        "museums", 
        "open access"
    ]
    r.language = ['it', 1.0]
    r.related_resources = []
    r.subordinate_resources = []
    r.title = unicode("Il capitale culturale")
    r.url = unicode("http://www.unimc.it/riviste/index.php/cap-cult/index")
    r.zotero_id = None 
    js = r.json_dumps()
    assert_equals(js, '{"subordinate_resources": [], "domain": "www.unimc.it", "description": "Il capitale culturale (ISSN: 2039-2362) \\\\u00e8 la rivista del Dipartimento di Beni Culturali dell\\\\u2019Universit\\\\u00e0 di Macerata con sede a Fermo, che si avvale di molteplici competenze disciplinari (archeologia, archivistica, diritto, economia aziendale, informatica, museologia, restauro, storia, storia dell\\\\u2019arte) unite dal comune obiettivo della implementazione di attivit\\\\u00e0 di studio, ricerca e progettazione per la valorizzazione del patrimonio culturale.", "language": ["it", 1.0], "title": "Il capitale culturale", "url": "http://www.unimc.it/riviste/index.php/cap-cult/index", "identifiers": {"issn": "2039-2362"}, "related_resources": [], "zotero_id": null, "keywords": ["antiquity", "archaeology", "art", "cultural heritage", "culture", "heritage", "history", "journal", "law", "museums", "open access"], "history": []}')

@with_setup(setup_function, teardown_function)
def test_json_load():
    """Ensure json read from file works."""

    r = resource.Resource()
    path_json = os.path.join(PATH_TEST_DATA, 'il-capitale-culturale.json')
    r.json_load(path_json)
    assert_equals(r.description, u"Il capitale culturale (ISSN: 2039-2362) \u00e8 la rivista del Dipartimento di Beni Culturali dell\u2019Universit\u00e0 di Macerata con sede a Fermo, che si avvale di molteplici competenze disciplinari (archeologia, archivistica, diritto, economia aziendale, informatica, museologia, restauro, storia, storia dell\u2019arte) unite dal comune obiettivo della implementazione di attivit\u00e0 di studio, ricerca e progettazione per la valorizzazione del patrimonio culturale.")
    assert_equals(r.domain, "www.unimc.it")
    assert_equals(r.identifiers, {"issn": "2039-2362"})
    assert_equals(r.keywords, [
    "antiquity", 
        "archaeology", 
        "art", 
        "cultural heritage", 
        "culture", 
        "heritage", 
        "history", 
        "journal", 
        "law", 
        "museums", 
        "open access"
    ])
    assert_equals(r.language, ['it', 1.0])
    assert_equals(r.related_resources, [])
    assert_equals(r.subordinate_resources, [])
    assert_equals(r.title, u"Il capitale culturale")
    assert_equals(r.url, u"http://www.unimc.it/riviste/index.php/cap-cult/index")
    assert_is_none(r.zotero_id)


