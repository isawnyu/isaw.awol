#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Work with an Atom entry representing an AWOL blog post.

This module defines the following classes:
 
 * AwolArticle: represents key information about the entry.

"""

import codecs
#import csv
import logging
import os
import pkg_resources
import re
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
RX_MATCH_DOMAIN = re.compile('^https?:\/\/([^/#]+)')
RX_IDENTIFIERS = {
    'issn': {
        'electronic': [
            re.compile(r'(electronic|e-|e‒|e–|e—|online|on-line|digital)([\s:]*issn[^\d]*[\dX-‒–—]{4}[-‒–—\s]?[\dX]{4})', re.IGNORECASE),
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
    'oi.uchicago.edu'
]
AGGREGATOR_IGNORE = [
    'http://www.jstor.org/page/info/about/archives/collections.jsp'
]
POST_SELECTIVE = {
    'http://ancientworldonline.blogspot.com/2012/07/chicago-demotic-dictionary-t.html': [0]
}
SUBORDINATE_FLAGS = [
    'terms of use',
    'download pdf',
    'download'
]

RX_DASHES = re.compile(r'[‒–—-]+')

class AwolArticle(Article):
    """Manipulate and extract data from an AWOL blog post."""

    def __init__(self, atom_file_name=None, json_file_name=None):

        Article.__init__(self, atom_file_name, json_file_name)

    def parse_atom_resources(self):
        """Extract information about all resources in the post."""

        logger = logging.getLogger(sys._getframe().f_code.co_name)

        try:
            if self.url is None:
                return None
        except AttributeError:
            return None
        resources = []

        title = self.title
        colon_prefix = title.split(u':')[0].lower()
        if colon_prefix in COLON_PREFIXES.keys() and (COLON_PREFIXES[colon_prefix])[0] == 'yes':
            logger.debug('post ignored: title prefix "{0}" found in COLON_PREFIXES with omit=yes'.format(colon_prefix))
            return resources

        try:
            soup = self.soup
        except AttributeError:
            logger.warning(u'post ignored: could not parse content in {0}: {1}'.format(self.url, self.title))
            return None
        published = self.root.xpath("//*[local-name()='published']")[0].text.strip()
        updated = self.root.xpath("//*[local-name()='updated']")[0].text.strip()
        anchors = [a for a in soup.find_all('a')]
        anchors = [a for a in anchors if a.get('href') is not None]
        urls = [a.get('href') for a in anchors if a.get('href') is not None]
        unique_urls = list(set(urls))
        domains = []
        for url in urls:
            m = RX_MATCH_DOMAIN.match(url)
            try:
                domain = m.group(1)
            except AttributeError:
                pass
            else:
                domains.append(domain)
        domains = list(set(domains))
        domains = [d for d in domains 
            if d not in DOMAINS_TO_IGNORE 
            and d not in DOMAINS_SECONDARY]
        if len(domains) == 1 and len(unique_urls) > 1 and domains[0] in AGGREGATORS:
            # this article is about an aggregator: parse for multiple resources
            if domains[0] == u'oi.uchicago.edu':
                print '***********************************************************'
                print 'oi.uchicago.edu:'
                print u'    url: {0}'.format(self.url)
                print u'    title: {0}'.format(self.title)
                print u'    tag: {0}'.format(self.id)
            if self.url in POST_SELECTIVE.keys():
                anchors = [a for i,a in enumerate(anchors) if i in POST_SELECTIVE[self.url]]
            for a in [a for a in anchors if domains[0] in a.get('href') and a.get('href') not in AGGREGATOR_IGNORE and a.get_text().strip() != u'']:
                if normalize_space(a.get_text()).lower() in SUBORDINATE_FLAGS:
                    print u'          append {0} to {1}'.format(a.get_text(), resources[-1].title)
                    resources[-1].subordinate_resources.append({
                        'url': a.get('href'),
                        'label': normalize_space(a.get_text())
                        })
                else:
                    html = u''
                    next_node = a.next_element
                    while True:
                        html = html + unicode(next_node)
                        if next_node.name in ['blockquote', 'hr']:
                            break
                        next_node = next_node.next_element
                        if next_node is None:
                            break
                    html = u'<div>' + html + u'</div>'
                    this_soup = BeautifulSoup(html)
                    resource = self._parse_resource(
                        domain=domains[0],
                        url=a.get('href'),
                        title=a.get_text().strip(),
                        content_soup=this_soup)
                    resource_fields = sorted([k for k in resource.__dict__.keys() if '_' not in k])
                    resource.set_provenance(self.id, 'citesAsDataSource', updated, resource_fields)
                    resource.set_provenance(self.url, 'citesAsMetadataDocument', updated)
                    resources.append(resource)
                    if domains[0] == u'oi.uchicago.edu':
                        print '----------------------------------------------------------'
                        print u'    resource: {0}'.format(resource.title)
                        print u'              {0}'.format(resource.url)

        elif len(domains) == 1 and len(unique_urls) > 1:
            logger.warning('aggregator detected, but ignored: {0}'.format(domains[0]))
        elif len(domains) == 1:
            # this is an article about a single resource
            urls=[url for url in urls if domains[0] in url]
            resource = self._parse_resource(
                domain=domains[0], 
                url=[url for url in urls if domains[0] in url][0],
                title=self._rtitle_from_ptitle(), 
                content_soup=self.soup)
            resource_fields = sorted([k for k in resource.__dict__.keys() if '_' not in k])
            resource.set_provenance(self.id, 'citesAsDataSource', updated, resource_fields)
            resource.set_provenance(self.url, 'citesAsMetadataDocument', updated)
            resources.append(resource)
        elif len(domains) > 1:
            # this article addresses multiple resources
            emsg = 'This post {0} appears to address multiple' \
            + ' resources. Support for parsing these is not yet' \
            + ' implemented.'
            emsg = emsg.format(self.id)
            raise NotImplementedError(emsg)
        else:
            # this article addresses no external resource
            emsg = u'post ignored: it appears not to address any external resources {0}: {1}'
            emsg = emsg.format(self.url, self.title)
            logger.warning(emsg)
            
        self.resources = resources
        return resources

    def _parse_description(self, content_soup):
        """Parse plain-text description from soup content."""

        desc_node = content_soup.blockquote
        try:
            desc_text = normalize_space(desc_node.get_text())
        except AttributeError:
            desc_text = u''
        if desc_text == u'':
            try:
                desc_node = content_soup.find_all('blockquote')[1]
            except IndexError:
                desc_text = u''
            else:
                desc_text = normalize_space(desc_node.get_text())
            if desc_text == u'':
                first_anchor = content_soup.a
                try:
                    nodes = first_anchor.next_siblings
                except AttributeError:
                    desc_text == u''
                else:
                    nodes = [node for node in nodes if node.name not in ['a', 'h1', 'h2', 'h3', 'h4', 'hr']]
                    html = u'<div>' + first_anchor.text + u': ' + u''.join([unicode(node) for node in nodes]) + u'</div>'
                    soup = BeautifulSoup(html)
                    desc_text = normalize_space(soup.get_text())
                    if desc_text == u'':
                        desc_text = normalize_space(content_soup.get_text())
        return desc_text

    def _parse_resource(self, domain, url, title, content_soup):
        """Extract single resource from a blog post."""

        logger = logging.getLogger(sys._getframe().f_code.co_name)

        r = Resource()
        r.domain = domain
        r.url = url
        if title is None or len(title.strip()) == 0:
            print "Arugula!"
            req = requests.get(url)
            if req.status_code == 200:
                title_soup = BeautifulSoup(req.text)
                r.title = title_soup.title.text
            else:
                print "fail fail fail"
            print 'r.title: {0} ({1})'.format(r.title, self.url)
        else:
            r.title = title
        content_text = content_soup.get_text()
        r.identifiers = self._parse_identifiers(content_text)
        r.description = self._parse_description(content_soup)
        r.keywords = self._parse_tags(self.title, title, self.categories, content_text) 
        s = u''
        try:
            s = u'{0}'.format(r.title)
        except TypeError:
            pass
        try:
            s = s + u' {0}'.format(r.description)
        except TypeError:
            pass
        language = langid.classify(s)
        if language[1] >= LANGID_THRESHOLD:
            r.language = language
        #r.subordinate_resources = self._parse_sub_resources(content_soup)
        #raise Exception
        try:
            r.append_event(
                'Data automatically parsed from content of {0}.'.format(self.url))
        except AttributeError:
            r.append_event(
                'Data automatically parsed from content of {0}.'.format(self.id))
        return r

    def _parse_tags(self, post_title, resource_title, post_categories, resource_text):
        """Infer and normalize resource tags."""

        logger = logging.getLogger(sys._getframe().f_code.co_name)

        tags = []
        for s in (post_title, resource_title, resource_text):
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
                        tags.append(u'mixed access')
                    else:
                        tags.append(u'open access')
                if 'series' in lower_list and 'lecture' not in lower_list:
                    tags.append(u'series')
                # mine for phrases
                for k in TITLE_SUBSTRING_PHRASES.keys():
                    if k in lower_s:
                        tag = TITLE_SUBSTRING_PHRASES[k]
                        tags.append(tag)

        # convert post categories to tags
        for c in post_categories:    
            tag = c['term'].lower()
            if 'kind#post' not in tag:
                if tag in TITLE_SUBSTRING_TAGS.keys():
                    tag = TITLE_SUBSTRING_TAGS[tag]
                elif c['term'] == u'Boğazköy':
                    tag = u'Boğazköy'
                elif c['term'] == u'Subsistenz und Umwelt im frühen Vorderasien':
                    tag = u'Subsistenz und Umwelt im frühen Vorderasien'
                else:
                    logger.error(u'unexpected category tag: {0}'.format(c['term']))
                    raise Exception
                tags.append(tag)


        # consolidate and normalize tags
        tags = list(set(tags))
        keywords = []
        for tag in tags:
            if tag == u'':
                pass
            elif u',' in tag:
                keywords.extend(tag.split(u','))
            #elif u'BoğAzköY' == tag:
            #    keywords.append(u'Boğazköy')
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


        return sorted(list(set(keywords)))

    def _parse_sub_resources(self, content_soup):
        """Extract subordinate resources."""

        logger = logging.getLogger(sys._getframe().f_code.co_name)

        anchors = [a for a in content_soup.find_all('a')]
        urls = [a.get('href') for a in anchors[1:]]
        for url in urls:
            logger.debug('url is: {0}'.format(url))

    def _rtitle_from_ptitle(self):
        """Parse resource title from post title."""

        title = self.title
        if u':' in title:
            colon_prefix = title.split(u':')[0].lower()
            if colon_prefix in COLON_PREFIXES.keys() and (COLON_PREFIXES[colon_prefix])[1] == 'yes':
                title = u':'.join(title.split(u':')[1:])
                return title.strip()
            else:
                return title
        else:
            return title

    def _parse_identifiers(self, content_text):
        """Parse identifying strings of interest from an AWOL blog post."""

        logger = logging.getLogger(sys._getframe().f_code.co_name)
        
        identifiers = {}
        text = normalize_space(content_text).lower()
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
            if k in words:
                if k not in identifiers.keys():
                    identifiers[k] = {}
                for kk in ['electronic', 'generic']:
                    candidates = get_candidates(k, kk, text)
                    logger.debug('candidates({0},{1}) {2})'.format(k, kk, candidates))
                    if len(candidates) > 0:
                        identifiers[k][kk] = []
                        for candidate in candidates:
                            extraction = extract(k, candidate)
                            logger.debug('extraction({0},{1}) {2})'.format(k, kk, extraction))
                            identifiers[k][kk].append(extraction)
                        if len(identifiers[k][kk]) > 1:
                            identifiers[k][kk] = list(set(identifiers[k][kk]))
                if len(identifiers[k].keys()) == 0:
                    logger.warning(u'failed to match valid issn in {0}'.format(text))
                if k == 'issn':
                    try:
                        identifiers[k]['electronic'] = [RX_DASHES.sub(u'-', normalize_space(issn).replace(u' ', u'-')).upper() for issn in identifiers[k]['electronic']]
                    except KeyError:
                        pass
                    identifiers[k]['generic'] = [RX_DASHES.sub(u'-', normalize_space(issn).replace(u' ', u'-')).upper() for issn in identifiers[k]['generic']]
        return identifiers


