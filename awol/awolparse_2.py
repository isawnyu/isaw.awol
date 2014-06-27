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


DEFAULTOUTPATH='.//zotero_items_load.log'
recCounter = int()
recCounter = 0

#creds.json- credentials used to access zotero group library that needs to be populated
creds = json.loads(open('creds.json').read())
zot = zotero.Zotero(creds['libraryID'], creds['libraryType'], creds['apiKey'])
##########################READ CSV###################
#Read CSV file containing the right tags to produce
dictReader = csv.DictReader(open('awol_title_strings.csv', 'rb'), 
                    fieldnames = ['titles', 'tags'], delimiter = ',', quotechar = '"')
#Build a dictionary from the CSV file-> {<string>:<tags to produce>}
titleStringsDict = dict()
for row in dictReader:
    titleStringsDict.update({row['titles']:row['tags']})

#Read awol_colon_prefixes.csv file and build a dictionary
dictReader2 = csv.DictReader(open('awol_colon_prefixes.csv', 'rb'), 
                     fieldnames = ['col_pre', 'omit_post', 'strip_title', 'mul_res'], delimiter = ',', quotechar = '"')
colPrefDict = dict()
#Build a dictionary of format {<column prefix>:<list of cols 2,3 and 4>}
for row in dictReader2:
    colPrefDict.update({row['col_pre']:[row['omit_post'], row['strip_title'], row['mul_res']]})
#############END OF READ CSV#########################

#*************************
# with open('procsd_files.txt','r') as myfile:
#     procFiles = myfile.read().replace('\n','')
#     procFilesList = procFiles.split(',')
#*************************

#Class that represents all the data that is important from the xml file
class Article:
    def __init__(self, id, title, tags, content, url, blogUrl, issn, template):
        self.id = id
        self.title = title
        self.tags = tags
        self.content = content
        self.url = url
        self.blogUrl = blogUrl
        self.template = template
        self.issn = issn

    def printItems(self):
        print self.id
        print self.title
        print self.tags
        print self.content
        print self.url
        print self.blogUrl
        print self.template
        print self.issn

#Class to extract data from the files
#first method to extract form local file
#seocnd method to extract form url
class ParseXML:
            
    #Function to get ISSNs if any from the given XML
    def getISSNFromXML(self, root):
        xmlStr = exml.tostring(root, encoding='utf8', method='xml')
        issnrex = re.findall(r'issn[^\d]*[\dX]{4}-?[\dX]{4}', xmlStr, re.IGNORECASE)
        if issnrex:
            log.debug('Found ISSNs')
            if len(issnrex) > 1: #If more than 1 issns are found
                for s in issnrex:
                    if ('electrón' or 'électron' or 'electron' or 'digital' or 'online') in s:
                        issn = re.search(r'[\dX]{4}-?[\dX]{4}', s)
                        log.debug(issn.group())
                        return issn.group()
            issn = re.search(r'[\dX]{4}-?[\dX]{4}', issnrex[0], re.IGNORECASE)
            log.debug(issn.group())
            return issn.group()
        else:
            return None
            
    #Function to look up data in CSV converted dict and produce relevant tags
    def produceTag(self, tags, categories, title):
        for c in categories:    
            tag = c.attrib['term']
            if tag in titleStringsDict.keys():
                tag = titleStringsDict[tag]
            else:
                tag = self.caseConversion(tag)
            #Check if multiple tags separated by ',' exist in the titleStringsDict[tag]
            if ',' in tag:
                tagList = tag.split(',')
                for tg in tagList:
                    if tg in title:
                        tags.append({'tag': tg })
            else:
                if tag in title:
                    tags.append({'tag': tag })
        if "open" and ("access" or "accesss") and not "partially" in title:
            tags.append({'tag': "Open Access" })
        elif "open" and ("access" or "accesss") and "partially" in title:
            tags.append({'tag': "Mixed Access" })
        elif "series" and not "lecture" in title:
            tags.append({'tag': "Series" })
        return tags
    
    def caseConversion(self,tag):
        utag = tag.upper()
        if(utag != tag):
            tag = tag.title()
        return tag
    
    #Function to check if record needs to be omitted from Zotero
    def isOmissible(self, title):
        colPre = title.split(':')[0]
        if colPre in colPrefDict.keys() and (colPrefDict[colPre])[0] == 'yes':
            return True
        else:
            return False
    
    #Function to check if colon prefix needs to be stripped from resource title
    def stripRsrc(self, title):
        colPre = title.split(':')[0]
        if colPre in colPrefDict.keys() and (colPrefDict[colPre])[1] == 'yes':
            log.debug('Stripping colon prefix- %s from title string' % colPre)
            return (title.split(':')[1]).strip()
        else:
            return title
    
    #Function get Article object from XML doc obj
    def getArticleFromXML(self, root):
        tags = []
        #Fetch id, title and categories
        id = root.find('{http://www.w3.org/2005/Atom}id').text
        title = unicode(root.find('{http://www.w3.org/2005/Atom}title').text)
        #Check if record needs to be eliminated from zotero OR
        #resource title needs to be stripped
        if ':' in title:
            if self.isOmissible(title):
                log.debug('Omitting record with title- %s' % title)
                return None
            else:
                title = self.stripRsrc(title)
        
        categories = root.findall('{http://www.w3.org/2005/Atom}category')
        tags = self.produceTag(tags, categories, title)
        
        #Fetch HTML content and URL
        content = ''
        url = ''
        if root.find('{http://www.w3.org/2005/Atom}content').text != None:
            soup = BeautifulSoup(root.find('{http://www.w3.org/2005/Atom}content').text)
            content = soup.getText()
            if soup.find('a') != None:
                url = (soup.find('a')).get('href')
                httpObj = httplib2.Http()
                try:
                    resp, content = httpObj.request(url, 'HEAD')
                    if resp['status'] == '404':
                        tags.append({'tag':'404:'+time.strftime("%H-%M-%S")})
                        log.info('Code 404: URL %s broken.' % url)
                    elif resp['status'] == '301':
                        tags.append({'tag':'301:'+time.strftime("%H-%M-%S")},{'tag':'old-url:'+url})
                        log.info('Code 301: URL %s redirecting to %s.' % (url, resp['location']))
                        url = resp['location']
                except socket_error:
                    tags.append({'tag':'111:Connection refused'})
                    log.info('Connection refused: URL %s' % url)                     
        
        blogUrl = root.findall("{http://www.w3.org/2005/Atom}link[@rel='alternate']")[0].attrib['href']
        #Eliminate the first category value(http://../kind#post) that's taken as a tag
        tags.pop(0)
        
        issn = self.getISSNFromXML(root) 
        if issn!=None:
            return Article(id, title, tags, content, url, blogUrl, issn, 'journalArticle')
        else:
            return Article(id, title, tags, content, url, blogUrl, issn, 'webpage')
        
    def extractElementsFromFile(self, fileObj):
        doc = exml.parse(fileObj)
        root = doc.getroot()
        return self.getArticleFromXML(root)

    def extractElementsFromURL(self, url):
        toursurl= urllib2.urlopen(url)
        toursurl_string= toursurl.read()
        root = exml.fromstring(toursurl_string)
        return self.getArticleFromXML(root)    

#Class to create zotero item
class CreateNewZotero:

    #Function to create a zotero record
    def createItem(self, art):
        global recCounter
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

#Create zotero objects from XML files in the local directory by passing its path
def parseDirectory(path):
    log.info('Parsing directory %s' % path)
    x = ParseXML()
    items = glob.glob(path + '/*-atom.xml')
    for i in items:
#         if i not in procFilesList:
        log.info('Now parsing:%s' % i)
        y = x.extractElementsFromFile(i)
        z = CreateNewZotero()
        z.createItem(y)
#         else:
#         log.info('Already processed file:%s' % i)
#         print 'Already processed file:'+i

def main():
    global recCounter
    try:
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-w", "--webpath", help = "web path to XML file", action = "store_true")
        group.add_argument("-l", "--localpath", help = "local path to XML file/ directory", type = str , choices = ['f','d'])
        parser.add_argument ("-v", "--verbose", action="store_true", help="verbose output (i.e., debug logging")
        parser.add_argument("-p", "--path", help = "specify path", type = str)
    #     parser.add_argument("-n", "--numdoc", help = "specify no of documents", type = int, default = -1)
    
        args = parser.parse_args()    
        if args.verbose:
            log.basicConfig(filename=DEFAULTOUTPATH, level=log.DEBUG)
        else:
            log.basicConfig(filename=DEFAULTOUTPATH, level=log.INFO)

        x = ParseXML()
        z = CreateNewZotero()
    
        if(args.webpath):
            y = x.extractElementsFromURL(args.path)
            z.createItem(y)
        else:
            if(args.localpath == 'f'):
                y = x.extractElementsFromFile(args.path)
                z.createItem(y)
            else:
                log.debug('Reading atom XMLs in dir: %s' % args.path)
                parseDirectory(args.path)
        
        log.info(str(recCounter)+" records created in Zotero!")
        print str(recCounter) + ' records created in Zotero!'
    except KeyboardInterrupt, e: # Ctrl-C
        raise e
    except SystemExit, e: # sys.exit()
        raise e
    except Exception, e:
        log.info("********ERROR, UNEXPECTED EXCEPTION********")
        log.info(e)
        log.info("*******************************************")
        traceback.print_exc()
        os._exit(1)

if __name__ == '__main__':
    main()