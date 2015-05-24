#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Normalize space in a string.
"""

import re

def normalize_space(raw):
    """Flatten all whitespace in a string."""

    rx = re.compile('\s+')
    cooked = rx.sub(' ', raw).strip()
    return cooked


