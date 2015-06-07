#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse HTML content for resources from a particular content domain.

This module defines the following classes:

 * AwolAggregatorParser: parse AWOL blog post content for resources
"""

import logging
import sys

from isaw.awol.parse.awol_parse import AwolBaseParser

class AwolDomainParser(AwolBaseParser):
    """Superclass: Extract data from an AWOL blog post about a content aggregator."""

    def __init__(self):
        AwolBaseParser.__init__(self)
