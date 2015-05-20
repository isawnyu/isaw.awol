import os
from pyzotero import zotero
import xml.etree.ElementTree as exml
from HTMLParser import HTMLParser;
from django.utils.encoding import smart_str
from bs4 import BeautifulSoup
import json;
import urllib2;
import glob;
import argparse;

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
    def caseConversion(self,tag):
        utag = tag.upper();
        if(utag != tag):
            tag = tag.title();
        return tag;

    def extractElementsFromFile(self, file):
        doc = exml.parse(file);
        root = doc.getroot();
        id = root.find('{http://www.w3.org/2005/Atom}id').text;
        title = root.find('{http://www.w3.org/2005/Atom}title').text;
        tags = [];
        categories = root.findall('{http://www.w3.org/2005/Atom}category');

        for c in categories:
            tag = c.attrib['term'];
            tag = self.caseConversion(tag);
            tags.append({'tag': tag });
        tags.pop(0);

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
        categories = root.findall('{http://www.w3.org/2005/Atom}category');

        for c in categories:
            tag = c.attrib['term'];
            tag = self.caseConversion(tag);
            tags.append({'tag': tag });
        tags.pop(0);

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

#Create zotero objects from XML files in the local directory by passing its path
def parseDirectory(PATH, no):
    x = ParseXML();

    items = glob.glob(PATH + '*-atom.xml');
    for i in items:
        if(no == 0):
            break;
        y = x.extractElementsFromFile(i);
        z = CreateNewZotero();
        z.createItem(y);
        no -= 1;


def main():

    parser = argparse.ArgumentParser();
    group = parser.add_mutually_exclusive_group();
    group.add_argument("-w", "--webpath", help = "web path to XML file", action = "store_true");
    group.add_argument("-l", "--localpath", help = "local path to XML file/ directory", type = str , choices = ['f','d']);
    parser.add_argument("path", help = "specify path")
    parser.add_argument("-n", "--numdoc", help = "specify no of documents", type = int, default = -1);

    args = parser.parse_args()


    x = ParseXML();
    z = CreateNewZotero();

    if(args.webpath):
        y = x.extractElementsFromURL(parser.path);
        z.createItem(y);
    else:
        if(args.localpath == 'f'):
            y = x.extractElementsFromFile(args.path);
            z.createItem(y);
        else:
            noofdoc = args.numdoc;
            parseDirectory(args.path, noofdoc);



if __name__ == '__main__':
    main()