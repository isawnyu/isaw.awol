#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse HTML content for resources from the Persée content aggregator.

This module defines the following classes:

 * AwolPerseeParser: parse AWOL blog post content for resources
"""

import logging
import sys

from isaw.awol.parse.awol_parse_domain import AwolDomainParser

class Parser(AwolDomainParser):
    """Extract data from an AWOL blog post about content on ASCSA."""

    def __init__(self):
        self.domain = 'www.ascsa.edu.gr'
        AwolDomainParser.__init__(self)


    #def _get_primary_anchor(self):
    #    """Deal with ASCSA peculiarities."""
    #    logger = logging.getLogger(sys._getframe().f_code.co_name)
    #    pa = AwolDomainParser._get_primary_anchor(self)
    #    if pa.get('href') == 'http://www.ascsa.edu.gr/index.php/news/newsDetails/school-newsletter-now-online':
    #        for pa in self.content['anchors']:
    #            if pa.get('href') == 'http://www.ascsa.edu.gr/index.php/publications/newsletter/':
    #                return pa
    #    return pa

    def reset(self, content_soup=None):
        AwolDomainParser.reset(self, content_soup)
        self.skip_urls.append('http://www.ascsa.edu.gr/index.php/news/newsDetails/school-newsletter-now-online')


        