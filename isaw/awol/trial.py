#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Ronak
#
# Created:     21/04/2014
# Copyright:   (c) Ronak 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import glob

DEFAULTINPATH = "C:\\Users\\Ronak\\Documents\\GitHub\\awol-backup\\";

def main():
    xmlList = glob.glob(DEFAULTINPATH + '*-atom.xml');

    print xmlList[0];
if __name__ == '__main__':
        main()
        #sys.exit(0)
