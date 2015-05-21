# -*- coding: utf-8 -*-
import xml.etree.ElementTree as exml
from bs4 import BeautifulSoup
import urllib2
import logging as log
import re
import httplib2
from socket import error as socket_error
from Article import Article
import ucsv as csv

#Class to extract data from the files
#first method to extract form local file
#seocnd method to extract form url
class ParseXML:
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
        
    #Read content-disposition.csv file and build a dictionary
    dictReader3 = csv.DictReader(open('content-disposition.csv', 'rb'), 
                         fieldnames = ['title', 'title_normalized', 'colonfix', 'single_resource', 'ignore', 'checked', 'multiple_resource', 'url', 'id'], delimiter = ',', quotechar = '"')
    contDispDict = dict()
    #Build a dictionary of format {<id>:[<list of rest of the columns>]}
    for row in dictReader3:
        if row['single_resource'] == 'true':
            contDispDict.update({row['id']:[row['title'], row['title_normalized'], row['colonfix'], row['single_resource'], row['ignore'], row['checked'], row['multiple_resource'], row['url']]})
        
    #############END OF READ CSV#########################
    #Check if multiple tags separated by ',' exist in the titleStringsDict[tag]
    def checkMulTags(self, tag, tags):
        if ',' in tag:
            tagList = tag.split(',')
            for tg in tagList:
                tags.append({'tag': tg })
        else:
            tags.append({'tag' : tag}) 
    
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
            if (tag != '' or tag != None) and ('kind#post' not in tag.lower()):
                if tag in self.titleStringsDict.keys():
                    tag = self.titleStringsDict[tag]
                else:
                    tag = self.caseConversion(tag)
                #Check if multiple tags separated by ',' exist in the titleStringsDict[tag]
                self.checkMulTags(tag, tags)
                print tags
            
        for key in self.titleStringsDict.keys():
            try:
                if title != None and key in title.lower():
                    tag = self.titleStringsDict[key]
                    if tag!= '':
                        self.checkMulTags(tag, tags)
            except Exception, e:
                pass
#                 log.info("Problem with key:%s" % key)
        
        if title != None and "open" and ("access" or "accesss") and not "partially" in title:
            tags.append({u'tag': "Open Access" })
        elif title != None and "open" and ("access" or "accesss") and "partially" in title:
            tags.append({u'tag': "Mixed Access" })
        elif title != None and "series" and not "lecture" in title:
            tags.append({u'tag': "Series" })
        print tags
        return tags
    
    def caseConversion(self,tag):
        utag = tag.upper()
        if(utag != tag):
            tag = tag.title()
        return tag
    
    #Function to check if record needs to be omitted from Zotero
    def isOmissible(self, title):
        colPre = title.split(':')[0]
        if colPre in self.colPrefDict.keys() and (self.colPrefDict[colPre])[0] == 'yes':
            return True
        else:
            return False
    
    #Function to check if colon prefix needs to be stripped from resource title
    def stripRsrc(self, title):
        colPre = title.split(':')[0]
        if colPre in self.colPrefDict.keys() and (self.colPrefDict[colPre])[1] == 'yes':
            log.debug('Stripping colon prefix- %s from title string' % colPre)
            return (title.split(':')[1]).strip()
        else:
            return title
    
    #Function get Article object from XML doc obj
    def getArticleFromXML(self, root):
        tags = []
        #Fetch tagId, title and categories
        tagId = root.find('{http://www.w3.org/2005/Atom}id').text
        if tagId in self.contDispDict.keys():
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
    #         print root.find('{http://www.w3.org/2005/Atom}content').text
            if root.find('{http://www.w3.org/2005/Atom}content').text != None:
                soup = BeautifulSoup(root.find('{http://www.w3.org/2005/Atom}content').text)
                content = soup.getText()
                if soup.find('a') != None:
                    url = (soup.find('a')).get('href')
                    httpObj = httplib2.Http()
                    try:
                        log.debug('Trying URL:%s' % url)
                        resp, httpcontent = httpObj.request(url, 'HEAD')
                        if resp['status'] == '404':
                            tags.append({'tag':'404'})
                            log.info('Code 404: URL %s broken.' % url)
                        elif resp['status'] == '301':
                            tags.append({'tag':'301','tag':'old-url:'+url})
                            log.info('Code 301: URL %s redirecting to %s.' % (url, resp['location']))
                            url = resp['location']
                    except socket_error:
                        tags.append({'tag':'111:Connection refused'})
                        log.info('Connection refused: URL %s' % url)  
                    except httplib2.RedirectLimit as redir_lim:
                        tags.append({'tag':'301'})
                        log.info('Redirect limit reached:'+url)
                        log.info(str(redir_lim))                   
                    except Exception as httpex:
                        tags.append({'tag': str(httpex.__class__.__name__)})
                        log.info(str(httpex)+':'+url)
            else:
                log.info('Content Null:%s' % root.find('{http://www.w3.org/2005/Atom}content').text)
            blogUrl = ''
            tmpList = root.findall("{http://www.w3.org/2005/Atom}link[@rel='alternate']")
            if len(tmpList) > 0:
                blogUrl = tmpList[0].attrib['href']
            #Eliminate the first category value(http://../kind#post) that's taken as a tag
            if 'kind#post' in unicode(str(tags[0]['tag']).lower()): 
                tags.pop(0)
            
            issn = self.getISSNFromXML(root) 
            if issn!=None:
                return Article(tagId, title, tags, content, url, blogUrl, issn, 'journalArticle')
            else:
                return Article(tagId, title, tags, content, url, blogUrl, issn, 'webpage')
        else:
            log.info('Record with tagId: %s excluded as per content-disposition.csv' % tagId)
        
    def extractElementsFromFile(self, fileObj):
        doc = exml.parse(fileObj)
        root = doc.getroot()
        return self.getArticleFromXML(root)

    def extractElementsFromURL(self, url):
        toursurl= urllib2.urlopen(url)
        toursurl_string= toursurl.read()
        root = exml.fromstring(toursurl_string)
        return self.getArticleFromXML(root)    
