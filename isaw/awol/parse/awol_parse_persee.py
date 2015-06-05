#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse HTML content for resources from the Persée content aggregator.

This module defines the following classes:

 * AwolPerseeParser: parse AWOL blog post content for resources
"""

from arglogger import arglogger
import logging
import sys

from isaw.awol.parse.awol_parse_aggregator import AwolAggregatorParser

class AwolPerseeParser(AwolAggregatorParser):
    """Extract data from an AWOL blog post about content on Persée."""

    def __init__():
        AwolAggregatorParser.__init__(self)
        