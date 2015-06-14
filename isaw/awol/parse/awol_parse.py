#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse HTML content for resources.

This module defines the following classes:

 * AwolParser: parse AWOL blog post content for resources
"""

from copy import copy
import logging
import pkg_resources
import re
import sys

from bs4 import BeautifulSoup
from bs4.element import NavigableString
import langid
import unicodecsv

from isaw.awol.clean_string import *
from isaw.awol.normalize_space import normalize_space
from isaw.awol.resource import Resource

DOMAINS_IGNORE = [
    'draft.blogger.com',
    'bobcat.library.nyu.edu',
    'cientworldonline.blogspot.com' # that there's a typo in a link somewhere in the blog
]
DOMAINS_SELF = [
    'ancientworldonline.blogspot.com',
]
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
RX_IDENTIFIERS = {
    'issn': {
        'electronic': [
            re.compile(r'(e-|e‒|e–|e—|e|)(issn[^\d]*[\dX-‒–—]{4}[-‒–—\s]?[\dX]{4})', re.IGNORECASE),
            re.compile(r'(electronic|online|on-line|digital)([\s:]*issn[^\d]*[\dX-‒–—]{4}[-‒–—\s]?[\dX]{4})', re.IGNORECASE),
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
            domains = [domain for domain in domains if domain not in self.skip_domains]
            c['domains'] = domains
        return c['domains']

    def parse(self, article):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        #logger.debug('parsing {0}'.format(article.id))
        c = self.content
        self.reset(article.soup)
        resources = self._get_resources(article)
        return resources

    def _get_resources(self, article):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        #logger.debug('getting resources from {0}'.format(article.id))
        primary_resource = self._get_primary_resource(article)
        #primary_resource.subordinate_resources = self._get_subordinate_resources(article)
        #for sr in primary_resource.subordinate_resources:
        #    parent = {
        #        'title': primary_resource.title,
        #        'url': primary_resource.url
        #    }
        #    if len(primary_resource.identifiers.keys()) > 0:
        #        try:
        #            parent['issn'] = primary_resource.identifiers['issn']['electronic'][0]
        #        except KeyError:
        #            try:
        #                parent['issn'] = primary_resource.identifiers['issn']['generic'][0]
        #            except KeyError:
        #                try:
        #                    parent['isbn'] = primary_resource.identifiers['isbn'][0]
        #                except KeyError:
        #                    pass                            
        #    sr.is_part_of = parent
        #    #logger.debug(sr)
        #primary_resource.related_resources = self._get_related_resources()
        ##logger.debug(u'got: "{0}"'.format(unicode(primary_resource)))
        #foo = [primary_resource,] + primary_resource.subordinate_resources + primary_resource.related_resources
        #return foo
        return [primary_resource,]

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
            
            if 'year' not in g.keys():
                return (m.group(g['volume']), None)
            elif 'volume' not in g.keys():
                return (None, m.group(g['year']))
            else:
                return (m.group(g['volume'], g['year']))

    def _get_subordinate_resources(self, article):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        resources = []
        anchors = self._get_anchors()[1:]
        for a in anchors:
            # title
            title_context = self._get_anchor_ancestor_for_title(a)
            title = clean_string(title_context.get_text())

            # try to extract volume and year
            try:
                volume, year = self._grok_analytic_title(title)
            except TypeError:
                volume = year = None
            if volume is not None and year is None:
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

            self._set_provenance(resource, article)

            resources.append(resource)
        return resources

    def _get_description(self, soup):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        desc_nodes = soup.body.div.contents
        desc_lines = []
        for desc_node in desc_nodes:
            #logger.debug(u'desc_node: \n    {0}'.format(unicode(desc_node)))
            if type(desc_node) == NavigableString:
                line = unicode(desc_node)
                #logger.debug(u'  appending (A): "{0}"'.format(line))
                desc_lines.append(line)
            elif desc_node.name == 'br':
                desc_lines[-1] += u'.'
                #logger.debug(u'  backslapping fullstop for br (A)')
            else:
                anchors = self._filter_anchors(desc_node.find_all('a'))
                #logger.debug('anchor length: {0}'.format(len(anchors)))
                if len(anchors) > 1:
                    for this_node in desc_node.contents:
                        if this_node == anchors[1]:
                            break
                        if type(this_node) == NavigableString:
                            line = unicode(this_node)
                            #logger.debug(u'  appending (B): "{0}"'.format(line))
                            desc_lines.append(line)
                        elif desc_node.name == 'br':
                            desc_lines[-1].append(u'.')
                            #logger.debug(u'backslapping fullstop for br (B)')
                        else:
                            lines = this_node.get_text('\n').split('\n')
                            #logger.debug(u'  extending with: {0}'.format(lines))
                            desc_lines.extend(lines)
                    break
                else:
                    try:
                        desc_lines.extend(desc_node.get_text('\n').split('\n'))
                    except AttributeError:
                        pass
                    else:
                        lines = desc_node.get_text('\n').split('\n')
                        #logger.debug(u'  extended with: {0}'.format(lines))
        #logger.debug('desc_lines follows')
        #for line in desc_lines:
            #logger.debug(u'   {0}'.format(line))
        if len(desc_lines) == 0:
            desc_text = None
        else:
            #logger.debug(u'before dedupe: {0}'.format(u'\n'.join(desc_lines)))
            desc_text = deduplicate_lines(u'\n'.join(desc_lines))
            if len(desc_text) == 0:
                desc_text = None
            else:
                desc_text = desc_text.replace(u'%IMAGEREPLACED%', u'').strip()
                desc_text = RX_PUNCT_FIX.sub(r'\1', desc_text)
                #logger.debug(u'before sentence dedupe: {0}'.format(desc_text))
                desc_text = deduplicate_sentences(desc_text)
                #logger.debug(u'after sentence dedupe: {0}'.format(desc_text))
                desc_text = RX_PUNCT_DEDUPE.sub(r'\1', desc_text)
                if len(desc_text) == 0:
                    desc_text = None
                elif desc_text[-1] != u'.':
                    desc_text += u'.'

        #logger.debug(u"desc_text: {0}".format(desc_text))

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

    def _get_description_html(self):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        c = self.content
        soup = c['soup']
        first_node = soup.body.contents[0]
        #logger.debug(unicode(first_node))
        last_node = None
        for tag_name in ['blockquote',]:
            for node in first_node.find_all_next(tag_name):
                if len(node.get_text().strip()) > 0:
                    last_node = node
                    break
            if last_node is not None:
                break
        if last_node is None:
            first_anchor = first_node.find_next('a')
            if first_anchor is not None:
                if not self._consider_anchor(first_anchor):
                    node = first_anchor.next_element
                else:
                    node = first_anchor.find_next('a')
                    if node is not None:
                        node = node.next_element 
                if node is None:
                    node = first_anchor
                while node.next_element is not None:
                    if node.name in ['hr', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ul', 'ol', 'p']:
                        break
                    else:
                        node = node.next_element
                last_node = node
            else:
                last_node = first_node

        html = u' {0}.\n'.format(unicode(first_node))
        next_node = first_node.next_element
        while next_node != last_node:
            html = html + u'\n{0}'.format(unicode(next_node))
            try:
                next_node = next_node.next_element
            except AttributeError:
                break
        html = html + u' {0}\n'.format(unicode(next_node)) 
        html = u'<div>\n' + html + u'\n</div>'
        #logger.debug('description html follows')
        #for hh in html.split(u'\n'):
            #logger.debug(u'   {0}'.format(hh))
        #logger.debug(u'description html:\n{0}'.format(html))
        return html

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
        html = self._get_description_html()
        this_soup = BeautifulSoup(html)
        #logger.debug(u'description soup: \n\n{0}'.format(unicode(this_soup)))
        #logger.debug(u'description text: \n\n{0}'.format(this_soup.get_text()))
        desc_text = self._get_description(this_soup)
        #logger.debug(u'got desc_text: \n\n{0}'.format(desc_text))

        # parse identifiers
        identifiers = self._parse_identifiers(desc_text)

        # language
        language = self._get_language(title, title_extended, desc_text)

        # determine keywords
        keywords = self._parse_keywords(article.title, titles[-1], article.categories)

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

        # provenance
        self._set_provenance(resource, article)

        #logger.debug(u'returning resource: "{0}"'.format(unicode(resource)))
        return resource

    def _set_provenance(self, resource, article):
        updated = article.root.xpath("//*[local-name()='updated']")[0].text.strip()   
        resource_fields = sorted([k for k in resource.__dict__.keys() if '_' != k[0]])
        resource.set_provenance(article.id, 'citesAsDataSource', updated, resource_fields)
        resource.set_provenance(article.url, 'citesAsMetadataDocument', updated)        

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

    def _consider_anchor(self, a):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
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

    def _get_anchors(self):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        c = self.content
        if c['anchors'] is not None:
            #logger.debug('already have anchors')
            return c['anchors']
        soup = c['soup']
        #logger.debug(u'finding anchors in: {0}'.format(unicode(soup))) 
        raw_anchors = [a for a in soup.find_all('a')]
        #logger.debug('raw anchors: {0}'.format(', '.join([a.get('href') for a in raw_anchors])))
        anchors = self._filter_anchors(raw_anchors)
        c['anchors'] = anchors
        return anchors

    def reset(self, content_soup=None):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        self.content = {}
        c = self.content
        if content_soup is not None:
            c['soup'] = content_soup
        c['anchors'] = None
        c['domains'] = None
        self.skip_domains = copy(DOMAINS_IGNORE) + copy(DOMAINS_SELF)
        self.skip_text = copy(ANCHOR_TEXT_IGNORE)
        self.skip_urls = copy(ANCHOR_URLS_IGNORE)





        