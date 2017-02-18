#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to walk AWOL backup and look for new keywords.
"""

import _mypath
import argparse
import errno
import fileinput
import hashlib
from isaw.awol import awol_article
import json
import logging
import os
import pkg_resources
import pprint
import regex as re
import sys
import traceback
import unicodecsv


RX_URLFLAT = re.compile(r'[=+\?\{\}\{\}\(\)\\\-_&%#/,\.;:]+')
RX_DEDUPEH = re.compile(r'[-]+')
DEFAULTLOGLEVEL = logging.WARNING

title_strings_csv = pkg_resources.resource_stream(
    'isaw.awol', 'awol_title_strings.csv')
dreader = unicodecsv.DictReader(
    title_strings_csv,
    fieldnames=[
        'titles',
        'tags'
    ],
    delimiter=',',
    quotechar='"')
TITLE_SUBSTRING_TAGS = dict()
for row in dreader:
    TITLE_SUBSTRING_TAGS.update({row['titles']: row['tags']})
del dreader


def main(args):
    """
    main functions
    """
    logger = logging.getLogger(sys._getframe().f_code.co_name)
    root_dir = args.whence[0]
    walk_count = 0
    newkeys = []
    for dir_name, sub_dir_list, file_list in os.walk(root_dir):
        for file_name in file_list:
            if 'post-' in file_name and file_name[-4:] == '.xml':
                walk_count = walk_count + 1
                if walk_count % 50 == 1:
                    if args.progress:
                        print('\n*****************************\nPERCENT COMPLETE: {0:.0f}\n'.format(float(walk_count)/4261.0*100.0))
                    newkeys = sorted(list(set(newkeys)))
                logger.info('\n=========================================================================================\nARTICLE:\n')
                target = os.path.join(dir_name, file_name)
                try:
                    a = awol_article.AwolArticle(atom_file_name=target)
                except (ValueError, RuntimeError) as e:
                    logger.warning(e)
                else:
                    keywords = [c['term'] for c in a.categories if c['vocabulary'] == 'http://www.blogger.com/atom/ns#']
                    for kw in keywords:
                        k = kw.lower().strip()
                        try:
                            nert = TITLE_SUBSTRING_TAGS[k]
                        except KeyError:
                            if k not in newkeys:
                                print('"{}"" from "{}"; title = {}'.format(
                                    k.encode('utf-8'), kw.encode('utf-8'), a.title.encode('utf-8')))
                                newkeys.append(k)
        for ignore_dir in ['.git', '.svn', '.hg']:
            if ignore_dir in sub_dir_list:
                sub_dir_list.remove(ignore_dir)


if __name__ == "__main__":
    log_level = DEFAULTLOGLEVEL
    log_level_name = logging.getLevelName(log_level)
    logging.basicConfig(level=log_level)

    try:
        parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument ("-l", "--loglevel", type=str, help="desired logging level (case-insensitive string: DEBUG, INFO, WARNING, ERROR" )
        parser.add_argument ("-v", "--verbose", action="store_true", default=False, help="verbose output (logging level == INFO")
        parser.add_argument ("-vv", "--veryverbose", action="store_true", default=False, help="very verbose output (logging level == DEBUG")
        parser.add_argument ("--progress", action="store_true", default=False, help="show progress")
        #parser.add_argument('postfile', type=str, nargs='?', help='filename containing list of post files to process')
        parser.add_argument('whence', type=str, nargs=1, help='path to directory to read and process')
        args = parser.parse_args()
        if args.loglevel is not None:
            args_log_level = re.sub('\s+', '', args.loglevel.strip().upper())
            try:
                log_level = getattr(logging, args_log_level)
            except AttributeError:
                logging.error("command line option to set log_level failed because '%s' is not a valid level name; using %s" % (args_log_level, log_level_name))
        if args.veryverbose:
            log_level = logging.DEBUG
        elif args.verbose:
            log_level = logging.INFO
        log_level_name = logging.getLevelName(log_level)
        logging.getLogger().setLevel(log_level)
        if log_level != DEFAULTLOGLEVEL:
            logging.warning("logging level changed to %s via command line option" % log_level_name)
        else:
            logging.info("using default logging level: %s" % log_level_name)
        logging.debug("command line: '%s'" % ' '.join(sys.argv))
        main(args)
        sys.exit(0)
    except KeyboardInterrupt, e: # Ctrl-C
        raise e
    except SystemExit, e: # sys.exit()
        raise e
    except Exception, e:
        print "ERROR, UNEXPECTED EXCEPTION"
        print str(e)
        traceback.print_exc()
        os._exit(1)
