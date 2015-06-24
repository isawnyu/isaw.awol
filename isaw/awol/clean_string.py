#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Normalize space in a string.
"""

import logging
import re
import sys

from isaw.awol.normalize_space import normalize_space

RX_CANARY = re.compile(r'[\.,:!\"“„\;\-\s\']+', re.IGNORECASE)
RX_DASHES = re.compile(u'['
    + u'\u2010' # hyphen
    + u'\u2011' # non-breaking hyphen
    + u'\u2012' # figure dash
    + u'\u2013' # en dash
    + u'\u2014' # em dash
    + u'\u2015' # quotation dash
    + u'\u2e3a' # two-em dash
    + u'\u2e3b' # three-em dash
    + u']+')

def clean_string(raw):
    prepped = normalize_space(raw)
    if prepped == u'':
        return u''
    chopped = prepped.split(u'.')
    if len(chopped) > 2:
        cooked = u'.'.join(tuple(chopped[:2]))
        i = 2
        #while i < len(chopped) and len(cooked) < 40: why truncation?
        while i < len(chopped):
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
        try:
            if len(j) == 2:
                cooked = cooked[1:-1] if cooked[0] == j[0] and cooked[-1] == j[1] else cooked
            else:
                cooked = cooked[1:] if cooked[0] == j[0] else cooked
                cooked = cooked[:-1] if cooked[-1] == j[0] else cooked
            if cooked[0:4] == u'and ':
                cooked = cooked[4:]
        except IndexError:
            pass
        else:
            cooked = cooked.strip()
    return cooked

def deduplicate_sentences(raws):
    logger = logging.getLogger(sys._getframe().f_code.co_name)

    #logger.debug('deduplicate_sentences')
    sentences = raws.split(u'.')
    sentences = [normalize_space(sentence) for sentence in sentences if len(normalize_space(sentence))>0]
    good_sentences = []
    prev_sentence = u''
    for sentence in sentences:
        #logger.debug(u'  checking: "{0}"'.format(sentence))
        if prev_sentence == sentence:
            #logger.debug(u'    DUPLICATE: IGNORED')
            pass
        elif len(prev_sentence) > 0 and len(prev_sentence) < len(sentence):
            #logger.debug(u'    checking if "{0}" starts with "{1}"'.format(sentence, prev_sentence))
            foo = sentence[:len(prev_sentence)]
            #logger.debug(u'      foo: {0}'.format(foo))
            if foo == prev_sentence:
                #logger.debug('    STARTS WITH: PREVIOUS REMOVED')
                good_sentences = good_sentences[0:-1]
            good_sentences.append(sentence)
        else:
            #logger.debug(u'    KEEP!')
            good_sentences.append(sentence)
        prev_sentence = sentence
    #logger.debug('good sentences follow')
    #for sentence in good_sentences:
        #logger.debug(u'    {0}'.format(sentence))
    return u'. '.join(good_sentences)

def deduplicate_lines(raws):
    logger = logging.getLogger(sys._getframe().f_code.co_name)
    #logger.debug('\n\ndeduplicating!')
    prev_line = u''
    good_lines = []
    cookeds = u''
    lines = raws.split(u'\n')
    lines = [normalize_space(line) for line in lines if normalize_space(line) != u'']
    for line in lines:
        #logger.debug(u'prev_line: {0}'.format(prev_line))
        #logger.debug(u'line: {0}'.format(line))
        canary = RX_CANARY.sub(u'', line.lower())
        #logger.debug(u'canary: {0}'.format(canary))
        if canary != u'':
            prev_length = len(prev_line)
            if prev_line != u'' and prev_length < len(canary):
                toucan = unicode(canary[:prev_length])
            else:
                toucan = u''
            #logger.debug(u'toucan: {0}'.format(toucan))
            if prev_line == u'':
                good_lines.append(line)
                #logger.debug('append initial!')
            elif toucan == prev_line:
                good_lines = good_lines[0:-1]
                #logger.debug('clawback!')
                good_lines.append(line)
            elif canary != prev_line:
                #logger.debug('append!')
                good_lines.append(line)
            else:
                #logger.debug('NEIN!')
                pass
        else:
            good_lines.append(line)
        prev_line = canary
    #logger.debug('good_lines follows')
    #for line in good_lines:
        #logger.debug(u'   {0}'.format(line))
    return normalize_space(u' '.join(good_lines))

def purify_html(raw):
    """Out vile jelly!"""
    cooked = RX_DASHES.sub(u'-', raw)   # regularize dashes and hyphens
    cooked = cooked.replace(u'\u00a0', u' ')    # non-breaking space delenda est
    cooked = cooked.replace(u'N\xb0', u'No.')   # extirpate use of degree sign as superscript "o" in volume numbers
    return cooked
