#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Ronak
#
# Created:     28/03/2014
# Copyright:   (c) Ronak 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import os
from pyzotero import zotero
import xml.etree.ElementTree as exml
from HTMLParser import HTMLParser;
from django.utils.encoding import smart_str
from bs4 import BeautifulSoup
import json;

creds = json.loads(open('creds.json').read());
zot = zotero.Zotero(creds['libraryID'], creds['libraryType'], creds['apiKey']);

class Article:
    def __init__(self, id, title, tags, content, url):
        self.id = id;
        self.title = title;
        self.tags = tags;
        self.content = content;
        self.url = url;

    def printItems(self):
        print self.id;
        print self.title;
        print self.tags;
        print self.content;
        print self.url;

class ParseXML:

    def extractElements(self, file):
        doc = exml.parse(file);
        root = doc.getroot();
        id = root[0].text;
        title = root[4].text;
        tags = [];
        tags.append({'tag': root[3].attrib['term'] });
        soup = BeautifulSoup(root[5].text);
        content = soup.getText();
        url = (soup.find('a')).get('href');

        return Article(id, title, tags, content, url);

class CreateNewZotero:


    def createItem(self, art):
        template = zot.item_template('webpage');
        template['extra'] = art.id;
        template['title'] = art.title;
        template['url'] = art.url;
        template['abstractNote'] = art.content;
        template['tags'] = art.tags;

        resp = zot.create_items([template]);

def main():

    x = ParseXML();
    y = x.extractElements('data\\t1 (2).xml');
    z = CreateNewZotero();
    z.createItem(y);


if __name__ == '__main__':
    main()