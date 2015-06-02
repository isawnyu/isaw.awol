#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to test upload of sample files to Zotero.
"""

import _mypath
import argparse
import fileinput
from functools import wraps
import json
import logging
import os
import re
import sys
import traceback

from pyzotero import zotero
from isaw.awol import awol_article

DEFAULTLOGLEVEL = logging.WARNING

def arglogger(func):
    """
    decorator to log argument calls to functions
    """
    @wraps(func)
    def inner(*args, **kwargs): 
        logger = logging.getLogger(func.__name__)
        logger.debug("called with arguments: %s, %s" % (args, kwargs))
        return func(*args, **kwargs) 
    return inner    


@arglogger
def main (args):
    """
    main functions
    """
    logger = logging.getLogger(sys._getframe().f_code.co_name)
    root_dir = args.whence[0]
    dest_dir = args.thence[0]
    parse_count = 0
    resources = None
    for dir_name, sub_dir_list, file_list in os.walk(root_dir):
        if resources is not None:
            del resources
        for file_name in file_list:
            if 'post-' in file_name and file_name[-4:] == '.xml':
                logger.info('parsing {0}'.format(file_name))
                target = os.path.join(dir_name, file_name)
                a = awol_article.AwolArticle(atom_file_name=target)
                try:
                    resources = a.parse_atom_resources()
                except NotImplementedError, msg:
                    pass
                else:
                    try:
                        logger.info('found {0} resources'.format(len(resources)))
                    except TypeError:
                        logger.info('found 0 resources')
                    else:                        
                        parse_count = parse_count + len(resources)
                        for r in resources:
                            this_id = id(r)
                            this_path = os.path.join(dest_dir, '.'.join((str(this_id), 'json')))
                            r.json_dump(this_path, formatted=True)
                        print '    parse_count: {0}'.format(parse_count)
                        #if parse_count > 50:
                        #    raise Exception
            else:
                logger.debug('skipping {0}'.format(file_name))
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
        parser.add_argument('credfile', type=str, nargs=1, help='path to credential file')
        #parser.add_argument('postfile', type=str, nargs='?', help='filename containing list of post files to process')
        parser.add_argument('whence', type=str, nargs=1, help='path to directory to read and process')
        parser.add_argument('thence', type=str, nargs=1, help='path to directory where you want the json-serialized resources dumped')
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
