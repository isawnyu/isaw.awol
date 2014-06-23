'''
Created on Jun 19, 2014

@author: Pavan
'''
import httplib2

# Get the HTTP object
h = httplib2.Http()        

# Send the request
def createChildAttachment(postUrlSuf, parentItem, url, title):
    headers = {'Content-Type' : 'application/json',
               'Zotero-API-Version': '2'}
    params ="""{
      "items": [
        {
          "itemType": "attachment",
          "parentItem": \""""+parentItem+"""\",
          "linkMode": "imported_url",
          "title": \""""+title+"""\",
          "accessDate": "",
          "url": \""""+url+"""\",
          "tags": []
        }
      ]
    }
    """
    postUrl = 'https://api.zotero.org'+postUrlSuf
    resp, content = h.request(postUrl, "POST", params, headers=headers)
    return content

posturlsuf = '/users/1853851/items?key=fQseyjPEdRgQMKo7wEo53Tex'
 
createChildAttachment(posturlsuf, '6VHCIQ49', 'http://zotero.com', "test url attachment")