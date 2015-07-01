#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bank of parsers to use for extracting AWOL blog content.

This module defines the following classes:

 * AwolParsers: parse AWOL blog post content for resources
"""

import logging
from importlib import import_module
import pkgutil
import sys

class AwolParsers():
    """Extract data from an AWOL blog post."""

    def __init__(self):
        """Load available parsers."""

        self.parsers = {}

        logger = logging.getLogger(sys._getframe().f_code.co_name)

        ignore_parsers = [
            'awol_parsers',             # self
            'awol_parse',               # superclass
            'awol_parse_domain',        # superclass
        ]
        where = 'isaw/awol/parse'
        parser_names = [name for _, name, _ in pkgutil.iter_modules([where]) if 'parse' in name]
        for parser_name in parser_names:
            if parser_name not in ignore_parsers:
                levels = where.split('/')
                levels.append(parser_name)
                parser_path = '.'.join(tuple(levels))
                #logger.debug('importing module "{0}"'.format(parser_path))
                mod = import_module(parser_path)
                parser = mod.Parser()
                self.parsers[parser.domain] = parser

    def parse(self, article):
        logger = logging.getLogger(sys._getframe().f_code.co_name)

        self.reset()
        self.content_soup = article.soup
        domains = self.get_domains()
        length = len(domains)
        logger.debug(
            u'\n^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nparsing '
            + article.url
            + u'\n')
        logger.debug(u'domains: {0}'.format(repr(domains)))
        if length == 0:
            raise NotImplementedError('awol_parsers does not know what to do with no domains in article: {0}'.format(article.id))
        elif length > 1:
            if u'journal:' in article.title.lower():
                parser = self.parsers['generic-single']
                logger.debug('using "{0}" parser'.format(parser.domain))
                return parser.parse(article)
            else:
                raise NotImplementedError(u'awol_parsers does not know what to do with multiple domains in article: {0}\n    {1}'.format(article.id, u'\n    '.join(domains)))
        else:
            try:
                parser = self.parsers[domains[0]]
            except KeyError:
                if u'journal:' in article.title.lower():
                    parser = self.parsers['generic-single']
                else:
                    parser = self.parsers['generic']
            logger.debug('using "{0}" parser'.format(parser.domain))
            return parser.parse(article)


    def reset(self):
        self.content_soup = None

        #for parser in self.parsers:
        #    parser.reset()


    def get_domains(self, content_soup=None):
        """find valid resource domains in content"""

        if content_soup is None and self.content_soup is None:
            raise AttributeError('No content soup has been fed to parsers.')

        if content_soup is not None:
            self.reset()
            self.content_soup = content_soup

        return self.parsers['generic'].get_domains(self.content_soup)

