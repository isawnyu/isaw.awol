#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Normalize space in a string.
"""

import logging
import re
import sys

from isaw.awol.normalize_space import normalize_space

RX_CANARY = re.compile(r'[\.,:!\"“„\;\-\s]+', re.IGNORECASE)
RX_DASHES = re.compile(r'[‒–—-]+')

def clean_string(raw):
    prepped = normalize_space(raw)
    if prepped == u'':
        return u''
    chopped = prepped.split(u'.')
    if len(chopped) > 2:
        cooked = u'.'.join(tuple(chopped[:2]))
        i = 2
        while i < len(chopped) and len(cooked) < 40:
            cooked = cooked + u'.' + chopped[i]
            i = i + 1
    else:
        cooked = prepped
    junk = [
        (u'(', u')'),
        (u'[', u']'),
        (u'{', u'}'),
        (u'"', u'"'),
        (u"'", u"'"),
        (u'<', u'>'),
        (u'«', u'»'),
        (u'‘', u'’'),
        (u'‚', u'‛'),
        (u'“', u'”'),
        (u'‟', u'„'),
        (u'‹', u'›'),
        (u'〟', u'＂'),
        (u'\\'),
        (u'/'),
        (u'|'),
        (u','),
        (u';'),
        (u'-'),
        (u'.'),
        (u'_'),
    ]
    for j in junk:
        if len(j) == 2:
            cooked = cooked[1:-1] if cooked[0] == j[0] and cooked[-1] == j[1] else cooked
        else:
            cooked = cooked[1:] if cooked[0] == j[0] else cooked
            cooked = cooked[:-1] if cooked[-1] == j[0] else cooked
        if cooked[0:4] == u'and ':
            cooked = cooked[4:]
        cooked = cooked.strip()
    return cooked

def deduplicate_lines(raws):
    prev_line = u''
    cookeds = u''
    lines = raws.split(u'\n')
    lines = [normalize_space(line) for line in lines if normalize_space(line) != u'']
    for line in lines:
        canary = RX_CANARY.sub(u'', line.lower())
        if canary != prev_line:
            cookeds = u' '.join((cookeds, line))
            prev_line = canary
    return normalize_space(cookeds)

def purify_html(raw):
    """Out vile jelly!"""
    cooked = RX_DASHES.sub(u'-', raw)   # regularize dashes
    cooked = cooked.replace(u'\u00A0', u' ')  # get rid of non-breaking spaces
    cooked = cooked.replace(u'N\xb0', u'No.')   # extirpate superscript 'o' in volume numbers
    return cooked
