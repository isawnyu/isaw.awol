#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define classes and methods for working with AWOL blog articles.

This module defines the following classes:
 
 * Article: represents key information about the article.
"""

class Article:
    """Represent all data that is important about an AWOL blog article."""

    def __init__(self, id, title, tags, content, url, blogUrl, issn, template):
        """Set all data about the article."""

        self.id = id
        self.title = title
        self.tags = tags
        self.content = content
        self.url = url
        self.blogUrl = blogUrl
        self.template = template
        self.issn = issn

    def __str__(self):
        """Print all data about the article."""
        return str(self.id+"|"+self.title+"|"+str(self.tags)+"|"+
            self.content+"|"+self.url+"|"+self.blogUrl+"|"+self.template+
            "|"+self.issn)
