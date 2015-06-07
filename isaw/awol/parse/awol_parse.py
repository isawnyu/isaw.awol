#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse HTML content for resources.

This module defines the following classes:

 * AwolParser: parse AWOL blog post content for resources
"""

import logging
import sys

IGNORE_DOMAINS = [
    'draft.blogger.com',
    'ancientworldonline.blogspot.com'
]

class AwolBaseParser:
    """Superclass: Extract data from an AWOL blog post."""

    def __init__(self):
        self.content = {}
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
            domains = [url.replace('http://', '').replace('https://', '').split('/')[0] for url in urls]
            domains = list(set(domains))
            domains = [domain for domain in domains if domain not in IGNORE_DOMAINS]
            c['domains'] = domains
        return c['domains']

    def reset(self, content_soup=None):

        c = self.content
        if content_soup is not None:
            c['soup'] = content_soup
        else:
            c['soup'] = None       
        c['domains'] = None
        