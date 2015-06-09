#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Working with blog posts.

This module defines the following classes:
 
 * Article: represents key information about the post.
"""

import logging
import os
import pprint
import re
import sys
import unicodedata

from bs4 import BeautifulSoup, UnicodeDammit
from lxml import etree as exml
from lxml.etree import XMLSyntaxError as XMLSyntaxError

from isaw.awol.normalize_space import normalize_space
from isaw.awol.clean_string import purify_html

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

            self._load_atom(atom_file_name)
        elif json_file_name is not None:
            # todo
            self.__load_json(json_file_name)

    def _load_atom(self, atom_file_name):
        """Open atom file and parse for basic info.

        We attempt to set the following attributes on the class:

         * id (string): tag id for this atom entry
         * title (unicode): title of the original blog post
         * url (string): url for the original blog post)
         * categories (dictionary) with the following keys:
           * 'vocabulary' (string): captures "scheme" from the entry categories
           * 'term' (string): verbatim from the entry categories
         * content (unicode): normalized unicode string containing everything
           that was in the entry content (see normalization comments below)
         * soup (bs4 BeutifulSoup object): html-parsed version of content

        All strings are space normalized (i.e., all continguous spans of
        whitespace are collapsed to a single space and the result string is
        stripped of leading and trailing whitespace).

        The normalization form of all unicode strings (title and content) are
        converted to Normalization Form "C" (canonical normalized).
        """

        logger = logging.getLogger(sys._getframe().f_code.co_name)

        with open(atom_file_name, 'r') as file_object:
            self.doc = exml.parse(file_object)
        self.root = self.doc.getroot()
        root = self.root
        self.id = root.find('{http://www.w3.org/2005/Atom}id').text.strip()
        logger.debug('article id: "{0}"'.format(self.id))

        # title of blog post should be same as title of atom entry
        raw_title = unicode(root.find('{http://www.w3.org/2005/Atom}title').text)
        try:
            self.title = normalize_space(unicodedata.normalize('NFC', raw_title))
        except TypeError:
            msg = 'could not extract blog post title for article with id: "{0}"'.format(self.id)
            raise RuntimeWarning(msg)
            
        else:
            logger.debug(u'article title: "{0}"'.format(self.title))

        # get url of blog post (html alternate)
        try:
            raw_url = unicode(root.xpath("//*[local-name()='link' and @rel='alternate']")[0].get('href'))
        except IndexError:
            msg = 'could not extract blog post URL for article with id: "{0}"'.format(self.id)
            raise RuntimeError(msg)
        else:
            try:
                self.url = normalize_space(unicodedata.normalize('NFC', raw_url))
            except TypeError:
                msg = 'could not extract blog post URL for article with id: "{0}"'.format(self.id)
                raise RuntimeError(msg)

        # capture categories as vocabulary terms
        self.categories = [{'vocabulary' : c.get('scheme'), 'term' : c.get('term')} for c in root.findall('{http://www.w3.org/2005/Atom}category')]
        
        # extract content, normalize, and parse as HTML for later use
        raw_content = unicode(root.find('{http://www.w3.org/2005/Atom}content').text)
        content = normalize_space(unicodedata.normalize('NFC', raw_content))
        content = purify_html(content)
        self.content = content
        soup = BeautifulSoup(content)
        try:
            html = exml.fromstring(str(soup))
        except XMLSyntaxError:
            msg = 'XMLSyntaxError while trying to parse content of {0}'.format(atom_file_name)
            raise ValueError(msg)

        #logger.debug('normalized html:\n\n' + exml.tostring(html, pretty_print=True))
        xsl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cleanup.xsl')
        xsl = exml.parse(xsl_path)
        transform = exml.XSLT(xsl)
        clean_html = transform(html)
        #logger.debug('cleaned html:\n\n' + exml.tostring(clean_html, pretty_print=True))
        self.soup = BeautifulSoup(exml.tostring(clean_html))


    def _load_json(self, json_file_name):
        """open atom file and parse for basic info"""
        emsg = 'Article constructor does not yet support JSON.'
        raise NotImplementedError(emsg)

    def __str__(self):
        """Print all data about the article."""

        return str(self.id+"|"+self.title+"|"+str(self.tags)+"|"+
            self.content+"|"+self.url+"|"+self.blogUrl+"|"+self.template+
            "|"+self.issn)


