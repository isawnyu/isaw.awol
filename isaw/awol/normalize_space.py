#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Normalize space in a string.
"""

import sys

import regex as re

RXU = re.compile(ur'\s+')
RX = re.compile(r'\s+')
def normalize_space(raw):
    """Flatten all whitespace in a string."""

    raw_type = type(raw)
    if raw_type == unicode:
        return RXU.sub(u' ', raw).strip()
    elif raw_type == str:
        return RX.sub(' ', raw).strip()
    else:
        raise TypeError(u'normalize_space cannot handle type {0}'.format(raw_type))


