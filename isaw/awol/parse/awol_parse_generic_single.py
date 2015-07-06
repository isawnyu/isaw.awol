#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse HTML content for resources generically.

This module defines the following classes:

 * Parser
"""

import logging
import sys

from isaw.awol.parse.awol_parse import AwolBaseParser
from isaw.awol.resource import merge

class Parser(AwolBaseParser):
    """Extract data from an AWOL blog post on the assumption the post is about a single resource."""

    def __init__(self):
        self.domain = 'generic-single'
        AwolBaseParser.__init__(self)

    def _get_resources(self, article):
        """Assume first link is the top-level resource and everything else is subordinate."""

        logger = logging.getLogger(sys._getframe().f_code.co_name)
        resources = []
        relateds = []
        subordinates = []
        soup = article.soup

        # first get the top-level resource (skipping over any self links)        
        a = soup.find_all('a')[0]
        try:
            a_prev, a, url, domain = self._get_next_valid_url(a)
        except ValueError as e:
            msg = u'{e} when handling {article} with {parser} parser'.format(
                e=e,
                article=article.url,
                parser=self.domain)
            logger.warning(msg)
            return resources

        #logger.debug(self._nodesplain(a, 'first valid url'))

        # if it points to an external bibliographic resource, try to retrieve and parse it
        bib_resource = None
        try:
            bib_resource = self._get_resource_from_external_biblio(url)
        except NotImplementedError, e:
            logger.warning(unicode(e) + u' while handling {0} from {1}'.format(url, article.url))
        except IOError, e:
            logger.error(unicode(e) + u' while handling {0} from {1}'.format(url, article.url))
        else:
            prev_url = url
            a = a.find_next('a')
            try:
                a_prev, a, url, domain = self._get_next_valid_url(a)
            except ValueError as e:
                msg = u'{e} after handling bibliographic url {biblurl} in {article} with {parser} parser'.format(
                    e=e,
                    biblurl=biblio_url,
                    article=article.url,
                    parser=self.domain)
                logger.warning(msg)
                
        # parse what we can out of the blog post itself
        post_resource = None
        if bib_resource is not None:
            if bib_resource.url != url:
                logger.warning('First URL {0} was external bibliography; second URL {1} does not match the resource URL {2} extracted from the biblio.'.format(prev_url, url, bib_resource.url))
                # try to get what we can from the post to round out what we have
                fields = []
                if bib_resource.description is None:
                    bib_resource.description = self._get_description()
                if bib_resource.description is not None:
                    fields.append('description')
                if len(bib_resource.keywords) == 0:
                    bib_resource.keywords = self._parse_keywords(article.title, bib_resource.title, article.categories)
                if len(bib_resource.keywords) > 0:
                    fields.append('keywords')
                if len(fields) > 0:
                    self._set_provenance(bib_resource, article, fields)
        if bib_resource is None or bib_resource.url == url:
            try:
                #logger.debug(self._nodesplain(a, 'calling _get_resource_from_article'))
                post_resource = self._get_resource_from_article(article, a)
            except IndexError, e:
                logger.error(unicode(e) + u' while handling {0} from {1}'.format(url, article.url))
            else:
                a = a.find_next('a')
                try:
                    a_prev, a, url, domain = self._get_next_valid_url(a)
                except ValueError as e:
                    msg = u'{e} after handling url {url} in {article} with {parser} parser'.format(
                        e=e,
                        url=url,
                        article=article.url,
                        parser=self.domain)
                    logger.warning(msg)

        top_resource = None
        if post_resource is not None and bib_resource is not None:
            top_resource = merge(bib_resource, post_resource)
        elif post_resource is not None:
            top_resource = post_resource
        elif bib_resource is not None:
            top_resource = bib_resource

        # parse subordinate and related resources
        #if top_resource.url == 'http://retro.seals.ch/digbib/vollist?UID=caf-002':
        #    raise Exception
        subordinates = self._get_subordinate_resources(article, top_resource.package(), start_anchor=a)
        top_resource.subordinate_resources = [sub.package() for sub in subordinates]

        return [top_resource,] + subordinates + relateds

