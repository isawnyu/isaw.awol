import httplib2

class ZoteroRESTCalls: 
    # Get the HTTP object
    h = httplib2.Http()
    
    # Send the request
    def createChildAttachment(self, postUrlSuf, parentItem, url, title):
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
        resp, content = self.h.request(postUrl, "POST", params, headers=headers)
        return content

posturlsuf = '/users/1853851/items?key=fQseyjPEdRgQMKo7wEo53Tex'
rest = ZoteroRESTCalls()
rest.createChildAttachment(posturlsuf, '6VHCIQ49', 'http://zotero.com', "test url attachment")