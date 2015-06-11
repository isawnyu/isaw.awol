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
    """Extract data from an AWOL blog post about content on Persée."""

    def __init__(self):
        self.domain = 'www.persee.fr'
        AwolDomainParser.__init__(self)
        