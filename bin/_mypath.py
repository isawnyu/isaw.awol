#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
thisdir = os.path.dirname(__file__)
libdir = os.path.join(thisdir, '..')

if libdir not in sys.path:
  sys.path.insert(0, libdir)
