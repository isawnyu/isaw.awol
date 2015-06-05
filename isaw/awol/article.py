#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Working with blog posts.

This module defines the following classes:
 
 * Article: represents key information about the post.
"""

import logging
import pprint
import re
import sys
import unicodedata

from bs4 import BeautifulSoup, UnicodeDammit
from lxml import etree as exml

from isaw.awol.normalize_space import normalize_space

class Article():
    """Manipulate and extract data from a blog post."""

    def __init__(self, atom_file_name=None, json_file_name=None):
        """Load post from Atom entry or JSON and extract basic info.

        The method looks for the following components and saves their 
        values as attributes of the object:

            * id (string): unique identifier for the blog post
            * title (unicode): title of the blog post
            * url (unicode): url of the blog post
            * categories (list of unicode strings): categories assigned to
              the blog post
            * content (string): raw text content of the blog post
            * soup: soupified content of the blog post.
        """

        logger = logging.getLogger(sys._getframe().f_code.co_name)

        if atom_file_name is not None:
            if json_file_name is not None:
                logger.warning(
                    'Filenames for both Atom and JSON were specified'
                    + ' in Article constructor. JSON filename ignored.')
            with open(atom_file_name, 'r') as file_object:
                self.doc = exml.parse(file_object)
            self.root = self.doc.getroot()
            root = self.root
            self.id = root.find('{http://www.w3.org/2005/Atom}id').text.strip()
            raw_title = root.find('{http://www.w3.org/2005/Atom}title').text
            try:
                self.title = normalize_space(unicodedata.normalize('NFC', UnicodeDammit(raw_title).unicode_markup))
            except TypeError:
                logger.warning('could not extract blog post title: {0}'.format(self.id))
            try:
                raw_url = root.xpath("//*[local-name()='link' and @rel='alternate']")[0].get('href')
            except IndexError:
                logger.warning('could not extract blog post URL: {0}'.format(self.id))
            else:
                try:
                    self.url = unicodedata.normalize('NFC', UnicodeDammit(raw_url).unicode_markup)
                except TypeError:
                    logger.warning('could not extract blog post URL: {0}'.format(self.id))
            self.categories = [{'vocabulary' : c.get('scheme'), 'term' : c.get('term')} for c in root.findall('{http://www.w3.org/2005/Atom}category')]
            raw_content = root.find('{http://www.w3.org/2005/Atom}content').text
            try:
                content = normalize_space(unicodedata.normalize('NFC', UnicodeDammit(raw_content).unicode_markup))
            except TypeError:
                content = None
                logger.warning('could not extract content')
            else:
                self.content = content
                self.soup = BeautifulSoup(content)
        elif json_file_name is not None:
            # todo
            emsg = 'Article constructor does not yet support JSON.'
            logger.error(emsg)
            raise NotImplementedError(emsg)


    def __str__(self):
        """Print all data about the article."""

        return str(self.id+"|"+self.title+"|"+str(self.tags)+"|"+
            self.content+"|"+self.url+"|"+self.blogUrl+"|"+self.template+
            "|"+self.issn)


