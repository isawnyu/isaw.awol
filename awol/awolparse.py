

import os
from pyzotero import zotero
import xml.etree.ElementTree as exml
from HTMLParser import HTMLParser;
from django.utils.encoding import smart_str
from bs4 import BeautifulSoup
import json;
import urllib2;


#global variables
#json file stores credentials
#credentials used to access zotero group library that needs to be populated

creds = json.loads(open('creds.json').read());
zot = zotero.Zotero(creds['libraryID'], creds['libraryType'], creds['apiKey']);

#Class that represents all the data that is important from the xml file
# contains a method to print all the items
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

#Class to extract data from the files
#first method to extract form local file file
#seocnd method to extract form url
class ParseXML:

    def extractElementsFromFile(self, file):
        doc = exml.parse(file);
        root = doc.getroot();
        id = root.find('{http://www.w3.org/2005/Atom}id').text;
        title = root.find('{http://www.w3.org/2005/Atom}title').text;
        tags = [];
        tags.append({'tag': root.find('{http://www.w3.org/2005/Atom}category').attrib['term'] });
        soup = BeautifulSoup(root.find('{http://www.w3.org/2005/Atom}content').text);
        content = soup.getText();
        url = (soup.find('a')).get('href');

        return Article(id, title, tags, content, url);

    def extractElementsFromURL(self, url):
        toursurl= urllib2.urlopen(url);
        toursurl_string= toursurl.read();
        root = exml.fromstring(toursurl_string);
        id = root.find('{http://www.w3.org/2005/Atom}id').text;
        title = root.find('{http://www.w3.org/2005/Atom}title').text;
        tags = [];
        tags.append({'tag': root.find('{http://www.w3.org/2005/Atom}category').attrib['term'] });
        soup = BeautifulSoup(root.find('{http://www.w3.org/2005/Atom}content').text);
        content = soup.getText();
        url = (soup.find('a')).get('href');
        return Article(id, title, tags, content, url);

#Class to create zotero item
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
    y = x.extractElementsFromURL('https://raw.githubusercontent.com/paregorios/awol-backup/ce859d62a770f798d7d2a06b42952bb48fe33fe5/post-7832348034400947503-atom.xml');
    #y = x.extractElementsFromFile('data/a1.xml')
    #y.printItems();
    z = CreateNewZotero();
    z.createItem(y);


if __name__ == '__main__':
    main()