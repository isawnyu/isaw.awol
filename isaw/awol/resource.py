#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define classes and methods for working with resources extracted from blog.

This module defines the following classes:

 * Resource: Extracts and represents key information about a web resource.
"""
import logging
import sys

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
        self.zotero_id = None

    def zotero_add(self, zot, creds, extras={}):
        """Upload as a record to Zotero."""

        logger = logging.getLogger(sys._getframe().f_code.co_name)

        try:
            issn = self.identifiers['issn']
        except KeyError:
            zot_type = 'webpage'
        else:
            zot_type = 'journalArticle'
        template = zot.item_template(zot_type)
        template['abstractNote'] = self.description
        if issn:
            template['issn'] = issn
        template['tags'] = self.keywords
        template['extra'] = ', '.join([':'.join((k,'"{0}"'.format(v))) for k,v in extras.iteritems()])
        template['language'] = self.language[0]
        template['title'] = self.title
        template['url'] = self.url
        resp = zot.create_items([template])
        try:
            zot_id = resp[u'success'][u'0']
        except KeyError
            logger.error('Zotero upload appears to have failed with {0}'.format(repr(resp)))
            raise
        else:
            self.zotero_id = zot_id


