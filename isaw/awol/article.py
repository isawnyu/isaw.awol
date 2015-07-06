#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Working with blog posts.

This module defines the following classes:
 
 * Article: represents key information about the post.
"""

import logging
import os
import sys
import unicodedata

from bs4 import BeautifulSoup
from lxml import etree as exml
from lxml.etree import XMLSyntaxError as XMLSyntaxError

from isaw.awol.normalize_space import normalize_space
from isaw.awol.clean_string import purify_text, purify_html
from isaw.awol.tools import urls

XML_PARSER = exml.XMLParser(recover=False)
XML_PARSER_LENIENT = exml.XMLParser(recover=True)
XSL_CLEANUP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cleanup.xsl')
XSL_CLEANUP = exml.parse(XSL_CLEANUP_PATH)

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
        #logger.debug('article id: "{0}"'.format(self.id))

        # title of blog post should be same as title of atom entry
        raw_title = unicode(root.find('{http://www.w3.org/2005/Atom}title').text)
        try:
            self.title = purify_text(normalize_space(unicodedata.normalize('NFC', raw_title)))
        except TypeError:
            msg = 'could not extract blog post title for article with id: "{0}"'.format(self.id)
            raise RuntimeWarning(msg)
            
        else:
            #logger.debug(u'article title: "{0}"'.format(self.title))
            pass

        # get url of blog post (html alternate)
        try:
            raw_url = unicode(root.xpath("//*[local-name()='link' and @rel='alternate']")[0].get('href'))
        except IndexError:
            msg = 'could not extract blog post URL for article with id: "{0}"'.format(self.id)
            raise RuntimeError(msg)
        else:
            try:
                raw_url = normalize_space(unicodedata.normalize('NFC', raw_url))
            except TypeError:
                msg = 'could not normalize blog post URL for article with id: "{0}"'.format(self.id)
                raise RuntimeError(msg)
            else:
                if urls.valid(raw_url):
                    self.url = raw_url
                else:
                    msg = 'invalid blog post URL ({0}) for article with id: "{1}"'.format(raw_url, self.id)
                    raise RuntimeError(msg)

        # capture categories as vocabulary terms
        self.categories = [{'vocabulary' : c.get('scheme'), 'term' : normalize_space(unicodedata.normalize('NFC', unicode(c.get('term'))))} for c in root.findall('{http://www.w3.org/2005/Atom}category')]
        
        # extract content, normalize, and parse as HTML for later use
        raw_content = root.find('{http://www.w3.org/2005/Atom}content').text
        soup = BeautifulSoup(raw_content)   # mainly to convert character entities to unicode
        soup_content = unicode(soup)
        del soup
        content = unicodedata.normalize('NFC', soup_content)
        del soup_content
        content = normalize_space(content)
        content = purify_html(content)  # get rid of all manner of evil, stupid stuff
        self.content = content
        try:
            html = exml.fromstring(content, XML_PARSER)
        except XMLSyntaxError:
            msg = 'XMLSyntaxError while trying to parse content of {0}; trying html5lib parser with BeautifulSoup and then lxml parser with recover=True'.format(atom_file_name)
            logger.warning(msg)
            soup = BeautifulSoup(raw_content, 'html5lib')
            soup_content = unicode(soup)
            del soup
            content = unicodedata.normalize('NFC', soup_content)
            del soup_content
            content = normalize_space(content)
            content = purify_html(content)
            self.content = content
            try:
                html = exml.fromstring(content, XML_PARSER_LENIENT)
            except XMLSyntaxError:
                msg = 'XMLSyntaxError while trying to re-parse content of {0} using html5lib parser with BeautifulSoup'.format(atom_file_name)
                logger.error(msg)
                logger.error(content)
                sys.exit(-1000)

        #logger.debug('normalized html:\n\n' + exml.tostring(html, pretty_print=True))
        transform = exml.XSLT(XSL_CLEANUP)
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


