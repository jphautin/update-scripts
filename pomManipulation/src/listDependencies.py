#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
__author__ = 'jean-philippe_hautin'

import os
import sys
import string
import shutil
import csv
from listPom import getPomFilenames

from xmlutil import writeXML,ET

POM_NS = "{http://maven.apache.org/POM/4.0.0}"

def dumpDependency(project,dependency):
    global dumpFile
    props = {}
    for element in dependency:
        props[element.tag] = element.text.strip()
    groupId = props["%sgroupId" % (POM_NS)]
    artifactId = props["%sartifactId" % (POM_NS)]
    version = props["%sversion" % (POM_NS)]
    if "%sscope" % (POM_NS) in props:
        scope = props["%sscope" % (POM_NS)]
    else:
        scope = ''
    if "%ssystemPath" % (POM_NS) in props:
        systemPath = props["%ssystemPath" % (POM_NS)]
    else:
        systemPath = ''
    #print "%s,%s,%s,%s,%s" % (groupId,artifactId,version,scope,systemPath)
    dumpFile.write("%s,%s,%s,%s,%s,%s,%s,%s\n" % (project['groupId'],project['artifactId'],project['version'],groupId,artifactId,version,scope,systemPath))

def readPom(pomFilename):
    global dependenciesTranslation
    paths = []
    tree = ET.parse(pomFilename)
    newPomFilename = pomFilename[:-7]
    project={}
    project['groupId']=tree.find("/%sgroupId" % (POM_NS)).text.strip()
    project['artifactId']=tree.find("/%sartifactId"% (POM_NS)).text.strip()
    project['version']=tree.find("/%sversion"% (POM_NS)).text.strip()
    for dependency in tree.findall("//%sdependency" % (POM_NS)):
        dumpDependency(project,dependency)

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

    dumpFile=open(searchingPath+"/direct-dependencies.csv",'wb')
    dumpFile.write("%s,%s,%s,%s,%s,%s,%s,%s\n" % ('project groupId','project artifactId','project version','dependency groupId','dependency artifactId','dependency version','dependency scope','dependency systemPath'))
    pomFilenames = getPomFilenames("pom.xml.backup",searchingPath)

    for pomFilename in pomFilenames:
        print "pom found %s : " % pomFilename
    print
    for pomFilename in pomFilenames:
        readPom(pomFilename)
    dumpFile.close()