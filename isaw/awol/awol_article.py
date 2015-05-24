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
        row['col_pre']:
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
RX_MATCH_DOMAIN = re.compile('^https?:\/\/([^/#]+)')
RX_IDENTIFIERS = {
    'issn': {
        'findall': re.compile(r'issn[^\d]*[\dX]{4}-?[\dX]{4}', re.IGNORECASE),
        'match': re.compile(r'issn[^\d]*([\dX]{4}-?[\dX]{4})', re.IGNORECASE),
        'pref_flags' : ['electrón', 'électron', 'electron', 'digital', 'online']
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

class AwolArticle(Article):
    """Manipulate and extract data from an AWOL blog post."""

    def __init__(self, atom_file_name=None, json_file_name=None):

        Article.__init__(self, atom_file_name, json_file_name)

    def parse_atom_resources(self):
        """Extract information about all resources in the post."""

        logger = logging.getLogger(sys._getframe().f_code.co_name)

        resources = []
        soup = self.soup
        anchors = [a for a in soup.find_all('a')]
        urls = [a.get('href') for a in anchors]
        domains = list(set([RX_MATCH_DOMAIN.match(url).group(1) for url in list(set(urls))]))
        domains = [d for d in domains 
            if d not in DOMAINS_TO_IGNORE 
            and d not in DOMAINS_SECONDARY]
        if len(domains) == 1:
            # this is an article about a single resource
            resource = self._parse_resource(
                domain=domains[0], 
                url=[url for url in urls if domains[0] in url][0],
                title=self._rtitle_from_ptitle(), 
                content_soup=self.soup)
            resources.append(resource)
        elif len(domains) > 1:
            # this article addresses multiple resources
            emsg = 'This post {0} appears to address multiple'
            + ' resources. Support for parsing these is not yet'
            + ' implemented.'
            emsg = emsg.format(self.id)
            logger.error(emsg)
            raise NotImplementedError(emsg)
        else:
            # this article addresses no external resource
            emsg = 'This post ({0}) appears not to address any'
            + ' external resources. It has been ignored.'
            emsg = emsg.format(self.id)
            logger.warning(emsg)
            pass
        self.resources = resources
        return resources

    def _parse_description(self, content_soup):
        """Parse plain-text description from soup content."""

        desc_node = content_soup.blockquote
        desc_text = normalize_space(desc_node.get_text())
        if desc_text == u'':
            desc_node = content_soup.find_all('blockquote')[1]
            desc_text = normalize_space(desc_node.get_text())
            if desc_text == u'':
                first_anchor = content_soup.a
                nodes = [node for node in first_url.next_siblings if node.name not in ['a', 'h1', 'h2', 'h3', 'h4', 'hr']]
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
        r.title = title
        content_text = content_soup.get_text()
        r.identifiers = self._parse_identifiers(content_text)
        r.description = self._parse_description(content_soup)
        r.keywords = self._parse_tags(self.title, self.categories, content_text) 
        #r.subordinate_resources = self._parse_sub_resources(content_soup)
        #raise Exception
        return r

    def _parse_tags(self, post_title, post_categories, content_text):
        """Infer and normalize resource tags."""

        logger = logging.getLogger(sys._getframe().f_code.co_name)

        tags = []
        # mine post title for tags
        lower_title = post_title.lower()
        for k in TITLE_SUBSTRING_TAGS.keys():
            if k in lower_title:
                tag = TITLE_SUBSTRING_TAGS[k]
        tags.append(tag)
        if u'open' in lower_title and u'access' in lower_title:
            if u'partial' in lower_title:
                tags.append(u'Mixed Access')
            else:
                tags.append(u'Open Access')
        if 'series' in lower_title and 'lecture' not in lower_title:
            tags.append(u'Series')

        # convert post categories to tags
        for c in post_categories:    
            tag = c['term'].lower()
            if 'kind#post' not in tag:
                if tag in TITLE_SUBSTRING_TAGS.keys():
                    tag = TITLE_SUBSTRING_TAGS[tag]
                else:
                    tag = (tag if tag == tag.upper() else tag.title())
                tags.append(tag)

        # mine post content for tags
        lower_content = content_text.lower()
        for k in TITLE_SUBSTRING_TAGS.keys():
            if k in lower_content:
                tag = TITLE_SUBSTRING_TAGS[k]
        tags.append(tag)

        # deal with special cases


        tags = list(set(tags))
        keywords = []
        for tag in tags:
            if ',' in tag:
                keywords.extend(tag.split(','))
            else:
                keywords.append(tag)
        keywords = list(set(keywords))
        return keywords

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
            colon_prefix = title.split(u':')[0]
            if colon_prefix in COLON_PREFIXES.keys() and (COLON_PREFIXES[colon_prefix])[1] == 'yes':
                title = u':'.join(title.split(u':')[1:])
                return title.strip()
        else:
            return title

    def _parse_identifiers(self, content_text):
        """Parse identifying strings of interest from an AWOL blog post."""

        identifiers = {}
        for k,rx in RX_IDENTIFIERS.iteritems():
            idents = list(set([normalize_space(s) for s in rx['findall'].findall(content_text)]))
            if len(idents) == 1:
                m = rx['match'].match(idents[0])
                if len(m.groups()) == 1:
                    identifiers[k] = m.groups()[0]
                else:
                    logger.warning('Unexpected disaster trying to parse {0} from "{1}"'.format(k, idents[0]))
            elif len(idents) > 1:
                flagged_idents = [ident for ident in idents if lambda s: len([f for f in rx['pref_flags'] if f in s.lower()]) > 0]
                if len(flagged_idents) == 1:
                    m = rx['match'].match(flagged_idents[0])
                    if len(m.groups()) == 1:
                        identifiers[k] = m.groups()[0]
                    else:
                        logger.warning('Unexpected disaster trying to parse {0} from "{1}"'.format(k, flagged_idents[0]))
        return identifiers
