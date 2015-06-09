#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse HTML content for resources.

This module defines the following classes:

 * AwolParser: parse AWOL blog post content for resources
"""

import logging
import pkg_resources
import re
import sys

from bs4 import BeautifulSoup
import langid
import unicodecsv

from isaw.awol.clean_string import clean_string, deduplicate_lines
from isaw.awol.normalize_space import normalize_space
from isaw.awol.resource import Resource

DOMAINS_IGNORE = [
    'draft.blogger.com',
]
DOMAINS_SELF = [
    'ancientworldonline.blogspot.com'
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
    {
        'rx': re.compile(r'^[^\d]*(\d{4})\W*(\d+)[^\d]*$', re.IGNORECASE),
        'volume': 2,
        'year': 1
    },
    {
        'rx': re.compile(r'^[^\d]*(\d{1-3})\W*(\d{4})[^\d]*$', re.IGNORECASE),
        'volume': 1,
        'year': 2
    }
]
def domain_from_url(url):
    return url.replace('http://', '').replace('https://', '').split('/')[0]

class AwolBaseParser:
    """Superclass: Extract data from an AWOL blog post."""

    def __init__(self):
        self.reset()

    def get_domains(self, content_soup=None):
        """Determine domains of resources linked in content."""

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
            domains = [domain for domain in domains if domain not in DOMAINS_IGNORE and domain not in DOMAINS_SELF]
            c['domains'] = domains
        return c['domains']

    def parse(self, article):
        c = self.content
        if c['soup'] is None:
            self.reset(article.soup)
        elif c['soup'] != article.soup:
            self.reset(article.soup)
        return self._get_resources(article)

    def _get_resources(self, article):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        primary_resource = self._get_primary_resource(article)
        primary_resource.subordinate_resources = self._get_subordinate_resources()
        for sr in primary_resource.subordinate_resources:
            parent = {
                'title': primary_resource.title,
                'url': primary_resource.url
            }
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
            sr.is_part_of = parent
            logger.debug(sr)
        primary_resource.related_resources = self._get_related_resources()
        logger.debug(primary_resource)
        return primary_resource

    def _get_anchor_ancestor_for_title(self, anchor):
        a = anchor
        parents = a.find_parents('li')
        if len(parents) > 0 and len(parents[0].find_all('a')) == 1:
            anchor_ancestor = parents[0]
        else:
            parents = a.find_parents('span')
            i = 0
            while i < len(parents):
                if len(parents[i].find_all('a')) > 1:
                    break
                i = i+1
            i = i - 1
            if i > -1:
                anchor_ancestor = parents[i]
            else:
                parents = a.find_parents('p')
                if len(parents) > 0 and len(parents[0].find_all('a')) == 1:
                    anchor_ancestor = parents[0]
                else:
                    anchor_ancestor = a
        return anchor_ancestor

    def _get_related_resources(self):
        resources = []
        anchors = self._get_anchors()[1:]
        anchors = [a for a in anchors if domain_from_url(a.get('href')) in DOMAINS_SELF]
        for a in anchors:
            # title
            title_context = self._get_anchor_ancestor_for_title(a)
            title = clean_string(title_context.get_text())

            # description
            html = u' {0}\n'.format(unicode(title_context))
            next_node = title_context.next_element
            while True:
                html = html + u' {0}\n'.format(unicode(next_node))
                if next_node.name in ['blockquote', 'hr', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ul', 'p', 'div', 'ol']:
                    break
                next_node = next_node.next_element
                if next_node is None:
                    break
            html = u'<div>\n' + html + u'\n</div>'
            this_soup = BeautifulSoup(html)
            desc_text = self._get_description(this_soup)

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
                params['language'] = language
            if len(keywords) > 0:
                params['keywords'] = keywords
            resource = self._make_resource(**params)
            resources.append(resource)
        return resources

    def _grok_analytic_title(self, title):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        for g in RX_ANALYTIC_TITLES:
            m = g['rx'].match(title)
            if m is not None:
                break
        if m is not None:
            #logger.debug("grok: {0}-{1}".format(*m.group(g['year'],g['volume'])))
            return (m.group(g['volume'], g['year']))

    def _get_subordinate_resources(self):
        resources = []
        anchors = self._get_anchors()[1:]
        anchors = [a for a in anchors if domain_from_url(a.get('href')) not in DOMAINS_IGNORE and domain_from_url(a.get('href')) not in DOMAINS_SELF]
        for a in anchors:
            # title
            title_context = self._get_anchor_ancestor_for_title(a)
            title = clean_string(title_context.get_text())

            # try to extract volume and year
            try:
                volume, year = self._grok_analytic_title(title)
            except TypeError:
                volume = year = None

            # description
            html = u' {0}\n'.format(unicode(title_context))
            next_node = title_context.next_element
            while True:
                html = html + u' {0}\n'.format(unicode(next_node))
                if next_node.name in ['blockquote', 'hr', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ul', 'p', 'div', 'ol']:
                    break
                next_node = next_node.next_element
                if next_node is None:
                    break
            html = u'<div>\n' + html + u'\n</div>'
            this_soup = BeautifulSoup(html)
            desc_text = self._get_description(this_soup)

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
                params['language'] = language
            if len(keywords) > 0:
                params['keywords'] = keywords
            if volume is not None:
                params['volume'] = volume
            if year is not None:
                params['year'] = year
            resource = self._make_resource(**params)
            resources.append(resource)
        return resources

    def _get_description(self, desc_nodes):
        desc_lines = []
        for desc_node in desc_nodes:
            if len(desc_node.find_all('a')) > 1:
                break
            try:
                desc_lines.extend(desc_node.get_text('\n').split('\n'))
            except AttributeError:
                pass
        if len(desc_lines) == 0:
            desc_text = None
        else:
            desc_text = deduplicate_lines(u'\n'.join(desc_lines))
            if len(desc_text) == 0:
                desc_text = None
        return desc_text        

    def _get_language(self, *args):
        chunks = [chunk for chunk in args if chunk is not None]
        s = u' '.join((tuple(chunks)))
        s = normalize_space(s)
        if s != u'':
            language = langid.classify(s)
            if language[1] >= LANGID_THRESHOLD:
                return language
        return None


    def _get_primary_resource(self, article):
        logger = logging.getLogger(sys._getframe().f_code.co_name)

        # title
        try:
            a = self._get_anchors()[0]
        except IndexError:
            msg = 'failed to parse primary anchor from {0}'.format(self.content['soup'])
            raise IndexError(msg)
        a_title = clean_string(a.get_text())  
        logger.debug('a_title: "{0}"'.format(a_title))
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
        c = self.content
        soup = c['soup']
        first_node = soup.body.contents[0]
        last_node = None
        for tag_name in ['blockquote', 'div']:
            for node in first_node.find_all_next(tag_name):
                if len(node.get_text().strip()) > 0:
                    last_node = node
                    break
            if last_node is not None:
                break
        if last_node is None:
            first_anchor = first_node.find_next('a')
            for tag_name in ['hr', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ul', 'ol', 'p']:
                last_node = first_anchor.find_next(tag_name)
        html = u' {0}\n'.format(unicode(first_node))
        next_node = first_node.next_element
        while next_node != last_node:
            html = html + u' {0}\n'.format(unicode(next_node))
            next_node = next_node.next_element
        html = html + u' {0}\n'.format(unicode(next_node)) 
        html = u'<div>\n' + html + u'\n</div>'
        this_soup = BeautifulSoup(html)
        desc_text = self._get_description(this_soup)

        # parse identifiers
        identifiers = self._parse_identifiers(desc_text)

        # language
        language = self._get_language(title, title_extended, desc_text)

        # determine keywords
        keywords = self._parse_keywords(article.title, titles[-1], article.categories, desc_text)

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
        if title_extended is not None:
            params['title_extended'] = title_extended
        if language is not None:
            params['language'] = language
        if len(keywords) > 0:
            params['keywords'] = keywords
        resource = self._make_resource(**params)

        # set dates and provenance
        published = article.root.xpath("//*[local-name()='published']")[0].text.strip()
        updated = article.root.xpath("//*[local-name()='updated']")[0].text.strip()        
        resource_fields = sorted([k for k in resource.__dict__.keys() if '_' != k[0]])
        resource.set_provenance(article.id, 'citesAsDataSource', updated, resource_fields)
        resource.set_provenance(article.url, 'citesAsMetadataDocument', updated)

        return resource


    def _parse_keywords(self, post_title=None, resource_title=None, post_categories=[], resource_text=None):
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

        return list(set(keywords))

    def _reconcile_titles(self, anchor_title=None, article_title=None):

        def check_colon(title):
            if u':' in title:
                colon_prefix = article_title.split(u':')[0].lower()
                if colon_prefix in COLON_PREFIXES.keys() and (COLON_PREFIXES[colon_prefix])[1] == 'yes':
                    return clean_string(u':'.join(article_title.split(u':')[1:]))
                else:
                    return title
            else:
                return title

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
            return (clean_article_title,)

    def _make_resource(self, **kwargs):
        r = Resource()
        for k,v in kwargs.items():
            setattr(r, k, v)
        return r

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

    def _get_anchors(self):
        c = self.content
        if c['anchors'] is not None:
            return c['anchors']
        else:
            soup = c['soup']
            anchors = [a for a in soup.find_all('a')]
            anchors = [a for a in anchors if a.get('href') is not None and len(a.get_text()) > 0]
        c['anchors'] = anchors
        return anchors

    def reset(self, content_soup=None):
        self.content = {}
        c = self.content
        if content_soup is not None:
            c['soup'] = content_soup
        else:
            c['soup'] = None       
        c['domains'] = None
        c['anchors'] = None
        c['unique_urls'] = None
        c['resources'] = None

        