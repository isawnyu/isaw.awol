#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse HTML content for multiple top-level resources (no subordinates).

This module defines the following classes:

 * Parser
"""

import logging
import sys

from isaw.awol.parse.awol_parse import AwolBaseParser
from isaw.awol.resource import merge

class Parser(AwolBaseParser):
    """Extract data from an AWOL blog post for multiple top-level resources."""

    def __init__(self):
        self.domain = 'generic-flat'
        AwolBaseParser.__init__(self)

    def _get_resources(self, article):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        subs = self._get_subordinate_resources(article)
        return subs

