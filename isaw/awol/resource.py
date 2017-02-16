#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define classes and methods for working with resources extracted from blog.

This module defines the following classes:

 * Resource: Extracts and represents key information about a web resource.
"""

import copy
import datetime
import io
import json
import logging
import pprint
import sys

from wikidata_suggest import suggest

PROVENANCE_VERBS = {
    'citesAsMetadataDocument': 'http://purl.org/spar/cito/citesAsMetadataDocument',
    'citesAsDataSource': 'http://purl.org/spar/cito/citesAsDataSource',
    'hasWorkflowMotif': 'http://purl.org/net/wf-motifs#hasWorkflowMotif',
    'Combine': 'http://purl.org/net/wf-motifs#Combine'
}

class Resource:
    """Store, manipulate, and export data about a single information resource."""

    def __init__(self):
        """Set all attributes to default values."""

        self.authors = []
        self.contributors = []
        self.description = None
        self.domain = None
        self.editors = []
        self.end_date = None
        self.extent = None
        self.form = None
        self.frequency = None
        self.identifiers = {}
        self.is_part_of = None
        self.issue = None
        self.issuance = None
        self.issued_dates = None
        self.keywords = []
        self.languages = []
        self.places = []
        self.provenance = []
        self.publishers = []
        self.related_resources = []
        self.responsibility = []
        self.start_date = None
        self.subordinate_resources = []
        self.title = None
        self.title_alternates = []
        self.title_extended = None
        self.type = None
        self.url = None
        self.url_alternates = []
        self.volume = None
        self.year = None
        self.zenon_id = None
        self.zotero_id = None

    def json_dumps(self, formatted=False):
        """Dump resource to JSON as a UTF-8 string."""

        logger = logging.getLogger(sys._getframe().f_code.co_name)
        dump = self.__dict__.copy()
        for k,v in dump.iteritems():
            logger.debug("{0} ({1})".format(k, type(v)))
        if formatted:
            return json.dumps(dump, indent=4, sort_keys=True, ensure_ascii=False).encode('utf8')
        else:
            return json.dumps(dump, ensure_ascii=False).encode('utf8')

    def json_dump(self, filename, formatted=False):
        """Dump resource as JSON to a UTF-8 encoded file."""
        dumps = self.json_dumps(formatted) # get utf8-encoded JSON dump
        with open(filename, 'w') as f:
            f.write(dumps)
        del dumps


    def json_loads(self, s):
        """Parse resource from a UTF-8 JSON string."""
        self.__dict__ = json.loads(unicode(s))

    def json_load(self, filename):
        """Parse resource from a json file."""
        with io.open(filename, 'r', encoding='utf8') as f:
            self.__dict__ = json.load(f)

    def package(self):
        """Return a summary package of resource information."""
        pkg = {}
        try:
            title = self.extended_title
        except AttributeError:
            title = self.title
        pkg['title_full'] = title
        pkg['url'] = self.url
        if title != self.title:
            pkg['title'] = self.title
        return pkg


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
        return pprint.pformat(self.__dict__, indent=4, width=120)


def merge(r1, r2):
    """Merge two resources into oneness."""
    logger = logging.getLogger(sys._getframe().f_code.co_name)
    r3 = Resource()
    modified_fields = []
    k1 = r1.__dict__.keys()
    k2 = r2.__dict__.keys()
    all_keys = list(set(k1 + k2))
    domain = r1.domain
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
                if v1.startswith(v2):
                    v3 = v2
                    r3.__dict__['url_alternates'].append(v1)
                elif v2.startswith(v1):
                    v3 = v1
                    r3.__dict__['url_alternates'].append(v2)
                else:
                    protocol1, path1 = v1.split('://')
                    protocol2, path2 = v2.split('://')
                    if path1 == path2 and (protocol1 == 'https' or protocol2 == 'https'):
                        v3 = 'https://' + path1
                    else:
                        raise ValueError(u'could not reconcile url mismatch in merge: {1} vs. {2}'.format(k, v1, v2))
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
            elif k == 'is_part_of':
                if v1 == v2:
                    v3 = v1
                    modified = False
                else:
                    if domain in v1['url']:
                        v3 = v1
                    elif domain in v2['url']:
                        v3 = v2
                    elif 'issn' in v1.keys() and not('issn' in v2.keys()):
                        v3 = v1
                    elif 'issn' in v2.keys() and not('issn' in v1.keys()):
                        v3 = v2
                    else:
                        v3 = None
            elif k in ['volume', 'year', 'zenon_id', 'issue', 'zotero_id']:
                if v1 == v2:
                    v3 = v1
                    modified = False
                elif v1 is None and v1 is not None:
                    v3 = v2
                elif v1 is not None and v2 is None:
                    v3 = v1
                else:
                    raise ValueError(u'cannot merge two resources in which the {0} field differs: "{1}" vs. "{2}"'.format(k, v1, v2))
            elif k == 'languages':
                if len(v1) == 0 and len(v2) > 0:
                    v3 = copy.deepcopy(v2)
                elif len(v1) > 0 and len(v2) == 0:
                    v3 = copy.deepcopy(v1)
                elif len(v1) > 0 and len(v2) > 0:
                    v3 = list(set(v1 + v2))
                else:
                    v3 = []
            elif k == 'identifiers':
                if len(v1) == 0 and len(v2) > 0:
                    v3 = copy.deepcopy(v2)
                elif len(v1) > 0 and len(v2) == 0:
                    v3 = copy.deepcopy(v1)
                elif len(v1) > 0 and len(v2) > 0:
                    v3 = {}
                    idfams = list(set(v1.keys() + v2.keys()))
                    for idfam in idfams:
                        thisval1 = None
                        thisval2 = None
                        try:
                            thisval1 = v1[idfam]
                        except KeyError:
                            pass
                        try:
                            thisval2 = v2[idfam]
                        except KeyError:
                            pass
                        if type(thisval1) == list or type(thisval2) == list:
                            v3[idfam] = []
                            if thisval1 is not None:
                                v3[idfam].extend(thisval1)
                            if thisval2 is not None:
                                v3[idfam].extend(thisval2)
                            v3[idfam] = list(set(v3[idfam]))
                        elif type(thisval1) == dict or type(thisval2) == dict:
                            if thisval1 is None and thisval2 is not None:
                                v3 = copy.deepcopy(v2)
                            elif thisval1 is not None and thisval2 is None:
                                v3 = copy.deepcopy(v1)
                            else:
                                v3[idfam] = {}
                                idtypes = list(set(thisval1.keys() + thisval2.keys()))
                                for idtype in idtypes:
                                    thissubval1 = None
                                    thissubval2 = None
                                    try:
                                        thissubval1 = v1[idfam][idtype]
                                    except KeyError:
                                        pass
                                    try:
                                        thissubval2 = v2[idfam][idtype]
                                    except KeyError:
                                        pass
                                    v3[idfam][idtype] = []
                                    if thissubval1 is not None:
                                        v3[idfam][idtype].extend(thissubval1)
                                    if thissubval2 is not None:
                                        v3[idfam][idtype].extend(thissubval2)
                                    v3[idfam][idtype] = list(set(v3[idfam][idtype]))
                else:
                    v3 = {}

            elif k in ['subordinate_resources', 'related_resources']:
                if len(v1) == 0 and len(v2) == 0:
                    modified = False
                v3 = v1 + v2
                seen = []
                for v3_child in v3:
                    if v3_child['url'] in seen:
                        del(v3_child)
                    else:
                        seen.append(v3_child['url'])
                del(seen)
            elif k == 'provenance':
                modified = False
                v3 = v1 + v2
            elif type(v1) == list and type(v2) == list:
                if len(v1) == 0 and len(v2) == 0:
                    modified = False
                    v3 = []
                elif len(v1) == 0 and len(v2) > 0:
                    v3 = v2
                elif len(v1) > 0 and len(v2) == 0:
                    v3 = v1
                else:
                    v3 = list(set(v1 + v2))
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

