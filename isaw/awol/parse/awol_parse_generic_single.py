#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse HTML content for resources generically.

This module defines the following classes:

 * Parser
"""

import logging
import requests
import sys

from bs4 import BeautifulSoup
from bs4.element import NavigableString
from lxml import etree

from isaw.awol.clean_string import *
from isaw.awol.parse.awol_parse import AwolBaseParser, BIBLIO_SOURCES, RX_PUNCT_FIX, RX_PUNCT_DEDUPE
from isaw.awol.resource import Resource, merge
from isaw.awol.tools import mods

MODS2RESOURCES = {
    'publisher':'publishers',
    'language':'languages',
    'statement_of_responsibility':'responsibility',
    'place':'places',
    'issued_date':'issued_dates',
    'uri':'identifiers'

}

def domain_from_url(url):
    return url.replace('http://', '').replace('https://', '').split('/')[0]

class Parser(AwolBaseParser):
    """Extract data from an AWOL blog post agnostic to domain of resource."""

    def __init__(self):
        self.domain = 'generic-single'
        AwolBaseParser.__init__(self)

    def _get_next_valid_url(self, anchor):
        a = anchor
        while a is not None:
            try:
                url = a.get('href')
            except AttributeError:
                url = None
            else:
                domain = domain_from_url(url)
                if domain not in self.skip_domains:
                    break
            a = a.find_next(a)
        if a is None:
            raise ValueError(u'could not find valid self-or-subsequent resource anchor')
        return (anchor, a, url, domain)

    def _resource_from_external_biblio(self, url):
        """Attempt to get third-party structured bibliographic data."""

        logger = logging.getLogger(sys._getframe().f_code.co_name)
        domain = domain_from_url(url)

        try:
            biblio_howto = BIBLIO_SOURCES[domain]
        except KeyError:
            msg = u'parsing structured bibliographic data from {0} is ' \
            + u'not supported.'.format(domain)
            raise NotImplementedError(msg)
        else:
            m = biblio_howto['url_pattern'].match(url)
            if m:
                biblio_url = url + biblio_howto['url_append']
                biblio_req = requests.get(biblio_url)
                if biblio_req.status_code == 200:
                    actual_type = biblio_req.headers['content-type']
                    if actual_type != biblio_howto['type']:
                        raise IOError('got {actualtype} from {biblurl} when '
                            + '{soughttype} was expected'.format(
                                actualtype=actual_type,
                                biblurl=biblio_url,
                                soughttype=biblio_howto['type']))
                    elif actual_type == 'application/rdf+xml':
                        root = etree.fromstring(biblio_req.content)
                        payload_element = root.xpath(
                            biblio_howto['payload_xpath'], 
                            namespaces=biblio_howto['namespaces'])[0]
                        payload = etree.tostring(payload_element, encoding='unicode')
                    else:
                        raise IOError(u'parsing content of type {actualtype} '
                            + 'is not supported'.format(
                                actualtype=actual_type))
                    payload_type = biblio_howto['payload_type']
                    if payload_type == 'application/mods+xml':
                        biblio_data = mods.extract(payload)
                    else:
                        raise NotImplementedError(u'parsing payload of type {payloadtype} '
                            + 'is not supported'.format(
                                payloadtype=payload_type))
                    logger.info(u'successfully parsed bibliographic data from ' +
                        '{bibliourl} about {title}'.format(
                            bibliourl=biblio_url,
                            title=biblio_data['title'][0]))
                    params = {}
                    for k in [k for k in biblio_data.keys() if k not in ['record_change_date', 'record_creation_date', 'name']]:
                        if k == 'uri':
                            value = (k, biblio_data[k])
                        elif k == 'language':
                            value = [lang[0] for lang in biblio_data[k]]
                        else:
                            value = biblio_data[k]
                        try:
                            rk = MODS2RESOURCES[k]
                        except KeyError:
                            rk = k
                        params[rk] = value
                    params['domain'] = domain_from_url(biblio_data['url'][0])
                    top_resource = self._make_resource(**params)
                    try:
                        updated = biblio_data['record_change_date'][0]
                    except KeyError:
                        updated = biblio_data['record_creation_date'][0]
                    resource_fields = sorted([k for k in params.keys() if '_' != k[0]])
                    top_resource.set_provenance(biblio_url, 'citesAsDataSource', updated, resource_fields)
                    if domain == 'zenon.dainst.org':
                        top_resource.zenon_id = url.split(u'/')[-1]
                else:
                    raise IOError("unsuccessfull attempt (status code {0}) " +
                        "to get bibliograhic data from {1}".format(
                            biblio_req.status_code, biblio_url))
            return top_resource

    def _resource_from_article(self, article, anchor):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        # titles
        anchor_title = clean_string(anchor.get_text())
        titles = self._reconcile_titles(anchor_title, article.title)
        try:
            title = titles[0]
        except IndexError:
            msg = 'could not extract resource title'
            raise IndexError(msg)
        try:
            title_extended = titles[1]
        except IndexError:
            title_extended = None

        # description
        desc_text = self._get_description()

        # parse identifiers
        identifiers = self._parse_identifiers(desc_text)
        logger.debug(u'identifiers: {0}'.format(repr(identifiers)))

        # language
        language = self._get_language(title, title_extended, desc_text)

        # determine keywords
        keywords = self._parse_keywords(article.title, titles[-1], article.categories)

        # create and populate the resource object
        params = {
            'url': anchor.get('href'),
            'domain': domain_from_url(anchor.get('href')),
            'title': title
        }
        if desc_text is not None:
            params['description'] = desc_text
        if len(identifiers.keys()) > 0:
            params['identifiers'] = identifiers
        if title_extended is not None:
            params['title_extended'] = title_extended
        if language is not None:
            params['languages'] = language
        if len(keywords) > 0:
            params['keywords'] = keywords
        resource = self._make_resource(**params)

        # provenance
        self._set_provenance(resource, article)

        #logger.debug(u'returning resource: "{0}"'.format(unicode(resource)))
        return resource        

    def _get_description(self, context=None):
        logger = logging.getLogger(sys._getframe().f_code.co_name)
        html = self._get_description_html(context)
        logger.debug(html)
        soup = BeautifulSoup(html)
        desc_nodes = soup.body.div.contents
        desc_lines = []
        for desc_node in desc_nodes:
            logger.debug(u'desc_node({0}: \n    "{1}"'.format(type(desc_node), unicode(desc_node)))
            if type(desc_node) == NavigableString:
                line = unicode(desc_node)
                logger.debug(u'  appending (A): "{0}"'.format(line))
                desc_lines.append(line)
            elif desc_node.name == 'br':
                desc_lines[-1] += u'.'
                logger.debug(u'  backslapping fullstop for br (A)')
            else:
                anchors = self._filter_anchors(desc_node.find_all('a'))
                logger.debug('anchor length: {0}'.format(len(anchors)))
                if len(anchors) > 1:
                    for this_node in desc_node.contents:
                        if this_node == anchors[1]:
                            break
                        if type(this_node) == NavigableString:
                            line = unicode(this_node)
                            logger.debug(u'  appending (B): "{0}"'.format(line))
                            desc_lines.append(line)
                        elif desc_node.name == 'br':
                            desc_lines[-1].append(u'.')
                            logger.debug(u'backslapping fullstop for br (B)')
                        else:
                            lines = this_node.get_text('\n').split('\n')
                            logger.debug(u'  extending with: {0}'.format(lines))
                            desc_lines.extend(lines)
                    break
                else:
                    try:
                        desc_lines.extend(desc_node.get_text('\n').split('\n'))
                    except AttributeError:
                        pass
                    else:
                        lines = desc_node.get_text('\n').split('\n')
                        logger.debug(u'  extended with: {0}'.format(lines))
        logger.debug('desc_lines follows')
        for line in desc_lines:
            logger.debug(u'   "{0}"'.format(line))
        if len(desc_lines) == 0:
            desc_text = None
        else:
            logger.debug(u'before dedupe: "{0}"'.format(u'\n'.join(desc_lines)))
            desc_text = deduplicate_lines(u'\n'.join(desc_lines))
            if len(desc_text) == 0:
                desc_text = None
            else:
                desc_text = desc_text.replace(u'%IMAGEREPLACED%', u'').strip()
                desc_text = RX_PUNCT_FIX.sub(r'\1', desc_text)
                logger.debug(u'before sentence dedupe: "{0}"'.format(desc_text))
                desc_text = deduplicate_sentences(desc_text)
                logger.debug(u'after sentence dedupe: "{0}"'.format(desc_text))
                desc_text = RX_PUNCT_DEDUPE.sub(r'\1', desc_text)
                if len(desc_text) == 0:
                    desc_text = None
                elif desc_text[-1] != u'.':
                    desc_text += u'.'

        #logger.debug(u"desc_text: {0}".format(desc_text))

        return desc_text        

    def _get_resources(self, article):
        """Assume first link is the top-level resource and everything else is subordinate."""

        logger = logging.getLogger(sys._getframe().f_code.co_name)
        resources = []
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

        # if it points to an external bibliographic resource, try to retrieve and parse it
        bib_resource = None
        try:
            bib_resource = self._resource_from_external_biblio(url)
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
                post_resource = self._resource_from_article(article, a)
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

        serialization = unicode(top_resource)
        serialization = u'\n'.join([u'    {0}'.format(line) for line in serialization.split(u'\n')])
        logger.debug(u'\n>> top_resource:\n    {0}'.format(serialization))

        # parse subordinate resources
        logger.warning("not yet parsing subordinates or relateds")

        return [top_resource,]

