# -*- coding: utf-8 -*-
import os
from pyzotero import zotero
import xml.etree.ElementTree as exml
from bs4 import BeautifulSoup
import json
import urllib2
import glob
import argparse
import csv
import logging as log
import traceback
import re
import httplib2
import time
from ZoteroRESTCalls import ZoteroRESTCalls
from socket import error as socket_error

#Class to create zotero item
class CreateNewZotero:
    #creds.json- credentials used to access zotero group library that needs to be populated
    creds = json.loads(open('creds.json').read())
    zot = zotero.Zotero(creds['libraryID'], creds['libraryType'], creds['apiKey'])
    #Function to create a zotero record
    def createItem(self, art):
        global recCounter, zot, creds
        zoterorest = ZoteroRESTCalls()
        if art != None:
            template = zot.item_template(art.template)
            template['extra'] = art.id
            template['title'] = art.title
            template['url'] = art.url
            template['abstractNote'] = art.content
            template['tags'] = art.tags
            if art.template == 'journalArticle':
                template['issn'] = art.issn
            try:
                resp = zot.create_items([template])
                postUrlSuf = '/'+creds['libraryType']+'s/'+creds['libraryID']+'/items?key='+creds['apiKey']
                title = 'Original Blog URL:' + art.blogUrl
                result = zoterorest.createChildAttachment(postUrlSuf, resp[0]['key'], art.blogUrl, title)
                log.info("Created Zotero item with title %s" % art.title)
                log.info("Child attachment result:%s" % result)
            except Exception, e:
                log.info("********ERROR, UNEXPECTED EXCEPTION********")
                log.info(e)
                log.info("*******************************************")
                traceback.print_exc()
            recCounter = recCounter + 1
        else:
            log.info("None record: Nothing to be created")