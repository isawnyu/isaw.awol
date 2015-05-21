'''
Created on Jun 17, 2014

@author: pavan
'''
from pyzotero import zotero
import json
#creds.json- credentials used to access zotero group library that needs to be populated
creds = json.loads(open('creds.json').read())
zot = zotero.Zotero(creds['libraryID'], creds['libraryType'], creds['apiKey'])
# f = open('backup_b4_del.log','w')
# count = 2 #Count will be equal to (no. of records in zotero)/100
z=zot.everything(zot.items())
# count = len(z)
print 'Retrieved:',
print len(z)
# while count>0:
for item in z:
    print item['key']
#         f.write(str(item))
#         f.write('\n')
    try:
        zot.delete_item(item)
    except Exception, e:
        print e
#     count = count-1
# f.close()