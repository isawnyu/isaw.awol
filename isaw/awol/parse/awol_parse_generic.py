#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse HTML content for resources generically.

This module defines the following classes:

 * Parser
"""

import logging
import sys

from isaw.awol.parse.awol_parse import AwolBaseParser

class Parser(AwolBaseParser):
    """Extract data from an AWOL blog post agnostic to domain of resource."""

    def __init__(self):
        self.domain = 'generic'
        AwolBaseParser.__init__(self)

