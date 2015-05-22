#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define classes and methods for working with AWOL blog articles.

This module defines the following classes:
 
 * Article: represents key information about the article.
"""


from lxml import etree as exml

class Article():
    """Represent all data that is important about an AWOL blog article."""

    def __init__(self, file_name):
        """Verify and open file."""
        with open(file_name, 'r') as file_object:
            self.doc = exml.parse(file_object)
        self.root = self.doc.getroot()

    def parse(self):
        """Parse desired components out of the file.

        Method looks for the following components and saves their values as
        attributes of the object:

            * id (string): unique identifier for the blog post
            * title (unicode): title of the blog post
            * url (unicode): url of the blog post
            * categories (list of unicode strings): categories assigned to
              the blog post
            * content (string): raw content of the blog post
            * resources (list of resource objects): information about each
              web resource found mentioned in the article content

        """

        root = self.root
        self.id = root.find('{http://www.w3.org/2005/Atom}id').text
        self.title = unicode(root.find('{http://www.w3.org/2005/Atom}title').text)
        self.url = unicode(root.xpath("//*[local-name()='link' and @rel='alternate']")[0].get('href'))
        self.categories = [{'vocabulary' : c.get('scheme'), 'term' : c.get('term')} for c in root.findall('{http://www.w3.org/2005/Atom}category')]
        self.content = root.find('{http://www.w3.org/2005/Atom}content').text
        self.resources = self.get_resources()

    def get_resources(self):
        """Identify all the resources mentioned in this article."""

        resources = []
        return resources

    def __str__(self):
        """Print all data about the article."""

        return str(self.id+"|"+self.title+"|"+str(self.tags)+"|"+
            self.content+"|"+self.url+"|"+self.blogUrl+"|"+self.template+
            "|"+self.issn)
