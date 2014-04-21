#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Ronak
#
# Created:     21/04/2014
# Copyright:   (c) Ronak 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import argparse
import glob
import logging as l
import os
import sys
import traceback
import xml.etree.ElementTree as xmlParser
import codecs
DEFAULTINPATH = "C:\\Users\\Ronak\\Documents\\GitHub\\awol-backup\\";
SCRIPT_DESC = 'parse unique colon-delimited prefixes out of Ancient World Online blog XML dump files (Atom format)';
DEFAULTOUTPATH='.\\parse.log';
def main():
    xmlList = glob.glob(DEFAULTINPATH + '*-atom.xml');

    print len(xmlList);
if __name__ == '__main__':
        main()
        #sys.exit(0)
