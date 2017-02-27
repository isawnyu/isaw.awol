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
    """Pluggable framework for parsing content from an AwolArticle."""

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
        parser_names = [
            name for _, name, _ in pkgutil.iter_modules([where])
            if 'parse' in name]
        for parser_name in parser_names:
            if parser_name not in ignore_parsers:
                levels = where.split('/')
                levels.append(parser_name)
                parser_path = '.'.join(tuple(levels))
                logger.debug('importing module "{0}"'.format(parser_path))
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
        if length == 0:
            raise NotImplementedError('awol_parsers does not know what to do with no domains in article: {0}'.format(article.id))
        else:
            tlow = article.title.lower()
            if u'journal:' in tlow:
                parser = self.parsers['generic-single']
            elif length == 1:
                try:
                    parser = self.parsers[domains[0]]
                except KeyError:
                    if domains[0] in ['www.egyptpro.sci.waseda.ac.jp',]:
                        parser = self.parsers['generic-single']
                    else:
                        parser = self.parsers['generic']
                        anchors = self.get_anchors()
                        logger.debug('len(anchors) = {}'.format(len(anchors)))
                        if len(anchors) > 1:
                            max_len = 0
                            for a in anchors:
                                max_len = max(len(a), max_len)
                            last_common = '{{0: <{}}}'.format(max_len).format(
                                'foo')
                            a_prev = anchors[0]
                            last_common = a_prev.get('href')
                            biggest = last_common
                            for a_next in anchors[1:]:
                                href = a_next.get('href')
                                if len(href) > len(biggest):
                                    biggest = href
                                this_common = longest_common_substring(
                                    last_common, a_next.get('href'))
                                last_common = this_common
                            if last_common.startswith('http'):
                                bits_common = last_common.split('/')
                                bits_biggest = biggest.split('/')
                                if len(bits_biggest) - len(bits_common) < 2:
                                    parser = self.parsers['generic-flat']
            else:
                raise NotImplementedError(u'awol_parsers does not know what to do with multiple domains in article: {0}\n    {1}'.format(article.id, u'\n    '.join(domains)))
            logger.info('using "{0}" parser'.format(parser.domain))
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

    def get_anchors(self, content_soup=None):
        """find valid anchors (links) in content"""

        if content_soup is None and self.content_soup is None:
            raise AttributeError('No content soup has been fed to parsers.')

        if content_soup is not None:
            self.reset()
            self.content_soup = content_soup

        return self.parsers['generic'].get_anchors(self.content_soup)


def longest_common_substring(s1, s2):
    m = [[0] * (1 + len(s2)) for i in xrange(1 + len(s1))]
    longest, x_longest = 0, 0
    for x in xrange(1, 1 + len(s1)):
        for y in xrange(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
                    x_longest = x
            else:
                m[x][y] = 0
    return s1[x_longest - longest: x_longest]
