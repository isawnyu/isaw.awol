#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define classes and methods for working with resources extracted from blog.

This module defines the following classes:

 * Resource: Extracts and represents key information about a web resource.
"""

class Resource:
    """Extract and represent key information about a web resource."""

    def __init__(self):
        """Set all attributes to default values."""

        self.description = None
        self.domain = None
        self.subordinate_resources = []
        self.identifiers = {}
        self.keywords = []
        self.language = None
        self.related_resources = []
        self.title = None
        self.url = None




