#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
__author__ = 'jean-philippe_hautin'

import sys
import os
import glob
import shutil
from listPom import getPomFilenames

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
  	print "backup of pom %s" % pomFilename
  	shutil.copy(pomFilename,pomFilename+".backup")
