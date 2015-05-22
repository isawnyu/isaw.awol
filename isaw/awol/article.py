#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define classes and methods for working with AWOL blog articles.

This module defines the following classes:
 
 * Article: represents key information about the article.
"""

import logging
import re
import sys

from bs4 import BeautifulSoup
from lxml import etree as exml
import pkg_resources
import unicodecsv as csv

from isaw.awol.resource import Resource

DOMAINS_TO_IGNORE = [
    'draft.blogger.com'
]
DOMAINS_NOT_PRIMARY = [
    'ancientworldonline.blogspot.com'
]
RX_MATCH_DOMAIN = re.compile('^https?:\/\/([^/#]+)')

# Build a dictionary of format {<column prefix>:<list of cols 2,3 and 4>}
colon_prefix_csv = pkg_resources.resource_stream('isaw.awol', 'awol_colon_prefixes.csv')
dreader = csv.DictReader(
    colon_prefix_csv,
    fieldnames = [
        'col_pre', 
        'omit_post', 
        'strip_title', 
        'mul_res'
    ], 
    delimiter = ',', 
    quotechar = '"')
COLUMN_PREFIXES = dict()
for row in dreader:
    COLUMN_PREFIXES.update({
        row['col_pre']:
            [
                row['omit_post'], 
                row['strip_title'], 
                row['mul_res']
            ]
    })
del dreader

class Article():
    """Represent all data that is important about an AWOL blog article."""

    def __init__(self, file_name):
        """Verify and open file."""
        with open(file_name, 'r') as file_object:
            self.doc = exml.parse(file_object)
        self.root = self.doc.getroot()

    def parse(self):
        """Parse desired components out of the file.

        Method looks for the following components and saves their values as
        attributes of the object:

            * id (string): unique identifier for the blog post
            * title (unicode): title of the blog post
            * url (unicode): url of the blog post
            * categories (list of unicode strings): categories assigned to
              the blog post
            * content (string): raw content of the blog post
            * resources (list of resource objects): information about each
              web resource found mentioned in the article content

        """

        root = self.root
        self.id = root.find('{http://www.w3.org/2005/Atom}id').text
        self.title = unicode(root.find('{http://www.w3.org/2005/Atom}title').text)
        self.url = unicode(root.xpath("//*[local-name()='link' and @rel='alternate']")[0].get('href'))
        self.categories = [{'vocabulary' : c.get('scheme'), 'term' : c.get('term')} for c in root.findall('{http://www.w3.org/2005/Atom}category')]
        self.content = root.find('{http://www.w3.org/2005/Atom}content').text
        self.resources = self.get_resources()

    def get_resources(self):
        """Identify all the resources mentioned in this article."""

        logger = logging.getLogger(sys._getframe().f_code.co_name)
        resources = []
        soup = BeautifulSoup(self.content)
        self.soup = soup
        anchors = [a for a in soup.find_all('a')]
        urls = [a.get('href') for a in anchors]
        for url in urls:
            m = RX_MATCH_DOMAIN.match(url)
            logger.debug('url "{0}" yields domain "{1}"'.format(url, m.group(1)))
        domains = list(set([RX_MATCH_DOMAIN.match(url).group(1) for url in urls]))
        domains = [d for d in domains 
            if d not in DOMAINS_TO_IGNORE 
            and d not in DOMAINS_NOT_PRIMARY]
        if len(domains) == 1:
            # this is an article about a single resource
            resource_title = self._parse_rtitle_from_ptitle()
            resource = self._extract_single_resource(
                domains[0], 
                [url for url in urls if domains[0] in url][0],
                resource_title )
            resources.append(resource)
        elif len(domains) > 1:
            # this article addresses multiple resources
            pass
        else:
            # this article addresses no external resource
            pass



        return resources

    def _extract_single_resource(self, domain, url, title=None):
        """Extract single resource from a blog post."""
        r = Resource()
        r.domain = domain
        r.url = url
        if title is not None:
            r.title = title
        return r

    def _parse_rtitle_from_ptitle(self):
        """Parse resource title from post title."""

        title = unicode(self.root.find('{http://www.w3.org/2005/Atom}title').text)
        #Check if record needs to be eliminated from zotero OR
        #resource title needs to be stripped
        if ':' in title:
            colon_prefix = title.split(':')[0]
            if colon_prefix in COLUMN_PREFIXES.keys() and (COLUMN_PREFIXES[colon_prefix])[1] == 'yes':
                return (title.split(':')[1]).strip()
        else:
            return title

    def __str__(self):
        """Print all data about the article."""

        return str(self.id+"|"+self.title+"|"+str(self.tags)+"|"+
            self.content+"|"+self.url+"|"+self.blogUrl+"|"+self.template+
            "|"+self.issn)



