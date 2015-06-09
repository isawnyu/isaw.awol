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
    assert_equals(len(plist.keys()), 3)    
    # test for known parsers
    assert_true('generic' in plist.keys())
    assert_true('www.persee.fr' in plist.keys())
    assert_true('www.ascsa.edu.gr' in plist.keys())

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
def test_parsers_generic():

    file_name = os.path.join(PATH_TEST_DATA, 'post-capitale-culturale.xml')
    a = AwolArticle(atom_file_name=file_name)
    parsers = AwolParsers()
    resources = parsers.parse(a)
    r = resources[0]
    assert_equals(r.title, u'Il capitale culturale')
    assert_equals(r.title_extended, u'Il capitale culturale. Studies on the Value of Cultural Heritage')
    assert_equals(r.url, 'http://www.unimc.it/riviste/index.php/cap-cult/index')
    assert_equals(r.description, u'Il capitale culturale. Studies on the Value of Cultural Heritage ISSN: 2039-2362 (ISSN: 2039-2362) è la rivista del Dipartimento di Beni Culturali dell’Università di Macerata con sede a Fermo, che si avvale di molteplici competenze disciplinari (archeologia, archivistica, diritto, economia aziendale, informatica, museologia, restauro, storia, storia dell’arte) unite dal comune obiettivo della implementazione di attività di studio, ricerca e progettazione per la valorizzazione del patrimonio culturale.')
    assert_equals(r.language, ('it', 1.0))
    assert_equals(r.domain, 'www.unimc.it')
    assert_equals(sorted(r.keywords), sorted([u'culture', u'journal', u'cultural heritage', u'open access', u'heritage']))
    assert_equals(r.identifiers, {'issn': {'electronic': [u'2039-2362']}})
    del resources

@with_setup(setup_function, teardown_function)
def test_parsers_persee():

    file_name = os.path.join(PATH_TEST_DATA, 'post-archeonautica.xml')
    a = AwolArticle(atom_file_name=file_name)
    parsers = AwolParsers()
    resources = parsers.parse(a)
    r = resources[0]
    assert_equals(r.title, u'Archaeonautica')
    assert_equals(r.url, 'http://www.persee.fr/web/revues/home/prescript/revue/nauti')
    assert_equals(r.description, u'Archaeonautica eISSN - 2117-6973 Archaeonautica est une collection créée en 1977 par le CNRS et le Ministère de la Culture à l’initiative de Bernard Liou. Publiée par CNRS Edition, le secrétariat de rédaction de la collection est assuré par le Centre Camille Jullian. Le but de la collection est la publication des recherches d’archéologie sous-marines ou, plus généralement, subaquatique, de la Préhistoire à l’époque moderne. Elle est aussi destinée à accueillir des études d’archéologie maritime et d’archéologie navale, d’histoire maritime et d’histoire économique.')
    assert_equals(r.language, ('fr', 1.0))
    assert_equals(r.domain, 'www.persee.fr')
    assert_equals(sorted(r.keywords), sorted([u'journal', u'open access', u'archaeology', u'nautical archaeology']))
    assert_equals(r.identifiers, {'issn': {'electronic': [u'2117-6973']}})
    del resources

    file_name = os.path.join(PATH_TEST_DATA, 'post-gallia-prehistoire.xml')
    a = AwolArticle(atom_file_name=file_name)
    parsers = AwolParsers()
    resources = parsers.parse(a)
    r = resources[0]
    assert_equals(r.title, u'Gallia Préhistoire')
    assert_equals(r.url, 'http://www.persee.fr/web/revues/home/prescript/revue/galip')
    assert_equals(r.description, u'Gallia Préhistoire Créée par le CNRS, la revue Gallia Préhistoire est, depuis plus d’un demi-siècle, la grande revue de l’archéologie nationale, réputée pour la rigueur de ses textes et la qualité de ses illustrations. Gallia Préhistoire publie des articles de synthèse sur les découvertes et les recherches les plus signifiantes dans le domaine de la Préhistoire en France. Son champ chronologique couvre toute la Préhistoire depuis le Paléolithique inférieur jusqu’à la fin de l’-ge du Bronze. Son champ géographique est celui de la France; cependant, Gallia Préhistoire publie aussi des études traitant des cultures limitrophes.')
    assert_equals(r.language, ('fr', 1.0))
    assert_equals(r.domain, 'www.persee.fr')
    assert_equals(r.keywords, [u'journal', u'open access'])


@with_setup(setup_function, teardown_function)
def test_parsers_ascsa():

    logger = logging.getLogger(sys._getframe().f_code.co_name)
    file_name = os.path.join(PATH_TEST_DATA, 'post-akoue.xml')
    logger.debug('\n\n\n********** FOOOOOOOOOO')
    a = AwolArticle(atom_file_name=file_name)
    parsers = AwolParsers()
    resources = parsers.parse(a)
    r = resources[0]
    assert_equals(r.title, u'ákoue News')
    assert_equals(r.url, 'http://www.ascsa.edu.gr/index.php/publications/newsletter/')
    assert_equals(r.description, u"ákoue News ákoue News The School's newsletter, ákoue, has become a new, shorter print publication as we transition an increasing number of news articles and stories to the School website. Often there will be links to additional photos or news in the web edition that we haven't room to place in the print edition. Also supplemental articles that did not make it into print will be placed on the newsletter's home page here. The last issue of ákoue had asked for subscribers to notify us of their delivery preference-print or web edition.  If you have do wish to have a print edition mailed to you, please contact us.")
    assert_equals(r.domain, 'www.ascsa.edu.gr')
    assert_equals(r.keywords, [u'ASCSA'])
    assert_equals(len(r.subordinate_resources), 0)
