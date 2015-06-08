#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Work with an Atom entry representing an AWOL blog post.

This module defines the following classes:
 
 * AwolArticle: represents key information about the entry.

"""

import codecs
#import csv
from importlib import import_module
import logging
import os
import pkg_resources
import pkgutil
import pprint
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

        try:
            title = self.title
        except AttributeError:
            logger.debug('post ignored: no post title')
            return resources
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
        ################# TESTING
        dump_domains = []
        #if len(domains) > 1:
        #    return None
        #if len(domains) == 1 and len(unique_urls) <= 1:
        #    return None
        #if len(domains) == 0:
        #    return None
        #if domains[0] not in dump_domains:
        #    return None
        ################# TESTING
        if len(domains) == 1 and len(unique_urls) > 1 and domains[0] in AGGREGATORS:
            # this article is about an aggregator: parse for multiple resources
            
            if domains[0] in dump_domains:
                dump_it = True
            else:
                dump_it = False
            if dump_it:
                print '***********************************************************'
                print '{0}'.format(domains[0])
                print u'    url: {0}'.format(self.url)
                print u'    title: {0}'.format(self.title)
                print u'    tag: {0}'.format(self.id)

            # filter urls selectively before processing
            if self.url in POST_SELECTIVE.keys():
                anchors = [a for i,a in enumerate(anchors) if i in POST_SELECTIVE[self.url]]

            # loop through anchors and process each as a potential resource
            force_related = None
            force_subordinate = None
            prev_superior = None
            prev_relator = None
            for a in [a for a in anchors if domains[0] in a.get('href') and a.get('href') not in AGGREGATOR_IGNORE and a.get_text().strip() != u'']:
                anchor_text = normalize_space(a.get_text())
                anchor_text_lower = anchor_text.lower()
                anchor_href = normalize_space(a.get('href'))
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
                        anchor_ancestor = a # I am my own grandpa!
                anchor_in_blockquote = len(a.find_parents('blockquote')) > 0
                anchor_in_issue_element = len(a.find_parents('div', class_='issueElement'))
                if anchor_in_blockquote and dump_it: print 'BLOCKQUOTE!'
                if anchor_in_issue_element and dump_it: print 'ISSUE ELEMENT!'

                ancestor_text = normalize_space(anchor_ancestor.get_text())
                ancestor_text_lower = anchor_text.lower()

                # parse a new resource related to this anchor
                if anchor_text_lower not in SUPPRESS_RESOURCE and anchor_href not in [r.url for r in resources]:
                    
                    # try to grab the most relevant stuff for the description, but not too much
                    html = u' {0}\n'.format(unicode(anchor_ancestor))
                    next_node = anchor_ancestor.next_element
                    while True:
                        html = html + u' {0}\n'.format(unicode(next_node))
                        if next_node.name in ['blockquote', 'hr', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ul', 'p', 'div', 'ol']:
                            break
                        next_node = next_node.next_element
                        if next_node is None:
                            break
                    html = u'<div>\n' + html + u'\n</div>'
                    this_soup = BeautifulSoup(html)

                    # parse the resource
                    resource = self._parse_resource(
                        domain=domains[0],
                        url=anchor_href,
                        title=self._parse_title(anchor_text),
                        content_soup=this_soup)
                    resources.append(resource)
                    if dump_it:
                        print u'    resource: {0}'.format(resource.title)
                        print u'              {0}'.format(resource.url)

                    # detect subordinate and related links and append them to the preceding resource
                    if len(resources) > 1 and self.url not in NO_SUBORDINATES:
                        if force_related is not None:
                            if dump_it:
                                print u'              FORCE related: "{0}" ({1}) to "{2}" ({3})'.format(anchor_text, anchor_href, force_related.title, force_related.url)
                            force_related.related_resources.append({
                                'url': anchor_href,
                                'label': anchor_text
                                })
                        elif force_subordinate is not None:
                            if dump_it:
                                print u'              FORCE subordinate: "{0}" ({1}) to "{2}" ({3})'.format(anchor_text, anchor_href, force_subordinate.title, force_subordinate.url)
                            force_subordinate.subordinate_resources.append({
                                'url': anchor_href,
                                'label': anchor_text
                                })
                        elif anchor_text_lower in SUBORDINATE_FLAGS:
                            if dump_it:
                                print u'              subordinate to "{0}" ({1})'.format(resources[-2].title, resources[-2].url)
                            if prev_superior is not None:
                                pass
                            else:
                                prev_superior = resources[-2]
                            prev_superior.subordinate_resources.append({
                                'url': anchor_href,
                                'label': anchor_text
                                })
                            prev_relator = None
                        elif anchor_text_lower in RELATED_FLAGS:
                            if dump_it:
                                print u'              related to "{0}" ({1})'.format(resources[-2].title, resources[-2].url)
                            if prev_relator is not None:
                                pass
                            else:
                                prev_relator = resources[-2]
                            prev_relator.related_resources.append({
                                'url': anchor_href,
                                'label': anchor_text
                                })
                            prev_superior = None
                        elif (anchor_text_lower[:5] == u'vol. ' 
                            or anchor_text_lower[:4] == u'no. '
                            or anchor_text_lower[:7] == u'volume '
                            or RX_NUMERICISH.match(anchor_text_lower) is not None
                            or anchor_in_blockquote
                            or anchor_in_issue_element):
                            if (prev_superior is None 
                                or (anchor_in_blockquote and not prev_blockquote)
                                or (anchor_in_issue_element and not prev_issue_element)):
                                    prev_superior = resources[-2]
                            resource.title_extended = u': '.join((prev_superior.title, resource.title))
                            if dump_it:
                                print u'              extended title: "{0}"'.format(resource.title_extended)
                            prev_superior.subordinate_resources.append({
                                'url': anchor_href,
                                'label': resource.title
                                })
                            if dump_it:
                                print u'              subordinate to "{0}" ({1})'.format(prev_superior.title, prev_superior.url)
                        else:
                            prev_superior = None
                            prev_relator = None

                    # set provenance
                    resource_fields = sorted([k for k in resource.__dict__.keys() if '_' != k[0]])
                    resource.set_provenance(self.id, 'citesAsDataSource', updated, resource_fields)
                    resource.set_provenance(self.url, 'citesAsMetadataDocument', updated)

                    # detect conditions that will force treatment of subsequent anchors as
                    # subordinate or related resources
                    if self.url not in NO_FORCING:
                        if anchor_text_lower in FORCE_AS_RELATED_AFTER or anchor_href in FORCE_AS_RELATED_AFTER:
                            force_subordinate = None
                            force_related = resource
                        if anchor_text_lower in FORCE_AS_SUBORDINATE_AFTER or anchor_href in FORCE_AS_SUBORDINATE_AFTER:
                            try:
                                force_subordinate = resource
                            except IndexError:
                                logger.warning('failed to set force_subordinate at {0} in {1}'.format(anchor_href, self.url))
                            else:
                                force_related = None

                    #if dump_it:
                    #    pprint.pprint(resource.__dict__)
                prev_blockquote = anchor_in_blockquote
                prev_issue_element = anchor_in_issue_element

        elif len(domains) == 1 and len(unique_urls) > 1:
            logger.warning('aggregator detected, but ignored: {0}'.format(domains[0]))
        elif len(domains) == 1:
            # this is an article about a single resource
            urls=[url for url in urls if domains[0] in url]
            resource = self._parse_resource(
                domain=domains[0], 
                url=[url for url in urls if domains[0] in url][0],
                title=self._parse_title(self.title), 
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

        def deduplicate(raws):
            prev_line = u''
            cookeds = u''
            lines = raws.split(u'\n')
            lines = [normalize_space(line) for line in lines if normalize_space(line) != u'']
            for line in lines:
                canary = RX_CANARY.sub(u'', line.lower())
                if canary != prev_line:
                    cookeds = u' '.join((cookeds, line))
                    prev_line = canary
            return normalize_space(cookeds)

        desc_node = content_soup
        try:
            desc_lines = desc_node.get_text('\n')
        except AttributeError:
            desc_text = u''
        else:
            desc_text = deduplicate(desc_lines)
        if desc_text == u'':
            try:
                desc_node = content_soup.find_all('blockquote')[1]
            except IndexError:
                desc_text = u''
            else:
                desc_text = deduplicate(desc_node.get_text('\n'))
            if desc_text == u'':
                first_anchor = content_soup.a
                try:
                    nodes = first_anchor.next_siblings
                except AttributeError:
                    desc_text == u''
                else:
                    nodes = [node for node in nodes if node.name not in ['a', 'h1', 'h2', 'h3', 'h4', 'hr']]
                    html = u'<div>\n' + first_anchor.text + u':\n' + u'\n'.join([unicode(node) for node in nodes]) + u'</div>'
                    soup = BeautifulSoup(html)
                    desc_text = deduplicate(soup.get_text('\n'))
                    if desc_text == u'':
                        desc_text = deduplicate(content_soup.get_text('\n'))
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
        r.description = self._parse_description(content_soup)
        r.identifiers = self._parse_identifiers(r.description)
        r.keywords = self._parse_tags(self.title, title, self.categories, r.description) 
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

    def _parse_title(self, title):
        """Parse resource title from post title."""

        if u':' in title:
            colon_prefix = title.split(u':')[0].lower()
            if colon_prefix in COLON_PREFIXES.keys() and (COLON_PREFIXES[colon_prefix])[1] == 'yes':
                title = u':'.join(title.split(u':')[1:])
        return clean_title(title)




