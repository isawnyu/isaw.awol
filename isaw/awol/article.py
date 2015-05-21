#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define classes and methods for working with AWOL blog articles.

This module defines the following classes:
 
 * Article: represents key information about the article.
"""


from bs4 import BeautifulSoup
import xml.etree.ElementTree as exml

class Article():
    """Represent all data that is important about an AWOL blog article."""

    def __init__(self, file_name):
        """Verify and open file."""
        with open(file_name, 'r') as file_object:
            self.doc = exml.parse(file_object)
        self.root = self.doc.getroot()

    def parse(self):
        """Parse desired components out of the file."""

        root = self.root
        self.id = root.find('{http://www.w3.org/2005/Atom}id').text
        self.title = unicode(root.find('{http://www.w3.org/2005/Atom}title').text)
        # self.tags = tags
        # self.content = content
        # self.url = url
        # self.blogUrl = blogUrl
        # self.template = template
        # self.issn = issn
        pass

    def __str__(self):
        """Print all data about the article."""

        return str(self.id+"|"+self.title+"|"+str(self.tags)+"|"+
            self.content+"|"+self.url+"|"+self.blogUrl+"|"+self.template+
            "|"+self.issn)
