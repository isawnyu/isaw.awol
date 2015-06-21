#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test code in the article module."""

import logging
import os
import sys

from nose import with_setup
from nose.tools import *

try:
    from nose.tools import assert_multi_line_equal
except ImportError:
    assert_multi_line_equal = assert_equal
else:
    assert_multi_line_equal.im_class.maxDiff = None
    
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
    assert_equals(len(plist.keys()), 4)    
    # test for known parsers
    assert_true('generic' in plist.keys())
    assert_true('www.persee.fr' in plist.keys())
    assert_true('www.ascsa.edu.gr' in plist.keys())
    assert_true('oi.uchicago.edu' in plist.keys())

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
    assert_equals(r.description, u'Il capitale culturale. Studies on the Value of Cultural Heritage. Il capitale culturale (ISSN: 2039-2362) è la rivista del Dipartimento di Beni Culturali dell’Università di Macerata con sede a Fermo, che si avvale di molteplici competenze disciplinari (archeologia, archivistica, diritto, economia aziendale, informatica, museologia, restauro, storia, storia dell’arte) unite dal comune obiettivo della implementazione di attività di studio, ricerca e progettazione per la valorizzazione del patrimonio culturale.')
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
    assert_equals(r.description, u'Archaeonautica. eISSN - 2117-6973. Archaeonautica est une collection créée en 1977 par le CNRS et le Ministère de la Culture à l’initiative de Bernard Liou. Publiée par CNRS Edition, le secrétariat de rédaction de la collection est assuré par le Centre Camille Jullian. Le but de la collection est la publication des recherches d’archéologie sous-marines ou, plus généralement, subaquatique, de la Préhistoire à l’époque moderne. Elle est aussi destinée à accueillir des études d’archéologie maritime et d’archéologie navale, d’histoire maritime et d’histoire économique.')
    assert_equals(r.language, ('fr', 1.0))
    assert_equals(r.domain, 'www.persee.fr')
    assert_equals(sorted(r.keywords), sorted([u'France', u'journal', u'open access', u'archaeology', u'nautical archaeology']))
    assert_equals(r.identifiers, {'issn': {'electronic': [u'2117-6973']}})
    assert_is_none(r.is_part_of)
    assert_equals(len(r.provenance), 2)
    assert_equals(r.provenance[0]['term'], 'http://purl.org/spar/cito/citesAsDataSource')
    assert_equals(r.provenance[1]['term'], 'http://purl.org/spar/cito/citesAsMetadataDocument')
    #assert_equals(len(r.related_resources), 0)
    #assert_equals(len(r.subordinate_resources), 14)
    #assert_equals(len(r.subordinate_resources[0].provenance), 2)
    #assert_equals(r.subordinate_resources[0].provenance[0]['term'], 'http://purl.org/spar/cito/citesAsDataSource')
    del resources

    file_name = os.path.join(PATH_TEST_DATA, 'post-gallia-prehistoire.xml')
    a = AwolArticle(atom_file_name=file_name)
    parsers = AwolParsers()
    resources = parsers.parse(a)
    r = resources[0]
    assert_equals(r.title, u'Gallia Préhistoire')
    assert_equals(r.url, 'http://www.persee.fr/web/revues/home/prescript/revue/galip')
    assert_equals(r.description, u'Gallia Préhistoire. Créée par le CNRS, la revue Gallia Préhistoire est, depuis plus d’un demi-siècle, la grande revue de l’archéologie nationale, réputée pour la rigueur de ses textes et la qualité de ses illustrations. Gallia Préhistoire publie des articles de synthèse sur les découvertes et les recherches les plus signifiantes dans le domaine de la Préhistoire en France. Son champ chronologique couvre toute la Préhistoire depuis le Paléolithique inférieur jusqu’à la fin de l’-ge du Bronze. Son champ géographique est celui de la France; cependant, Gallia Préhistoire publie aussi des études traitant des cultures limitrophes.')
    assert_equals(r.language, ('fr', 1.0))
    assert_equals(r.domain, 'www.persee.fr')
    assert_equals(r.keywords, [u'journal', u'open access'])


@with_setup(setup_function, teardown_function)
def test_parsers_ascsa():

    file_name = os.path.join(PATH_TEST_DATA, 'post-akoue.xml')
    a = AwolArticle(atom_file_name=file_name)
    parsers = AwolParsers()
    resources = parsers.parse(a)
    r = resources[0]
    assert_equals(r.title, u'ákoue News')
    assert_equals(r.url, 'http://www.ascsa.edu.gr/index.php/publications/newsletter/')
    assert_equals(r.description, u"\xe1koue News. The School's newsletter, \xe1koue, has become a new, shorter print publication as we transition an increasing number of news articles and stories to the School website. Often there will be links to additional photos or news in the web edition that we haven't room to place in the print edition. Also supplemental articles that did not make it into print will be placed on the newsletter's home page here. The last issue of \xe1koue had asked for subscribers to notify us of their delivery preference-print or web edition. If you have do wish to have a print edition mailed to you, please contact us.")
    assert_equals(r.domain, 'www.ascsa.edu.gr')
    assert_equals(r.keywords, [u'ASCSA'])
    #assert_equals(len(r.subordinate_resources), 0)

@with_setup(setup_function, teardown_function)
def test_parsers_oi():

    file_name = os.path.join(PATH_TEST_DATA, 'post-grammatical-case.xml')
    a = AwolArticle(atom_file_name=file_name)
    parsers = AwolParsers()
    resources = parsers.parse(a)
    r = resources[0]
    assert_equals(r.title, u'Grammatical Case in the Languages of the Middle East and Europe')
    assert_equals(r.url, 'http://oi.uchicago.edu/pdf/saoc64.pdf')
    assert_equals(r.description, u"Announced today: SAOC 64. Grammatical Case in the Languages of the Middle East and EuropeActs of the International Colloquium Variations, concurrence et evolution des cas dans divers domaines linguistiques, Paris, 2-4 April 2007 Edited by Michèle Fruyt, Michel Mazoyer, and Dennis Pardee Purchase Book Download PDF Terms of Use Studies in Ancient Oriental Civilization (SAOC) volume 64 contains twenty-eight studies of various aspects of the case systems of Sumerian, Hurrian, Elamite, Eblaite, Ugaritic, Old Aramaic, Biblical Hebrew, Indo-European, the languages of the Bisitun inscription, Hittite, Armenian, Sabellic, Gothic, Latin, Icelandic, Slavic, Russian, Ouralien, Tokharian, and Etruscan. The volume concludes with a paper on future directions. Studies in Ancient Oriental Civilization 64 Chicago: The Oriental Institute, 2011 ISBN-13: 978-1-885923-84-4 ISBN-10: 1-885923-84-8 Pp. viii+ 420; 25 figures, 3 tables $45.00 Table of Contents Cas et analyse en morphèmes? Christian Touratier The Conjugation Prefixes, the Dative Case, and the Empathy Hierarchy in Sumerian. Christopher Woods Agent, Subject, Patient, and Beneficiary: Grammatical Roles in Hurrian. Dennis R. M. Campbell Des cas en élamite? Florence Malbran-Labat Évolution des cas dans le sémitique archaïque: la contribution de l’éblaïte. Pelio Fronzaroli Some Case Problems in Ugaritic. Robert Hawley Early Canaanite and Old Aramaic Case in the Light of Language Typology. Rebecca Hasselbach Vestiges du système casuel entre le nom et le pronom suffixe en hébreu biblique. Dennis Pardee Genèse et évolution du système casuel indo-européen: questions et hypothèses. Jean Haudry Allative in Indo-European. Folke Josephson Anomalies grammaticales à Bisotun. É. Pirart The Problem of the Ergative Case in Hittite. Craig Melchert A propos de l’opposition entre le statique et le dynamique en hittite. Michel Mazoyer Sur l’évolution du locatif en arménien. Matthias Fritz Énigmes autour du datif et de l’instrumental. Françoise Bader Les marques casuelles dans les documents paléo‑sabelliques et la morphologie du génitif pluriel sud-picénien. Vincent Martzloff Formation et variations dans les systèmes flexionnels des langues sabelliques: entre synchronie et diachronie. Paolo Poccetti Cas et évolution linguistique en latin. Michèle Fruyt La casualité latine en variation diastratique: du parler populaire à la diction poétique. Carole Fry Le flottement entre les cas en latin tardif. Gerd V. M. Haverling Case Marking of Core Arguments and Alignment in Late Latin. Michela Cennamo Cas grammaticaux et cas locaux en gotique: les modèles casuels en gotique. André Rousseau Remarques sur le datif en islandais moderne. Patrick Guelpa Mécanismes de réaffectation désinentielle et hiérarchie des oppositions casuelles en slave. Claire Le Feuvre Pourquoi deux génitifs et deux locatifs en russe pour certains substantifs? Etat actuel des paradigmes et aspects diachroniques. Sergueï Sakhno Regards sur les cas dans les langues ouraliennes. Jean Perrot† Sur l’histoire des cas en tokharien. Georges-Jean Pinault Accord sur le désaccord: quelques réflexions sur les rapports entre morphèmes casuels et adpositions en étrusque. G. van Heems Synthèse: The Dynamics of Case — Recapitulation and Future Directions. Gene Gragg")
    assert_equals(r.domain, 'oi.uchicago.edu')
    assert_equals(r.keywords, [u'Europe', u'book', u'Middle East', u'language', u'Oriental Institute'])
    
@with_setup(setup_function, teardown_function)
def test_parsers_oi():

    file_name = os.path.join(PATH_TEST_DATA, 'post-egyptian-antiquity.xml')
    a = AwolArticle(atom_file_name=file_name)
    parsers = AwolParsers()
    resources = parsers.parse(a)
    r = resources[0]
    assert_equals(r.description, u"A Call to Protect Egyptian Antiquities, Cultural Heritage and Tourism Economy. We, the undersigned, strongly urge immediate action to protect Egyptian antiquities, important sites, and cultural heritage. In so doing, significant archaeological artifacts and irreplaceable historic objects will be preserved. Importantly, such protection will help the Egyptian economy in the wake of political revolution. Such an initiative will also help stem illicit international crime organizations that have links to money laundering, human trafficking and the drug trade. Whereas, Egyptian antiquities and sites are among the most historically significant and important in the world, Whereas, Egypt has numerous museums and historical sites, some of which are victims of ongoing looting, including recent reports that artifacts originally from Tutankhamen\u2019s tomb have been stolen, Whereas, more than 50 ancient Egyptian artifacts have been reported stolen from the Cairo Museum alone, Whereas, UNESCO has called for international mobilization to block cultural artifacts stolen from Egypt, Whereas, the tourism industry in Egypt is closely tied to cultural expeditions, employs one in eight Egyptians, accounts for some $11 billion in revenue for the Egyptian economy, and is the one of the largest sectors of the Egyptian economy.")

@with_setup(setup_function, teardown_function)
def test_parsers_issue56():
    """Make sure we're not getting raw HTML in descriptions."""

    logger = logging.getLogger(sys._getframe().f_code.co_name)
    file_name = os.path.join(PATH_TEST_DATA, 'post-oxford-archaeology.xml')
    a = AwolArticle(atom_file_name=file_name)
    parsers = AwolParsers()
    resources = parsers.parse(a)
    r = resources[0]
    if u'div' in r.description:
        logger.debug(r.description)
        raise Exception

