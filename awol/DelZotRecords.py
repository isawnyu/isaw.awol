'''
Created on Jun 17, 2014

@author: pavan
'''
from pyzotero import zotero
import json
#creds.json- credentials used to access zotero group library that needs to be populated
creds = json.loads(open('creds.json').read())
zot = zotero.Zotero(creds['libraryID'], creds['libraryType'], creds['apiKey'])
f = open('backup_b4_del.log','w')
count = 6 #Count will be equal to (no. of records in zotero)/100
while count>0:
    z=zot.items(limit=99)
    print 'Retrieved:',
    print len(z)
    for item in z:
        f.write(str(item))
        f.write('\n')
        zot.delete_item(item)
    print '99 deleted'
    count = count-1
f.close()