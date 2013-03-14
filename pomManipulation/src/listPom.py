#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
__author__ = 'jean-philippe_hautin'

import glob
import shutil
import sys
import os
import fnmatch

def locate(pattern, root=os.curdir):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.'''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)


def getPomFilenames(filename = "pom.xml",searchRootDirectory = "."):
  pomFilenames = locate(filename,searchRootDirectory)
  finalPomFilenames = [ f for f in pomFilenames if not "/bin/" in f ]
  finalPomFilenames.sort()
  return finalPomFilenames

if __name__ == "__main__":

  if len(sys.argv) < 2:
    sys.stderr.write('Usage: '+sys.argv[0]+" <searching path for pom.xml files>")
    sys.exit(1)

  searchingPath=sys.argv[1]

  if not os.path.exists(searchingPath):
    sys.stderr.write('ERROR: %s was not found!' % (searchingPath))
    sys.exit(1)

  pomFilenames = getPomFilenames(searchRootDirectory=searchingPath)
  print "found %s poms" % len(pomFilenames)
  for pomFilename in pomFilenames:
    print "pom found %s : " % pomFilename[len(searchingPath):]

