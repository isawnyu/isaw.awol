#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse HTML content for resources from the OI content aggregator.

This module defines the following classes:

 * AwolPerseeParser: parse AWOL blog post content for resources
"""

import logging
import sys

from isaw.awol.parse.awol_parse_domain import AwolDomainParser
from isaw.awol.parse.awol_parse import domain_from_url

NEVER_PRIMARY_DOMAINS = [
    'www.oxbowbooks.com',
]
MY_SKIP_URLS = [
    'http://oi.uchicago.edu/news/',
]

class Parser(AwolDomainParser):
    """Extract data from an AWOL blog post about content on OI."""

    def __init__(self):
        self.domain = 'oi.uchicago.edu'
        AwolDomainParser.__init__(self)
        
    def _get_primary_anchor(self):
        """Deal with OI peculiarities."""
        for pa in AwolDomainParser._get_anchors(self):
            url = pa.get('href')
            domain = domain_from_url(url)
            if domain not in NEVER_PRIMARY_DOMAINS and url not in MY_SKIP_URLS:
                break
        return pa
