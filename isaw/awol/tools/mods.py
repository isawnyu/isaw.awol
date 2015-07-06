#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
parse MODS
"""

import inspect
import sys

from lxml import etree
from lxml import objectify

def extract(mods):
    """Return a dictionary of everything we can parse out of MODS xml."""

    root = objectify.fromstring(mods)
    d = {}
    walk(d, root)
    return d

def walk(d, node):
    local_name = node.tag.split('}')[-1]
    try:
        func = getattr(sys.modules[__name__], local_name)
    except AttributeError:        
        for child in node.iterchildren():
            walk(d, child)
    else:
        func(d, node)

def append(d, k, v):
    try:
        d[k].append(v)
    except KeyError:
        d[k] = []
        d[k].append(v)

def title(d, node):
    append(d, 'title', node.text)

def name(d, node):
    try:
        role = node.role.roleTerm
    except AttributeError:
        role = 'name'
    name_type = node.get('type')
    try:
        parts = node.namePart
    except AttributeError:
        value = node.text
    else:        
        if name_type == 'personal':
            value = {}
            for part in parts:
                value[part.get('type')] = part.text
        else:
            parts = [part.text for part in parts]
            value = u', '.join(parts)
    append(d, role, value)

def typeOfResource(d, node):
    append(d, 'type', node.text.lower())

def publisher(d, node):
    append(d, 'publisher', node.text)

def frequency(d, node):
    append(d, 'frequency', node.text.lower())

def issuance(d, node):
    append(d, 'issuance', node.text)

def form(d, node):
    append(d, 'form', node.text.lower())

def extent(d, node):
    append(d, 'extent', node.text.lower())

def originInfo(d, node):
    places = []
    for place in node.place:
        places.append(place.placeTerm)
    parts = {}
    for place in places:
        if place.get('type') == 'text':
            try:
                parts['text'].append(place.text)
            except KeyError:
                parts['text'] = []
                parts['text'].append(place.text)
        elif place.get('type') == 'code':
            parts[place.get('authority')] = place.text
    parts['place_name'] = u', '.join(parts['text'])
    del(parts['text'])
    append(d, 'place', parts)
    children = [child for child in node.iterchildren() if node.tag.split('}')[-1] != 'place']
    for child in children:
        walk(d, child)

def recordCreationDate(d, node):
    append(d, 'record_creation_date', node.text)

def recordChangeDate(d, node):
    append(d, 'record_change_date', node.text)

def dateIssued(d, node):
    point = node.get('point')
    if point is None:
        key = 'issued_date'
    elif point == 'end' and node.text=='9999':
        key = None
    else:
        key = '{0}_date'.format(point)
    if key is not None:
        append(d, key, node.text)


def languageTerm(d, node):
    if node.get('type') == 'code':
        value = (node.text, node.get('authority'))
    else:
        value = node.text
    append(d, 'language', value)

def note(d, node):
    node_type = node.get('type')
    if node_type is not None:
        key = node_type.replace(' ', '_')
    else:
        key = 'note'
    append(d, key, node.text)

def identifier(d, node):
    node_type = node.get('type')
    if node_type is None:
        key = 'identifier'
    else:
        key = node_type
    append(d, key, node.text)

def url(d, node):
    append(d, 'url', node.text)








