#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
__author__ = 'jean-philippe_hautin'


import glob
import shutil
from listPom import getPomFilenames
import os
import sys

if __name__ == "__main__":

    if len(sys.argv) < 2:
        sys.stderr.write('Usage: '+sys.argv[0]+" <searching path for pom.xml files>")
        sys.exit(1)

    searchingPath=sys.argv[1]
    if searchingPath[-1:]=='/':
        searchingPath=searchingPath[:-1]

    if not os.path.exists(searchingPath):
        sys.stderr.write('ERROR: %s was not found!' % (searchingPath))
        sys.exit(1)

    for pomFilename in getPomFilenames("pom.xml",searchingPath):
        print "found pom file %s " %pomFilename
        if os.path.exists(pomFilename+".backup"):
            workingPomFile = pomFilename[:-4]+".dependencies.xml"
            deprecatedUpdatedPomFile = pomFilename+".update"
            if os.path.exists(pomFilename):
                print "remove of pom %s" % pomFilename
                os.remove(pomFilename)
            if os.path.exists(workingPomFile):
                print "remove of pom %s" % workingPomFile
                os.remove(workingPomFile)
            if os.path.exists(deprecatedUpdatedPomFile):
                print "remove of pom %s" % deprecatedUpdatedPomFile
                os.remove(deprecatedUpdatedPomFile)
        else:
            print "can not delete pom %s without a backup file" % pomFilename
