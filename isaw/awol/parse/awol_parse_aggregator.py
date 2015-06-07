#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse HTML content for resources from a content aggregator.

This module defines the following classes:

 * AwolAggregatorParser: parse AWOL blog post content for resources
"""

from arglogger import arglogger
import logging
import sys

from isaw.awol.parse.awol_parse import AwolParser

class AwolAggregatorParser(AwolParser):
    """Extract data from an AWOL blog post about a content aggregator."""

    def __init__():
        AwolParser.__init__(self)
