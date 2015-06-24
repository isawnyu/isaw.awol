#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define classes and methods for working with resources extracted from blog.

This module defines the following classes:

 * Resource: Extracts and represents key information about a web resource.
"""

import copy
import datetime
import json
import logging
import sys

from wikidata_suggest import suggest

PROVENANCE_VERBS = {
    'citesAsMetadataDocument': 'http://purl.org/spar/cito/citesAsMetadataDocument',
    'citesAsDataSource': 'http://purl.org/spar/cito/citesAsDataSource',
    'hasWorkflowMotif': 'http://purl.org/net/wf-motifs#hasWorkflowMotif',
    'Combine': 'http://purl.org/net/wf-motifs#Combine'
}

class Resource:
    """Extract and represent key information about a web resource."""

    def __init__(self):
        """Set all attributes to default values."""

        self.authors = []
        self.description = None
        self.domain = None
        self.subordinate_resources = []
        self.identifiers = {}
        self.is_part_of = None
        self.keywords = []
        self.language = None
        self.provenance = []
        self.related_resources = []
        self.title = None
        self.url = None
        self.volume = None
        self.year = None
        self.zotero_id = None

    def json_dumps(self, formatted=False):
        """Dump resource to JSON as a UTF-8 string."""
        if formatted:
            return json.dumps(self.__dict__, indent=4, sort_keys=True)
        else:
            return json.dumps(self.__dict__)

    def json_dump(self, filename, formatted=False):
        """Dump resource as JSON to a file."""
        dump = self.__dict__.copy()
        dump['related_resources'] = [r.__dict__.copy() for r in self.related_resources]
        dump['subordinate_resources'] = [r.__dict__.copy() for r in self.subordinate_resources]
        with open(filename, 'w') as f:
            if formatted:
                json.dump(dump, f, indent=4, sort_keys=True)
            else:
                json.dump(dump, f)
        del dump

    def json_loads(self, s):
        """Parse resource from a UTF-8 JSON string."""
        self.__dict__ = json.loads(s)

    def json_load(self, filename):
        """Parse resource from a json file."""
        with open(filename, 'r') as f:
            self.__dict__ = json.load(f)
        related = []
        for d in self.related_resources:
            r = Resource()
            for k,v in d.items():
                setattr(r, k, v)
            related.append(r)
        self.related_resources = related
        subordinate = []
        for d in self.subordinate_resources:
            r = Resource()
            for k,v in d.items():
                setattr(r, k, v)
            related.append(r)
        self.subordinate_resources = subordinate

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

    def wikidata_suggest(self, resource_title):
        wikidata = suggest(resource_title)
        if wikidata:
            return wikidata['id']
        else:
            return None

    def set_provenance(self, object, verb='citesAsMetadataDocument', object_date=None, fields=None):
        """Add an entry to the provenance list."""

        d = {
            'term': PROVENANCE_VERBS[verb],
            'when': datetime.datetime.utcnow().isoformat(),
            'resource': object
        }
        if object_date is not None:
            d['resource_date'] = object_date
        if fields is not None:
            if fields is list:
                d['fields'] = fields
            else:
                d['fields'] = list(fields)

        self.provenance.append(d)

    def __str__(self):
        
        try:
            title_extended = self.title_extended
        except AttributeError:
            title_extended = None

        s = u"""
        title: {title}
        authors: {authors}
        extended title: {titleextended}
        url: {url}
        description: {description}
        language: {language}
        domain: {domain}
        keywords: {keywords}
        identifiers: {identifiers}
        part of: {partof}
        volume: {volume}
        year: {year}
        related resources: {related}
        subordinate resources: {subordinate}
        provenance: {provenance}
        """
        s = s.format(
            title = self.title,
            authors = repr(self.authors),
            titleextended = title_extended,
            url = self.url,
            description = self.description,
            language = self.language,
            domain = self.domain,
            keywords = repr(self.keywords),
            identifiers = repr(self.identifiers), 
            partof = repr(self.is_part_of),
            volume = self.volume,
            year = self.year,
            provenance = repr(self.provenance), 
            subordinate = [r.title for r in self.subordinate_resources],
            related = [r.title for r in self.related_resources])
        return s

def merge(r1, r2):
    """Merge two resources into oneness."""

    r3 = Resource()
    modified_fields = []
    k1 = r1.__dict__.keys()
    k2 = r2.__dict__.keys()
    all_keys = list(set(k1 + k2))
    for k in all_keys:
        modified = False
        v3 = None
        try:
            v1 = copy.deepcopy(r1.__dict__[k])
        except KeyError:
            v1 = None
        try:
            v2 = copy.deepcopy(r2.__dict__[k])
        except KeyError:
            v2 = None

        if k in ['url',]:
            if v1 != v2:
                raise Exce(u'cannot merge two resources in which the {0} field differs: "{1}" vs. "{2}"'.format(k, v1, v2))
            else:
                v3 = v1
        else:
            modified = True
            if v1 is None and v2 is None:
                v3 = None
                modified = False
            # prefer some data over no data
            elif v1 is None and v2 is not None:
                v3 = v2
            elif v1 is not None and v2 is None:
                v3 = v1
            elif k in ['volume', 'year', 'is_part_of', 'zotero_id']:
                if v1 == v2:
                    v3 = v1
                    modified = False
                else:
                    print('\n\n\n##########\nv1:')
                    print(unicode(v1))
                    print('\n\n##########\nv2:')
                    print(unicode(v2))
                    raise Exception(u'cannot merge two resources in which the {0} field differs: "{1}" vs. "{2}"'.format(k, v1, v2))
            elif k == 'language':
                if v1[0] == v2[0]:
                    v3 = copy.deepcopy(v1)
                    if v1[1] != v2[1]:
                        v3[1] = min(v1[1], v2[1])
                    else:
                        modified = False
                else:
                    v3 = None   # if parsers didn't agree, then don't assert anything
            elif k == 'identifiers':
                pass
            elif k in ['subordinate_resources', 'related_resources']:
                if len(v1) == 0 and len(v2) == 0:
                    modified = False
                v3 = v1 + v2
                urls = list(set([r.url for r in v3]))
                resources = []
                for url in urls:
                    resources.append([r for r in v3 if r.url == url][0])
                v3 = resources
            elif k == 'provenance':
                modified = False
                v3 = v1 + v2
            elif type(v1) == list:
                v3 = set(v1 + v2)
                if v3 == set(v1) and v3 == set(v2):
                    modified = False
                v3 = list(v3)
            elif type(v1) in [unicode, str]:
                if len(v1) == 0 and len(v2) == 0:
                    modified = False
                    v3 = v1
                elif v1 == v2:
                    modified = False
                    v3 = v1
                # if one contains the other, prefer the container
                elif v1 in v2:
                    v3 = v2
                elif v2 in v1:
                    v3 = v1
                # prefer the longer of the two
                elif len(v1) > len(v2):
                    v3 = v1
                else:
                    v3 = v2
            else:
                raise Exception
        r3.__dict__[k] = v3
        if modified:
            modified_fields.append(k)
    r3.set_provenance('http://purl.org/net/wf-motifs#Combine', 'hasWorkflowMotif', fields=modified_fields)
    return r3


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
    
