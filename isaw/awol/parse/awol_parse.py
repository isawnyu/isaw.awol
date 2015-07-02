#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse HTML content for resources.

This module defines the following classes:

 * AwolParser: parse AWOL blog post content for resources
"""

from copy import copy, deepcopy
import logging
import pkg_resources
import re
import requests
import sys

from bs4 import BeautifulSoup
from bs4.element import NavigableString
import langid
from lxml import etree
import unicodecsv

from isaw.awol.clean_string import *
from isaw.awol.normalize_space import normalize_space
from isaw.awol.resource import Resource
from isaw.awol.tools import mods

DOMAINS_IGNORE = [
    'draft.blogger.com',
    'bobcat.library.nyu.edu',
    'cientworldonline.blogspot.com' # that there's a typo in a link somewhere in the blog
]
DOMAINS_SELF = [
    'ancientworldonline.blogspot.com',
]
BIBLIO_SOURCES = {
    'zenon.dainst.org': {
        'url_pattern': re.compile(u'^https?:\/\/zenon.dainst.org/Record/\d+\/?$'),
        'url_append': '/RDF',
        'type': 'application/rdf+xml',
        'namespaces' : {
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'mods': 'http://www.loc.gov/mods/v3'
        },
        'payload_xpath': '//rdf:Description[1]/mods:mods[1]',
        'payload_type': 'application/mods+xml'
    }
}
DOMAINS_BIBLIOGRAPHIC = BIBLIO_SOURCES.keys()
MODS2RESOURCES = {
    'publisher':'publishers',
    'language':'languages',
    'statement_of_responsibility':'responsibility',
    'place':'places',
    'issued_date':'issued_dates',
    'uri':'identifiers'

}
ANCHOR_TEXT_IGNORE = [
    u'contact us',
]
ANCHOR_URLS_IGNORE = [
]
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
def check_colon(title):
    if u':' in title:
        colon_prefix = title.split(u':')[0].lower()
        if colon_prefix in COLON_PREFIXES.keys() and (COLON_PREFIXES[colon_prefix])[1] == 'yes':
            return clean_string(u':'.join(title.split(u':')[1:]))
        else:
            return title
    else:
        return title
OMIT_TITLES = [
    u'administrative',
    u'administrative note'
]
def allow_by_title(title):
    if title.lower() in OMIT_TITLES:
        return False
    elif u':' in title:
        colon_prefix = title.split(u':')[0].lower()
        if colon_prefix in COLON_PREFIXES.keys() and (COLON_PREFIXES[colon_prefix])[0] == 'yes':
            return False
    return True

RX_IDENTIFIERS = {
    'issn': {
        'electronic': [
            re.compile(r'(e-|e)(issn[\s:\-]*[\dX\-]{4}[\-\s]+[\dX]{4})', re.IGNORECASE),
            re.compile(r'(electronic|online|on-line|digital|internet)([\s:]*issn[^\d]*[\dX]{4}[\-\s]+[\dX]{4})', re.IGNORECASE),
            re.compile(r'(issn[\s\(\-]*)(electrónico|électronique|online|on-line|digital|internet)([^\d]*[\dX]{4}[\-\s]+[\dX]{4})', re.IGNORECASE),
            re.compile(r'(issn[^\d]*[\dX]{4}[\-\s]+[\dX]{4}[\s\(]*)(electrónico|électronique|online|on-line|digital)', re.IGNORECASE),
        ],
        'generic': [
            re.compile(r'(issn[^\d]*[\dX]{4}[\-\s]+[\dX]{4})', re.IGNORECASE),
            re.compile(r'(issn[^\d]*[\dX\-\s]{8-11})', re.IGNORECASE)
        ],
        'extract': {
            'precise': re.compile(r'^[^\d]*([\dX]{4}[\-\s]+[\dX]{4}).*$', re.IGNORECASE),
            'fallback': re.compile(r'^[^\d]*([\dX\-\s]+).*$', re.IGNORECASE)
        }
    },
    'isbn': {
        'electronic': [
            re.compile(r'(electronic|e-|online|on-line|digital)([\s:]*isbn[^\d]*[\dX\-]+)', re.IGNORECASE),
            re.compile(r'(isbn[\s\(]*)(electrónico|électronique|online|on-line|digital)([^\d]*[\dX\-]+)', re.IGNORECASE),
            re.compile(r'(isbn[^\d]*[\dX\-]+[\s\(]*)(electrónico|électronique|online|on-line|digital)', re.IGNORECASE),
        ],
        'generic': [
            re.compile(r'isbn[^\d]*[\dX\-]+', re.IGNORECASE),
        ],
        'extract': {
            'precise': re.compile(r'^[^\d]*([\dX\-]+).*$', re.IGNORECASE),
        }
    }
}

RX_AUTHORS = [
    re.compile(r'(compiled by |assembled by |created by |written by |authors?):?\s*([^\.]+)', re.IGNORECASE)
]
RX_EDITORS = [
    re.compile(r'(edited by |editors?):?\s*([^\.]+)', re.IGNORECASE)
]

LANGID_THRESHOLD = 0.98
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
TITLE_SUBSTRING_PHRASES = {k:v for (k,v) in TITLE_SUBSTRING_TAGS.iteritems() if k not in TITLE_SUBSTRING_TERMS.keys()}
RX_ANALYTIC_TITLES = [
    # volume, issue, year (e.g. Bd. 52, Nr. 1 (2005))
    {
        'rx': re.compile(r'^Bd\.\s+(\d+),?\s+Nr\.\s+(\d+)\s+\(?(\d{4})\)?$', re.IGNORECASE),
        'volume': 1,
        'issue': 2,
        'year': 3
    },
    # year, blah blah blah, then volume (e.g. u'1888 Mitteilungen des Deutschen Arch\xe4ologischen Instituts / R\xf6mische Abteilung Band 3')
    {
        'rx': re.compile(r'^(\d{4})[^\d]+Band (\d+)$', re.IGNORECASE),
        'volume': 2,
        'year': 1
    },
    # year, then volume
    {
        'rx': re.compile(r'^[^\d]*(\d{4})\W*([\d\-]+)[^\d]*$', re.IGNORECASE),
        'volume': 2,
        'year': 1
    },
    # volume, then year
    {
        'rx': re.compile(r'^[^\d]*([\d\-]{1-4})\W*(\d{4})[^\d]*$', re.IGNORECASE),
        'volume': 1,
        'year': 2
    },
    # volume only
    {
        'rx': re.compile(r'^[^\d]*([\d\-]+)[^\d]*$', re.IGNORECASE),
        'volume': 1,
    },


]
RX_PUNCT_FIX = re.compile(r'\s+([\.,:;]{1})')
RX_PUNCT_DEDUPE = re.compile(r'([\.,:;]{1})([\.,:;]{1})')

def domain_from_url(url):
    return url.replace('http://', '').replace('https://', '').split('/')[0]

class AwolBaseParser:
    """Superclass: Extract data from an AWOL blog post."""

    # constructor
    def __init__(self):
        self.reset()

    # public methods
    def get_domains(self, content_soup=None):
        """Determine domains of resources linked in content."""

        #logger = logging.getLogger(sys._getframe().f_code.co_name)

        if content_soup is not None:
            self.reset(content_soup)

        c = self.content
        if c['domains'] is None:
            soup = c['soup']
            anchors = [a for a in soup.find_all('a')]
            urls = [a.get('href') for a in anchors if a.get('href') is not None]
            urls = list(set(urls))
            domains = [domain_from_url(url) for url in urls]
            domains = list(set(domains))
            #logger.debug(u'domain set: \n   {0}'.format(u'\n   '.join(domains)))
            domains = [domain for domain in domains if domain not in self.skip_domains]
            #logger.debug(u'domain after skips: \n   {0}'.format(u'\n   '.join(domains)))
            if len(domains) > 1:
                domains = [domain for domain in domains if domain not in self.bibliographic_domains]
            c['domains'] = domains
        #logger.debug(u'get_domains got: \n   {0}'.format(u'\n   '.join(c['domains'])))
        return c['domains']

    def parse(self, article):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        logger.debug(u'parsing {0}'.format(article.url))
        self.reset(article.soup)
        resources = self._get_resources(article)
        return resources

    def reset(self, content_soup=None):
        #logger = logging.getLogger(sys._getframe().f_code.co_name)
        #logger.debug("******* reset!")
        self.content = {}
        c = self.content
        if content_soup is not None:
            c['soup'] = content_soup
        c['anchors'] = None
        c['domains'] = None
        self.skip_domains = copy(DOMAINS_IGNORE) + copy(DOMAINS_SELF)
        self.bibliographic_domains = copy(DOMAINS_BIBLIOGRAPHIC)
        self.skip_text = copy(ANCHOR_TEXT_IGNORE)
        self.skip_urls = copy(ANCHOR_URLS_IGNORE)

    # private methods
    def _consider_anchor(self, a):
        #logger = logging.getLogger(sys._getframe().f_code.co_name)
        #logger.debug('skip urls: {0}'.format(', '.join(self.skip_urls)))
        url = a.get('href')
        if url is not None:
            #logger.debug('filtering: {0}'.format(url))
            text = a.get_text()
            if len(text) > 0:
                #logger.debug(u'text of a is: {0}'.format(text))
                domain = domain_from_url(url)
                #logger.debug('domain is: {0}'.format(domain))
                if (domain in self.skip_domains
                or url in self.skip_urls
                or text in self.skip_text):
                    #logger.debug('skipping!')
                    pass
                else:
                    #logger.debug('keeping!')
                    return True
            else:
                #logger.debug('omitting: no text')
                pass
        else:
            #logger.debug('omitting: no url')
            pass
        return False

    def _filter_anchors(self, anchors):
        filtered = [a for a in anchors if self._consider_anchor(a)]
        return filtered

    def _get_anchor_ancestor_for_title(self, anchor):
        a = anchor
        url = a.get('href')
        parent = a.find_parent('li')
        if parent is not None:
            anchor_ancestor = parent
        else:
            previous_parent = a
            parent = a.parent
            while parent is not None and len([a for a in parent.find_all('a') if a.get('href') != url]) > 0:
                prevous_parent = parent
                parent = parent.parent
            #parents = a.find_parents('span')
            #i = 0
            #while i < len(parents):
            #    if len(parents[i].find_all('a')) > 1:
            #        break
            #    i = i+1
            #i = i - 1
            #if i > -1:
            #    anchor_ancestor = parents[i]
            #else:
            #    parents = a.find_parents('p')
            #    if len(parents) > 0 and len(parents[0].find_all('a')) == 1:
            #        anchor_ancestor = parents[0]
            #    else:
            #        anchor_ancestor = a
            if previous_parent.name == 'body':
                anchor_ancestor = anchor
            else:
                anchor_ancestor = previous_parent
        return anchor_ancestor

    def _get_anchors(self):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        c = self.content
        if c['anchors'] is not None:
            #logger.debug('already have anchors')
            return c['anchors']
        soup = c['soup']
        #logger.debug(u'finding anchors in: {0}'.format(unicode(soup))) 
        raw_anchors = [a for a in soup.find_all('a') if a.find_previous('a', href=a.get('href')) is None]
        #logger.debug('raw anchors: {0}'.format(', '.join([a.get('href') for a in raw_anchors])))
        anchors = self._filter_anchors(raw_anchors)
        c['anchors'] = anchors
        return anchors

    def _get_description(self, context=None):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        if context is None:
            c = self.content
            soup = c['soup']
            first_node = soup.body.contents[0]
            #logger.debug(u'context:\n\n{0}\n\n'.format(soup.prettify()))
            skip_first_anchor = True
        else:
            first_node = context
            #logger.debug('special context!!')
            skip_first_anchor = False

        stop_tags = ['a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'ol', 'li', 'table']

        def digdigdig(this_node, first_node, stop_tags, skip_first_anchor, previous_urls):
            logger = logging.getLogger(sys._getframe().f_code.co_name)

            node_type = type(this_node)
            node_name = this_node.name
            try:
                node_url = this_node.get('href')
            except AttributeError:
                node_url = ''
            #logger.debug('dig (nodetype: {nodetype}, name: {name}, url: {url})'.format(
            #    nodetype=node_type, name=node_name, url=node_url))
            results = []

            if (
                this_node != first_node 
                and node_name in stop_tags 
                and (
                    node_name != 'a'
                    or (
                        'a' in stop_tags 
                        and node_name == 'a'
                        and (
                                (
                                skip_first_anchor
                                and len(previous_urls) == 0                                    
                                )
                            or (
                                not(skip_first_anchor)
                                and len(previous_urls) > 0
                                and node_url != previous_urls[-1]
                                )
                            )
                        )
                    )
                ):
                if node_name == 'a':
                    previous_urls.append(node_url)
                return (True, results)

            if node_name == 'a':
                previous_urls.append(this_node.get('href'))
            if node_name == 'br':
                results.append(u'. ')
            if node_type == NavigableString:
                results.append(purify_html(unicode(this_node)))
            else:
                try:
                    descendants = this_node.descendants
                except AttributeError:
                    pass
                else:
                    if descendants is not None:
                        for child in this_node.children:
                            stop, child_results = digdigdig(child, first_node, stop_tags, skip_first_anchor, previous_urls)
                            results.extend(child_results)
                            if stop:
                                return (stop, results)
            return (False, results)

        previous_urls = []
        stop, desc_lines = digdigdig(first_node, first_node, stop_tags, False, previous_urls)
        node = first_node.next_sibling
        while not stop and node is not None and node.name not in stop_tags:
            stop, results = digdigdig(node, first_node, stop_tags, False, previous_urls)
            desc_lines.extend(results)
            node = node.next_sibling

        if len(desc_lines) == 0:
            previous_urls = []
            stop, desc_lines = digdigdig(first_node, first_node, stop_tags, True, previous_urls)
            node = first_node.next_sibling
            while not stop and node is not None and node.name not in stop_tags:
                stop, results = digdigdig(node, first_node, stop_tags, True, previous_urls)
                desc_lines.extend(results)
                node = node.next_sibling

        if len(desc_lines) == 0:
            desc_text = None
        else:
            desc_text = deduplicate_lines(u'\n'.join(desc_lines))
            desc_text = u''.join(desc_lines)
            if len(desc_text) == 0:
                desc_text = None
            else:
                desc_text = desc_text.replace(u'%IMAGEREPLACED%', u'').strip()
                desc_text = RX_PUNCT_FIX.sub(r'\1', desc_text)
                desc_text = deduplicate_sentences(desc_text)
                desc_text = RX_PUNCT_DEDUPE.sub(r'\1', desc_text)
                desc_text = normalize_space(desc_text)
                if len(desc_text) == 0:
                    desc_text = None
                elif desc_text[-1] != u'.':
                    desc_text += u'.'

        return desc_text   

    def _get_language(self, *args):
        chunks = [chunk for chunk in args if chunk is not None]
        s = u' '.join((tuple(chunks)))
        s = normalize_space(s)
        if s != u'':
            language = langid.classify(s)
            if language[1] >= LANGID_THRESHOLD:
                return language[0]
        return None

    def _get_next_valid_url(self, anchor):
        a = anchor
        while a is not None:
            try:
                url = a.get('href')
            except AttributeError:
                url = None
            else:
                domain = domain_from_url(url)
                if domain not in self.skip_domains:
                    break
            a = a.find_next(a)
        if a is None:
            raise ValueError(u'could not find valid self-or-subsequent resource anchor')
        return (anchor, a, url, domain)

    def _get_primary_anchor(self):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        anchors = self._get_anchors()
        #logger.debug("anchors before primary: {0}".format(', '.join([a.get('href') for a in anchors])))
        try:
            a = self._get_anchors()[0]
        except IndexError:
            msg = 'failed to parse primary anchor from {0}'.format(self.content['soup'])
            raise IndexError(msg)
        #logger.debug('primary anchor is {0}'.format(a.get('href')))
        return a        

    def _get_primary_resource(self, article):
        logger = logging.getLogger(sys._getframe().f_code.co_name)

        #logger.debug('getting primary resource from {0}'.format(article.id))
        # title
        a = self._get_primary_anchor()
        a_title = clean_string(a.get_text())  
        #logger.debug(u'found a_title: "{0}"'.format(a_title))
        titles = self._reconcile_titles(a_title, article.title)
        try:
            title = titles[0]
        except IndexError:
            msg = 'could not extract resource title'
            raise IndexError(msg)
        try:
            title_extended = titles[1]
        except IndexError:
            title_extended = None

        # description
        desc_text = self._get_description()
        if desc_text is None:
            logger.warning(article.soup.prettify())
            raise Exception


        # parse authors
        authors = self._parse_authors(desc_text)

        # parse identifiers
        identifiers = self._parse_identifiers(desc_text)

        # language
        language = self._get_language(title, title_extended, desc_text)

        # determine keywords
        keywords = self._parse_keywords(article.title, titles[-1], article.categories)

        # create and populate the resource object
        params = {
            'url': a.get('href'),
            'domain': a.get('href').replace('http://', '').replace('https://', '').split('/')[0],
            'title': title
        }
        if desc_text is not None:
            params['description'] = desc_text
        if len(authors) > 0:
            params['authors'] = authors
        if len(identifiers.keys()) > 0:
            params['identifiers'] = identifiers
        if title_extended is not None:
            params['title_extended'] = title_extended
        if language is not None:
            params['languages'] = language
        if len(keywords) > 0:
            params['keywords'] = keywords
        resource = self._make_resource(**params)

        # provenance
        self._set_provenance(resource, article)

        #logger.debug(u'returning resource: "{0}"'.format(unicode(resource)))
        return resource

    def _get_related_resources(self):
        resources = []
        anchors = self._get_anchors()[1:]
        anchors = [a for a in anchors if domain_from_url(a.get('href')) in DOMAINS_SELF]
        for a in anchors:
            # title
            title_context = self._get_anchor_ancestor_for_title(a)
            title = clean_string(title_context.get_text())

            # description
            #html = u' {0}\n'.format(unicode(title_context))
            next_node = title_context.next_element
            #while True:
            #    html = html + u' {0}\n'.format(unicode(next_node))
            #    if next_node.name in ['blockquote', 'hr', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ul', 'p', 'div', 'ol']:
            #        break
            #    next_node = next_node.next_element
            #    if next_node is None:
            #        break
            #html = u'<div>\n' + html + u'\n</div>'
            #this_soup = BeautifulSoup(html)
            #desc_text = self._get_description(this_soup)
            desc_text = self._get_description(next_node)

            # parse identifiers
            identifiers = self._parse_identifiers(desc_text)

            # language
            language = self._get_language(title, desc_text)

            # determine keywords
            keywords = self._parse_keywords(resource_title=title, resource_text=desc_text)

            # create and populate the resource object
            r = Resource()
            params = {
                'url': a.get('href'),
                'domain': a.get('href').replace('http://', '').replace('https://', '').split('/')[0],
                'title': title
            }
            if desc_text is not None:
                params['description'] = desc_text
            if len(identifiers.keys()) > 0:
                params['identifiers'] = identifiers
            if language is not None:
                params['languages'] = language
            if len(keywords) > 0:
                params['keywords'] = keywords
            resource = self._make_resource(**params)
            resources.append(resource)
        return resources

    def _get_resources(self, article):
        logger = logging.getLogger(sys._getframe().f_code.co_name)

        logger.debug(u'getting resources from {0}: {1}'.format(article.id, article.title))
        if allow_by_title(article.title):
            logger.debug(u'allowed by title')
            primary_resource = self._get_primary_resource(article)
            parent = primary_resource.package()
            if len(primary_resource.identifiers.keys()) > 0:
                try:
                    parent['issn'] = primary_resource.identifiers['issn']['electronic'][0]
                except KeyError:
                    try:
                        parent['issn'] = primary_resource.identifiers['issn']['generic'][0]
                    except KeyError:
                        try:
                            parent['isbn'] = primary_resource.identifiers['isbn'][0]
                        except KeyError:
                            pass           

            subs = self._get_subordinate_resources(article, primary_resource.package())                 
            for sr in subs:
                sr.is_part_of = parent
                primary_resource.subordinate_resources.append(sr.package())

            rels = self._get_related_resources()
            for rr in rels:
                primary_resource.related_resources(append(rr.package()))

            return [primary_resource,] + subs + rels
        else:
            logger.warning(u"omitted by title: {0}".format(article.title))
            return None

    def _get_resource_from_article(self, article, anchor, context=None):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        # titles
        anchor_title = clean_string(anchor.get_text())
        titles = self._reconcile_titles(anchor_title, article.title)
        try:
            title = titles[0]
        except IndexError:
            msg = 'could not extract resource title'
            raise IndexError(msg)
        try:
            title_extended = titles[1]
        except IndexError:
            title_extended = None

        # description
        desc_text = self._get_description(context)
        if desc_text is None:
            logger.warning(article.soup.prettify())
            raise Exception('failed to parse description')

        # parse authors
        authors = self._parse_authors(desc_text)

        # parse identifiers
        identifiers = self._parse_identifiers(desc_text)
        #logger.debug(u'identifiers: {0}'.format(repr(identifiers)))

        # language
        language = self._get_language(title, title_extended, desc_text)

        # determine keywords
        keywords = self._parse_keywords(article.title, titles[-1], article.categories)

        # create and populate the resource object
        params = {
            'url': anchor.get('href'),
            'domain': domain_from_url(anchor.get('href')),
            'title': title
        }
        if desc_text is not None:
            params['description'] = desc_text
        if len(identifiers.keys()) > 0:
            params['identifiers'] = identifiers
        if len(authors) > 0:
            params['authors'] = authors            
        if title_extended is not None:
            params['title_extended'] = title_extended
        if language is not None:
            params['languages'] = language
        if len(keywords) > 0:
            params['keywords'] = keywords
        resource = self._make_resource(**params)

        # provenance
        self._set_provenance(resource, article)

        #logger.debug(u'returning resource: "{0}"'.format(unicode(resource)))
        return resource        

    def _get_resource_from_external_biblio(self, url):
        """Attempt to get third-party structured bibliographic data."""

        logger = logging.getLogger(sys._getframe().f_code.co_name)
        domain = domain_from_url(url)

        try:
            biblio_howto = BIBLIO_SOURCES[domain]
        except KeyError:
            msg = u'parsing structured bibliographic data from {0} is not supported.'.format(domain)
            raise NotImplementedError(msg)
        else:
            m = biblio_howto['url_pattern'].match(url)
            if m:
                biblio_url = url + biblio_howto['url_append']
                biblio_req = requests.get(biblio_url)
                if biblio_req.status_code == 200:
                    actual_type = biblio_req.headers['content-type']
                    if actual_type != biblio_howto['type']:
                        raise IOError('got {actualtype} from {biblurl} when '
                            + '{soughttype} was expected'.format(
                                actualtype=actual_type,
                                biblurl=biblio_url,
                                soughttype=biblio_howto['type']))
                    elif actual_type == 'application/rdf+xml':
                        root = etree.fromstring(biblio_req.content)
                        payload_element = root.xpath(
                            biblio_howto['payload_xpath'], 
                            namespaces=biblio_howto['namespaces'])[0]
                        payload = etree.tostring(payload_element, encoding='unicode')
                    else:
                        raise IOError(u'parsing content of type {actualtype} '
                            + 'is not supported'.format(
                                actualtype=actual_type))
                    payload_type = biblio_howto['payload_type']
                    if payload_type == 'application/mods+xml':
                        biblio_data = mods.extract(payload)
                    else:
                        raise NotImplementedError(u'parsing payload of type {payloadtype} '
                            + 'is not supported'.format(
                                payloadtype=payload_type))
                    logger.info(u'successfully parsed bibliographic data from ' +
                        '{bibliourl} about {title}'.format(
                            bibliourl=biblio_url,
                            title=biblio_data['title'][0]))
                    params = {}
                    for k in [k for k in biblio_data.keys() if k not in ['record_change_date', 'record_creation_date', 'name']]:
                        if k == 'uri':
                            value = (k, biblio_data[k])
                        elif k == 'language':
                            value = [lang[0] for lang in biblio_data[k]]
                        elif k == 'url':
                            value = biblio_data[k][0]
                            if len(biblio_data[k]) > 1:
                                raise Exception
                        else:
                            value = biblio_data[k]
                        try:
                            rk = MODS2RESOURCES[k]
                        except KeyError:
                            rk = k
                        params[rk] = value
                    params['domain'] = domain_from_url(biblio_data['url'][0])
                    top_resource = self._make_resource(**params)
                    try:
                        updated = biblio_data['record_change_date'][0]
                    except KeyError:
                        updated = biblio_data['record_creation_date'][0]
                    resource_fields = sorted([k for k in params.keys() if '_' != k[0]])
                    top_resource.set_provenance(biblio_url, 'citesAsDataSource', updated, resource_fields)
                    if domain == 'zenon.dainst.org':
                        top_resource.zenon_id = url.split(u'/')[-1]
                else:
                    raise IOError("unsuccessfull attempt (status code {0}) " +
                        "to get bibliograhic data from {1}".format(
                            biblio_req.status_code, biblio_url))
            return top_resource
    
    def _get_subordinate_resources(self, article, parent_package, start_anchor=None):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        resources = []
        anchors = self._get_anchors()
        index = 0
        if start_anchor is not None:
            for i,a in enumerate(anchors):
                if a == start_anchor:
                    index = i
                    break
            anchors = [a for a in anchors[index:]]

        parent_domain = domain_from_url(parent_package['url'])
        anchors = [a for a in anchors if parent_domain in a.get('href')]
        #logger.debug(u'anchors: {0}'.format(repr([a.get('href') for a in anchors])))

        for a in anchors:
            #logger.debug(u'subordinate anchor: {0}'.format(a.get('href')))
            # title
            title_context = self._get_anchor_ancestor_for_title(a)
            #tc_type = type(title_context)
            #tc_name = title_context.name
            #tc_code = title_context.prettify()
            #logger.debug(u'title_context (type: {tc_type}, name: {tc_name})'.format(tc_type=tc_type, tc_name=tc_name))
            #logger.debug(tc_code)
            title = clean_string(title_context.get_text(u' '))

            # try to extract volume and year
            try:
                volume, issue, year = self._grok_analytic_title(title)
            except TypeError:
                volume = year = issue = None
            if volume is not None and year is None and issue is not None:
                # sometimes more than one volume falls in a single list item b/c same year or parts
                try:
                    parent_li = a.find_parents('li')[0]
                except:
                    pass
                else:
                    try:
                        raw = parent_li.get_text().strip()[0:4]
                    except IndexError:
                        pass
                    else:
                        try:
                            cooked = str(int(raw))
                        except ValueError:
                            pass
                        else:
                            if cooked == raw:
                                year = cooked

            # description
            next_node = title_context.next_sibling
            desc_text = self._get_description(next_node)

            # parse identifiers
            identifiers = self._parse_identifiers(desc_text)

            # language
            language = self._get_language(title, desc_text)

            # determine keywords
            keywords = self._parse_keywords(resource_title=title, resource_text=desc_text)

            # create and populate the resource object
            params = {
                'url': a.get('href'),
                'domain': a.get('href').replace('http://', '').replace('https://', '').split('/')[0],
                'title': title,
                'is_part_of': parent_package
            }
            if desc_text is not None:
                params['description'] = desc_text
            if len(identifiers.keys()) > 0:
                params['identifiers'] = identifiers
            if language is not None:
                params['languages'] = language
            if len(keywords) > 0:
                params['keywords'] = keywords
            if volume is not None:
                params['volume'] = volume
            if year is not None:
                params['year'] = year
            if issue is not None:
                params['issue'] = issue
            resource = self._make_resource(**params)

            self._set_provenance(resource, article)

            resources.append(resource)
        return resources

    def _get_unique_urls(self):
        c = self.content
        if c['unique_urls'] is not None:
            return c['unique_urls']
        else:
            anchors = self._get_anchors()
        urls = [a.get('href') for a in anchors if a.get('href') is not None]
        unique_urls = list(set(urls))
        c['unique_urls'] = unique_urls
        return unique_urls

    def _grok_analytic_title(self, title):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        for g in RX_ANALYTIC_TITLES:
            m = g['rx'].match(title)
            if m is not None:
                break
        if m is not None:
            try:
                volume = m.group(g['volume'])
            except KeyError:
                volume = None
            try:
                issue = m.group(g['issue'])
            except KeyError:
                issue = None
            try:
                year = m.group(g['year'])
            except KeyError:
                year = None
            return (volume, issue, year)            

    # keyword methods
    def _mine_keywords(self, *args):
        tags = []
        for s in args:
            if s is not None:
                lower_s = s.lower()
                # mine for terms (i.e., single-word keys)
                lower_list = list(set(lower_s.split()))
                for k in TITLE_SUBSTRING_TERMS.keys():
                    if k in lower_list:
                        tag = TITLE_SUBSTRING_TERMS[k]
                        tags.append(tag)
                if u'open' in lower_list and u'access' in lower_list:
                    if u'partial' in lower_list:
                        if u'partial open access' in lower_s:
                            tags.append(u'mixed access')
                    else:
                        if u'open access' in lower_s:
                            tags.append(u'open access')
                if 'series' in lower_list and 'lecture' not in lower_list:
                    tags.append(u'series')
                # mine for phrases
                for k in TITLE_SUBSTRING_PHRASES.keys():
                    if k in lower_s:
                        tag = TITLE_SUBSTRING_PHRASES[k]
                        tags.append(tag)  
        return tags

    def _parse_keywords(self, post_title=None, resource_title=None, post_categories=[], resource_text=None):
        """Infer and normalize resource tags."""

        logger = logging.getLogger(sys._getframe().f_code.co_name)

        # mine keywords from content
        tags = self._mine_keywords(post_title, resource_title)

        # convert post categories to tags
        for c in post_categories:    
            tag = c['term'].lower()
            if 'kind#post' not in tag:
                if tag in TITLE_SUBSTRING_TAGS.keys():
                    tag = TITLE_SUBSTRING_TAGS[tag]
                else:
                    logger.error(u'unexpected category tag "{0}" in post with title "{1}"'.format(c['term'], post_title))
                    raise Exception
                tags.append(tag)
        return self._clean_keywords(tags)

    def _clean_keywords(self, raw_tags):
        tags = list(set(raw_tags))
        keywords = []
        for tag in tags:
            if tag == u'':
                pass
            elif u',' in tag:
                keywords.extend(tag.split(u','))
            else:
                keywords.append(tag)
        keywords = sorted([normalize_space(kw) for kw in list(set(keywords))], key=lambda s: s.lower())
        for tag in keywords:
            if tag == tag.upper():
                pass
            elif tag.lower() in TITLE_SUBSTRING_TAGS.keys():
                pass
            elif tag != tag.lower():
                print tag
                raise Exception
        return list(set(keywords))

    def _make_resource(self, **kwargs):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        r = Resource()

        for k,v in kwargs.items():
            #logger.debug(u'_make_resource_processing {0}={1}'.format(k, v))
            if v is not None:

                if type(v) == list:
                    value = v
                elif type(v) in [unicode, str]:
                    if k == 'url':
                        value = v
                    else:
                        value = [v, ]
                elif type(v) == tuple:
                    value = v
                elif type(v) == dict:
                    value = v
                else:
                    value = list(v) 
                try:
                    curv = getattr(r, k)
                except AttributeError:
                    raise AttributeError(u'{k} is not a valid attribute for a resource'.format(k=k))
                else:
                    if curv == None and type(value) in [unicode, str, dict]:
                        setattr(r, k, value)
                    elif curv == None:
                        setattr(r, k, value[0])
                        if len(value) > 1:
                            raise Exception('rats')
                    elif type(curv) == list:
                        value_new = deepcopy(curv)
                        value_new.extend(value)
                        setattr(r, k, value_new)
                    elif type(curv) == dict and type(value) == tuple:
                        value_new = deepcopy(curv)
                        value_new[value[0]] = value[1]
                        setattr(r, k, value_new)
                    elif type(curv) == dict and type(value) == dict:
                        value_new = deepcopy(curv)
                        for kk in value.keys():
                            value_new[kk] = value[kk]
                        setattr(r, k, value_new)
                    else:
                        logger.debug(u'k={0}'.format(k))
                        logger.debug(value)
                        logger.debug(u'type(curv)= {0}'.format(type(curv)))
                        logger.debug(u'type(value)= {0}'.format(type(value)))
                        raise Exception('bother')

        return r

    def _parse_authors(self, content_text):
        return self._parse_peeps(RX_AUTHORS, content_text)

    def _parse_editors(self, content_text):
        return self._parse_peeps(RX_EDITORS, content_text)

    def _parse_identifiers(self, content_text):
        """Parse identifying strings of interest from an AWOL blog post."""

        logger = logging.getLogger(sys._getframe().f_code.co_name)
        
        identifiers = {}
        if content_text == None:
            return identifiers
        text = content_text.lower()
        words = list(set(text.split()))

        def get_candidates(k, kk, text):
            candidates = []
            rexx = RX_IDENTIFIERS[k]
            for rx in rexx[kk]:
                candidates.extend([u''.join(groups) for groups in rx.findall(text)])
            if len(candidates) > 1:
                candidates = list(set(candidates))
            return candidates

        def extract(k, text):
            m = RX_IDENTIFIERS[k]['extract']['precise'].match(text)
            if m is not None:
                if len(m.groups()) == 1:
                    return m.groups()[0]
            else:
                try:
                    m = RX_IDENTIFIERS[k]['extract']['fallback'].match(text)
                except KeyError:
                    pass
                else:
                    if m is not None:
                        if len(m.groups()) == 1:
                            return m.groups()[0]
            logger.error("failed to match {0} in {1}".format(k, text))
            raise Exception

        for k in RX_IDENTIFIERS.keys():
            if k in u' '.join(words):
                if k not in identifiers.keys():
                    identifiers[k] = {}
                for kk in ['electronic', 'generic']:
                    candidates = get_candidates(k, kk, text)
                    #logger.debug('candidates({0},{1}) {2})'.format(k, kk, candidates))
                    if len(candidates) > 0:
                        identifiers[k][kk] = []
                        for candidate in candidates:
                            extraction = extract(k, candidate)
                            #logger.debug('extraction({0},{1}) {2})'.format(k, kk, extraction))
                            identifiers[k][kk].append(extraction)
                        if len(identifiers[k][kk]) > 1:
                            identifiers[k][kk] = list(set(identifiers[k][kk]))
                if len(identifiers[k].keys()) == 0:
                    logger.warning(u'failed to match valid issn in {0}'.format(text))
                # regularize presentation form and deduplicate issns
                if k == 'issn':
                    try:
                        identifiers[k]['electronic'] = [issn.replace(u' ', u'-').upper() for issn in identifiers[k]['electronic']]
                    except KeyError:
                        pass
                    try:
                        identifiers[k]['generic'] = [issn.replace(u' ', u'-').upper() for issn in identifiers[k]['generic']]
                    except KeyError:
                        pass
                    if 'electronic' in identifiers[k].keys() and 'generic' in identifiers[k].keys():
                        for ident in identifiers[k]['generic']:
                            if ident in identifiers[k]['electronic']:
                                identifiers[k]['generic'].remove(ident)
                        if len(identifiers[k]['generic']) == 0:
                            del identifiers[k]['generic']
        #logger.debug("identifiers: {0}".format(identifiers))
        return identifiers

    def _parse_peeps(self, rx_list, content_text):

        cooked = []
        raw = u''
        for rx in rx_list:
            m = rx.search(content_text)
            if m:
                raw = m.groups()[-1]
                break
        if len(raw) > 0:
            if u',' in raw:
                cracked = raw.split(u',')
            else:
                cracked = [raw,]
            for chunk in cracked:
                if u' and ' in chunk:
                    cooked.extend(chunk.split(u' and '))
                else:
                    cooked.append(chunk)
            cooked = [normalize_space(peep) for peep in cooked if len(normalize_space(peep)) > 0]
        return cooked

    def _reconcile_titles(self, anchor_title=None, article_title=None):

        if anchor_title is None and article_title is None:
            return None
        if anchor_title is None:
            return (check_colon(article_title),)
        if article_title is None:
            return (check_colon,)
        anchor_lower = anchor_title.lower()
        article_lower = article_title.lower()
        if anchor_lower == article_lower:
            return (article_title,)
        clean_article_title = check_colon(article_title)
        clean_article_lower = clean_article_title.lower()
        if clean_article_lower == anchor_lower:
            return (anchor_title,)
        elif clean_article_lower in anchor_lower:
            return (clean_article_title, anchor_title)
        else:
            return (anchor_title,)

    def _set_provenance(self, resource, article, fields=None):
        updated = article.root.xpath("//*[local-name()='updated']")[0].text.strip()  
        if fields is None: 
            resource_fields = sorted([k for k in resource.__dict__.keys() if '_' != k[0]])
        else:
            resource_fields = fields
        resource.set_provenance(article.id, 'citesAsDataSource', updated, resource_fields)
        resource.set_provenance(article.url, 'citesAsMetadataDocument', updated)        

