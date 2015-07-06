#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse HTML content for resources from the OI content aggregator.

This module defines the following classes:

 * AwolPerseeParser: parse AWOL blog post content for resources
"""

import logging
import sys

from bs4.element import NavigableString

from isaw.awol import resource
from isaw.awol.normalize_space import normalize_space
from isaw.awol.parse.awol_parse import domain_from_url
from isaw.awol.clean_string import clean_string
from isaw.awol.parse.awol_parse_domain import AwolDomainParser
from isaw.awol.parse.awol_parse import domain_from_url


class Parser(AwolDomainParser):
    """Extract data from an AWOL blog post about content on Othes and Vienna."""

    def __init__(self):
        self.domain = 'othes.univie.ac.at'
        AwolDomainParser.__init__(self)
        
    def _get_resources(self, article):
        """Override basic resource extraction."""
        if article.url == u'http://ancientworldonline.blogspot.com/2015/05/universitat-wien-theses-and.html':
            resources = []
            relatives = []
            soup = article.soup
            people = soup.find_all('span', 'person_name')
            for person in people:
                a = person.find_next_sibling('a')
                foo = a.find_next_sibling('br').next_sibling
                try:
                    bar = a.find_next_sibling('span', 'person_name').previous_sibling
                except AttributeError:
                    bar = None
                description = u''
                while foo is not None and foo != bar:
                    if type(foo) == NavigableString:
                        description += u'{0} '.format(clean_string(unicode(foo)))
                    else:
                        description += u'{0} '.format(clean_string(foo.get_text()))
                    foo = foo.next_sibling
                if description.strip() == u'':
                    description = None
                else:
                    description = normalize_space(u'. '.join([chunk.strip() for chunk in description.split(u'.')]))
                foosball = a.find_all_previous('a')
                foosball = [f for f in foosball if 'subjects' in f.get('href')]
                if len(foosball) > 0:
                    f = foosball[0]
                    params = {
                        'domain': domain_from_url(f.get('href')),
                        'keywords': self._parse_keywords(resource_title=clean_string(f.get_text())),
                        'languages': self._get_language(clean_string(f.get_text())),
                        'title': clean_string(f.get_text()),                        
                        'url': f.get('href')
                    }
                    rr = self._make_resource(**params)
                    self._set_provenance(rr, article)
                    relatives.append(rr)
                params = {
                    'authors': [clean_string(person.get_text()), ],
                    'description': description,
                    'domain': domain_from_url(a.get('href')),
                    'keywords': self._parse_keywords(post_title=rr.title, resource_title=clean_string(a.get_text())),
                    'languages': self._get_language(clean_string(a.get_text())),
                    'title': clean_string(a.get_text()),
                    'url': a.get('href'),
                    'year': clean_string(unicode(person.next_sibling)),
                }
                resource = self._make_resource(**params)

                resource.related_resources.append(rr.package())
                self._set_provenance(resource, article)
                resources.append(resource)
            relative_urls = list(set([r.url for r in relatives]))
            unique_relatives = []
            for rurl in relative_urls:
                unique_relatives.append([r for r in relatives if r.url == rurl][0])
            return resources + unique_relatives
        else:
            return AwolDomainParser._get_resources(self, article)
