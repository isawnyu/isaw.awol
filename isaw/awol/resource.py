#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define classes and methods for working with resources extracted from blog.

This module defines the following classes:

 * Resource: Extracts and represents key information about a web resource.
"""

import datetime
import json
import logging
import sys

from wikidata_suggest import suggest


class Resource:
    """Extract and represent key information about a web resource."""

    def __init__(self):
        """Set all attributes to default values."""

        self.history = []
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

    def json_dumps(self, formatted=False):
        """Dump resource to JSON as a UTF-8 string."""
        if formatted:
            return json.dumps(self.__dict__, indent=4, sort_keys=True)
        else:
            return json.dumps(self.__dict__)

    def json_dump(self, filename, formatted=False):
        """Dump resource as JSON to a file."""
        with open(filename, 'w') as f:
            if formatted:
                json.dump(self.__dict__, f, indent=4, sort_keys=True)
            else:
                json.dump(self.__dict__, f)

    def json_loads(self, s):
        """Parse resource from a UTF-8 JSON string."""
        self.__dict__ = json.loads(s)

    def json_load(self, filename):
        """Parse resource from a json file."""
        with open(filename, 'r') as f:
            self.__dict__ = json.load(f)

    def zotero_add(self, zot, creds, extras={}):
        """Upload as a record to Zotero."""

        logger = logging.getLogger(sys._getframe().f_code.co_name)

        try:
            issn = self.identifiers['issn']
        except KeyError:
            if 'journal' in self.keywords:
                zot_type = 'journalArticle'
            else:
                zot_type = 'webpage'
        else:
            zot_type = 'journalArticle'
        template = zot.item_template(zot_type)
        template['abstractNote'] = self.description
        if 'issn' in locals():
            template['issn'] = issn
        template['tags'] = self.keywords
        template['extra'] = ', '.join([':'.join((k,'"{0}"'.format(v))) for k,v in extras.iteritems()])
        try:
            template['language'] = self.language[0]
        except TypeError:
            pass
        template['title'] = self.title
        template['url'] = self.url
        resp = zot.create_items([template])
        try:
            zot_id = resp[u'success'][u'0']
            logger.debug("zot_id: {0}".format(zot_id))
        except KeyError:
            logger.error('Zotero upload appears to have failed with {0}'.format(repr(resp)))
            raise
        else:
            self.zotero_id = {
                'libraryType': creds['libraryType'],
                'libraryID': creds['libraryID'],
                'itemID': zot_id
            }
            logger.debug(repr(self.zotero_id))
            self.append_event(
                'Successfully uploaded to Zotero with {0}'.format(repr(self.zotero_id)))

    def append_event(self, msg):
        """Append an event record to resource history."""
        event = '{0}: {1} ({2})'.format(
            datetime.datetime.utcnow().isoformat(), 
            msg,
            scriptinfo()['source'])
        self.history.append(event)

    def wikidata_suggest(self, resource_title):
        wikidata = suggest(resource_title)
        if wikidata:
            return wikidata['id']
        else:
            return None



    def __str__(self):
        
        s = u"""
        title: {title}
        url: {url}
        description : {description}
        language: {language}
        domain: {domain}
        keywords: {keywords}
        identifiers: {identifiers}
        related resources: NOT IMPLEMENTED
        subordinate resources: NOT IMPLEMENTED
        history: {history}
        """
        s = s.format(
            title = self.title,
            url = self.url,
            description = self.description,
            language = self.language,
            domain = self.domain,
            keywords = repr(self.keywords),
            identifiers = repr(self.identifiers), 
            history = repr(self.history))

        return s


def scriptinfo():
    '''
    Returns a dictionary with information about the running top level Python
    script:
    ---------------------------------------------------------------------------
    dir:    directory containing script or compiled executable
    name:   name of script or executable
    source: name of source code file
    ---------------------------------------------------------------------------
    "name" and "source" are identical if and only if running interpreted code.
    When running code compiled by py2exe or cx_freeze, "source" contains
    the name of the originating Python script.
    If compiled by PyInstaller, "source" contains no meaningful information.
    '''

    import os, sys, inspect
    #---------------------------------------------------------------------------
    # scan through call stack for caller information
    #---------------------------------------------------------------------------
    for teil in inspect.stack():
        # skip system calls
        if teil[1].startswith("<"):
            continue
        if teil[1].upper().startswith(sys.exec_prefix.upper()):
            continue
        trc = teil[1]
        
    # trc contains highest level calling script name
    # check if we have been compiled
    if getattr(sys, 'frozen', False):
        scriptdir, scriptname = os.path.split(sys.executable)
        return {"dir": scriptdir,
                "name": scriptname,
                "source": trc}

    # from here on, we are in the interpreted case
    scriptdir, trc = os.path.split(trc)
    # if trc did not contain directory information,
    # the current working directory is what we need
    if not scriptdir:
        scriptdir = os.getcwd()

    scr_dict ={"name": trc,
               "source": trc,
               "dir": scriptdir}
    return scr_dict
    
