#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Work with an Atom entry representing an AWOL blog post.

This module defines the following classes:

 * AwolArticle: represents key information about the entry.

"""

from importlib import import_module
import logging
import os
import pkg_resources
import regex as re
import sys

from bs4 import BeautifulSoup
import langid
import requests
import unicodecsv

from isaw.awol.article import Article
from isaw.awol.normalize_space import normalize_space
from isaw.awol.resource import Resource


PATH_CURRENT = os.path.dirname(os.path.abspath(__file__))
# Build a dictionary of format {<colon prefix>:<list of cols 2,3 and 4>}
colon_prefix_csv = pkg_resources.resource_stream('isaw.awol', 'awol_colon_prefixes.csv')
dreader = unicodecsv.DictReader(
    colon_prefix_csv,
    fieldnames = [
        'col_pre',
        'omit_post',
        'strip_title',
        'mul_res'
    ],
    delimiter = ',',
    quotechar = '"')
COLON_PREFIXES = dict()
for row in dreader:
    COLON_PREFIXES.update({
        normalize_space(row['col_pre']).lower():
            [
                row['omit_post'],
                row['strip_title'],
                row['mul_res']
            ]
    })
del dreader
DOMAINS_TO_IGNORE = [
    'draft.blogger.com'
]
DOMAINS_SECONDARY = [
    'ancientworldonline.blogspot.com'
]
LANGID_THRESHOLD = 0.95
RX_CANARY = re.compile(r'[\.,:!\"“„\;\-\s]+', re.IGNORECASE)
RX_NUMERICISH = re.compile(r'^a?n?d?\s*[\.,:!\"“„\;\-\s\d\(\)\[\]]+$', re.IGNORECASE)
RX_MATCH_DOMAIN = re.compile('^https?:\/\/([^/#]+)')
RX_IDENTIFIERS = {
    'issn': {
        'electronic': [
            re.compile(r'(electronic|e-|e‒|e–|e—|e|online|on-line|digital)([\s:]*issn[^\d]*[\dX-‒–—]{4}[-‒–—\s]?[\dX]{4})', re.IGNORECASE),
            re.compile(r'(issn[\s\(]*)(electrónico|électronique|online|on-line|digital)([^\d]*[\dX-‒–—]{4}[-‒–—\s]?[\dX]{4})', re.IGNORECASE),
            re.compile(r'(issn[^\d]*[\dX-‒–—]{4}[-‒–—\s]?[\dX]{4}[\s\(]*)(electrónico|électronique|online|on-line|digital)', re.IGNORECASE),
        ],
        'generic': [
            re.compile(r'(issn[^\d]*[\dX-‒–—]{4}[-‒–—\s]?[\dX]{4})', re.IGNORECASE),
            re.compile(r'(issn[^\d]*[\dX-‒–—]{8-9})', re.IGNORECASE)
        ],
        'extract': {
            'precise': re.compile(r'^[^\d]*([\dX]{4}[-‒–—\s]?[\dX]{4}).*$', re.IGNORECASE),
            'fallback': re.compile(r'^[^\d]*([\dX-‒–—\s]+).*$', re.IGNORECASE)
        }
    },
    'isbn': {
        'electronic': [
            re.compile(r'(electronic|e-|e‒|e–|e—|online|on-line|digital)([\s:]*isbn[^\d]*[\dX-‒–—]+)', re.IGNORECASE),
            re.compile(r'(isbn[\s\(]*)(electrónico|électronique|online|on-line|digital)([^\d]*[\dX-‒–—]+)', re.IGNORECASE),
            re.compile(r'(isbn[^\d]*[\dX-‒–—]+[\s\(]*)(electrónico|électronique|online|on-line|digital)', re.IGNORECASE),
        ],
        'generic': [
            re.compile(r'isbn[^\d]*[\dX-‒–—]+', re.IGNORECASE),
        ],
        'extract': {
            'precise': re.compile(r'^[^\d]*([\dX-‒–—]+).*$', re.IGNORECASE),
        }
    }
}

title_strings_csv = pkg_resources.resource_stream('isaw.awol', 'awol_title_strings.csv')
dreader = unicodecsv.DictReader(
    title_strings_csv,
    fieldnames = [
        'titles',
        'tags'
    ],
    delimiter = ',',
    quotechar = '"')
TITLE_SUBSTRING_TAGS = dict()
for row in dreader:
    TITLE_SUBSTRING_TAGS.update({row['titles']:row['tags']})
del dreader
TITLE_SUBSTRING_TERMS = {k:v for (k,v) in TITLE_SUBSTRING_TAGS.iteritems() if ' ' not in k}
TITLE_SUBSTRING_TERMS[u'boğazköy'] = u'Boğazköy'
TITLE_SUBSTRING_PHRASES = {k:v for (k,v) in TITLE_SUBSTRING_TAGS.iteritems() if k not in TITLE_SUBSTRING_TERMS.keys()}
AGGREGATORS = [
    'www.jstor.org',
    'oi.uchicago.edu',
    'www.persee.fr',
    'dialnet.unirioja.es',
    'amar.hsclib.sunysb.edu',
    'hrcak.srce.hr',
    'www.griffith.ox.ac.uk'
]
AGGREGATOR_IGNORE = [
    'http://www.jstor.org/page/info/about/archives/collections.jsp',
    'https://oi.uchicago.edu/getinvolved/',
    'http://oi.uchicago.edu/news/'
]
POST_SELECTIVE = {
    'http://ancientworldonline.blogspot.com/2012/07/chicago-demotic-dictionary-t.html': [0,],
    'http://ancientworldonline.blogspot.com/2013/01/new-issues-of-asor-journals.html': [0,1,]
}
SUBORDINATE_FLAGS = [
    'terms of use',
    'download pdf',
    'download',
]
NO_FORCING = [
    'http://ancientworldonline.blogspot.com/2011/03/ancient-world-in-persee.html',
    'http://ancientworldonline.blogspot.com/2009/09/open-access-journals-in-ancient-studies.html',
    'http://ancientworldonline.blogspot.com/2011/05/open-access-journal-bsaa-arqueologia.html',
]
NO_SUBORDINATES = [
    'http://ancientworldonline.blogspot.com/2012/12/newly-online-from-ecole-francaise-de.html',
    'http://ancientworldonline.blogspot.com/2011/03/ancient-world-in-persee.html'
]
FORCE_AS_SUBORDINATE_AFTER = [
    'http://oi.uchicago.edu/research/library/acquisitions.html',
    'http://oi.uchicago.edu/research/pubs/ar/10-11/',
    'http://oi.uchicago.edu/research/pubs/ar/28-59/',
    'http://oi.uchicago.edu/research/pubs/catalog/as/',
    'http://oi.uchicago.edu/research/pubs/catalog/as/',
    'http://oi.uchicago.edu/research/pubs/catalog/saoc/',
    'http://www.persee.fr/web/ouvrages/home/prescript/fond/befar',
    'http://www.persee.fr/web/ouvrages/home/prescript/issue/mom_0184-1785_2011_act_45_1#',
    'https://oi.uchicago.edu/research/pubs/ar/11-20/11-12/',
    'https://oi.uchicago.edu/research/pubs/catalog/oip/',
    'oriental institute news & notes',
    'http://amar.hsclib.sunysb.edu/amar/',
    'http://www.persee.fr/web/revues/home/prescript/issue/litt_0047-4800_2001_num_122_2',
    'http://oi.uchicago.edu/research/pubs/nn/',
    'http://ancientworldonline.blogspot.com/2010/04/open-access-journal-oriental-institute.html'
]
RELATED_FLAGS = [
    'list of volumes in print',
    'membership'
]
FORCE_AS_RELATED_AFTER = [
    'http://oi.uchicago.edu/research/library/dissertation/nolan.html',
    'http://oi.uchicago.edu/research/pubs/ar/28-59',
    'https://oi.uchicago.edu/research/pubs/archeological/',
    'list of volumes in print',
]
SUPPRESS_RESOURCE = [
    'terms of use',
    'download pdf',
    'download',
    'membership',
    'here'
]


RX_DASHES = re.compile(r'[‒–—-]+')


def clean_title(raw):
    prepped = normalize_space(raw)
    chopped = prepped.split(u'.')
    if len(chopped) > 2:
        cooked = u'.'.join(tuple(chopped[:2]))
        i = 2
        while i < len(chopped) and len(cooked) < 40:
            cooked = cooked + u'.' + chopped[i]
            i = i + 1
    else:
        cooked = prepped
    junk = [
        (u'(', u')'),
        (u'[', u']'),
        (u'{', u'}'),
        (u'"', u'"'),
        (u"'", u"'"),
        (u'<', u'>'),
        (u'«', u'»'),
        (u'‘', u'’'),
        (u'‚', u'‛'),
        (u'“', u'”'),
        (u'‟', u'„'),
        (u'‹', u'›'),
        (u'〟', u'＂'),
        (u'\\'),
        (u'/'),
        (u'|'),
        (u','),
        (u';'),
        (u'-'),
        (u'.'),
        (u'_'),
    ]
    for j in junk:
        if len(j) == 2:
            cooked = cooked[1:-1] if cooked[0] == j[0] and cooked[-1] == j[1] else cooked
        else:
            cooked = cooked[1:] if cooked[0] == j[0] else cooked
            cooked = cooked[:-1] if cooked[-1] == j[0] else cooked
        if cooked[0:4] == u'and ':
            cooked = cooked[4:]
        cooked = cooked.strip()
    return cooked

class AwolArticle(Article):
    """Extracts, normalizes, and stores data from an AWOL blog post."""

    def __init__(self, atom_file_name=None, json_file_name=None):

        Article.__init__(self, atom_file_name, json_file_name)
        lt = self.title.lower()
        if lt in COLON_PREFIXES.keys():
            if COLON_PREFIXES[lt][0] == 'yes':
                return None




