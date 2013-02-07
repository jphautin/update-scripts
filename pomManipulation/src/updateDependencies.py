#!/usr/bin/python2.6
__author__ = 'jean-philippe_hautin'

import sys
import os
import string
import shutil
import csv
from listPom import getPomFilenames

from xmlutil import writeXML,ET

POM_NS = "{http://maven.apache.org/POM/4.0.0}"

OLDGROUPID=3
OLDARTIFACTID=4
OLDVERSION=5
OLDSCOPE=6
OLDSYSTEMPATH=7
NEWGROUPID=8
NEWARTIFACTID=9
NEWVERSION=10
NEWSCOPE=11
NEWCLASSIFER=12

EURONET_PACKAGE="com.raileurope.euronet"

def initDependenciesTranslation():
    global searchingPath
    result = {}
    csvfile=open(searchingPath+'/dependencies-translation.csv','rb')
    csvreader = csv.reader(csvfile)
    for line in csvreader:

        key=getKeyFromElements(line[OLDGROUPID], line[OLDARTIFACTID],  line[OLDVERSION], line[OLDSCOPE])
        print "%s / %s / %s / %s --> %s / %s / %s / %s " % (line[OLDGROUPID], line[OLDARTIFACTID], line[OLDVERSION],line[OLDSCOPE], line[NEWGROUPID], line[NEWARTIFACTID], line[NEWVERSION], line[NEWSCOPE])
        templateDependency={}
        templateDependency['groupId']=line[NEWGROUPID]
        templateDependency['artifactId']=line[NEWARTIFACTID]
        templateDependency['version']=line[NEWVERSION]
        templateDependency['scope']=line[NEWSCOPE]
        templateDependency['classifier']=line[NEWCLASSIFER]
        templateDependency['systemPath']=''
        result[key]=templateDependency
    return result

def getkeyFromProps(props):
    groupId = props["%sgroupId" % (POM_NS)]
    artifactId = props["%sartifactId" % (POM_NS)]
    version = props["%sversion" % (POM_NS)]
    if "%sscope" % (POM_NS) in props:
        scope = props["%sscope" % (POM_NS)]
    else:
        scope=""
    return getKeyFromElements(groupId,artifactId,version,scope)

def getKeyFromElements(groupId,artifactId,version,scope):
    key="%s_%s_%s_%s" % (groupId, artifactId,  version, scope)
    return key

def getDependencyFromTemplateDependency(templateDependency,systemPath):
    dependency={}
    dependency['%sgroupId' % (POM_NS)]=templateDependency['groupId']
    dependency['%sartifactId' % (POM_NS)]=templateDependency['artifactId']
    dependency['%sversion' % (POM_NS)]=templateDependency['version']
    dependency['%ssystemPath' % (POM_NS)]=templateDependency['systemPath']
    dependency['%sscope' % (POM_NS)]=templateDependency['scope']
    dependency['%sclassifier' % (POM_NS)]=templateDependency['classifier']
    if "%version%" in dependency['%sversion' % (POM_NS)]:
        print "looking for version in systemPath %s" % (systemPath)
        (name,version)=systemPath.rsplit("-",1)
        # remove the extension .war, .jar .ear
        version=version[:-4]
        print "found version %s" % (version)
        dependency['%sversion' % (POM_NS)]=dependency['%sversion' % (POM_NS)].replace("%version%",version)
    return dependency

def updateDependency(dependencies,dependency):
    props = {}
    for element in dependency:
        props[element.tag] = element.text
    key=getkeyFromProps(props)
    if key in dependenciesTranslation :
        templateDependency=dependenciesTranslation[key]
        if "%ssystemPath" % (POM_NS) in props:
            systemPath = props["%ssystemPath" % (POM_NS)]
        else:
            systemPath = ''
        newvalue=getDependencyFromTemplateDependency(templateDependency,systemPath)
        for element in dependency:
            if element.tag in newvalue:
                element.text=newvalue[element.tag]
        if  len(newvalue['%sclassifier' % (POM_NS)])!=0:
            classifier=dependency.find("%sclassifier" % (POM_NS))
            if classifier is None:
                classifier=ET.SubElement(dependency,"classifier")
            classifier.text=newvalue['%sclassifier' % (POM_NS)]
        systemPath=dependency.find("%ssystemPath" % (POM_NS))
        scope=dependency.find("%sscope" % (POM_NS))
        artifactId = dependency.find("%sartifactId" % (POM_NS))
        if artifactId.text == "REMOVE":
            print "info : removing dependency %s " % (key)
            dependencies.remove(dependency)
        else:
            if scope is not None:
                if len(scope.text) ==0:
                    dependency.remove(scope)
            if systemPath is not None:
                if len(systemPath.text) ==0:
                    #empty, not looking for dependency in repository (standard way)
                    dependency.remove(systemPath)
                else:
                    #make it work on any system (and not anly Windows)
                    systemPath.text=systemPath.text.replace('\\','/')
    else:
        print "warn : key %s is not tranlated " % (key)

def updatePom(pomFilename):
    global dependenciesTranslation
    paths = []
    tree = ET.parse(pomFilename)
    newPomFilename = pomFilename[:-7]
    dependencies=tree.find("//%sdependencies" % (POM_NS))
    if dependencies is not None :
        for dependency in dependencies.findall("%sdependency" % (POM_NS)):
            updateDependency(dependencies,dependency)
    parentGroupId=tree.find("/%sparent/%sgroupId" % (POM_NS,POM_NS))
    if parentGroupId is not None:
        parentGroupId.text=EURONET_PACKAGE
    currentGroupId=tree.find("%sgroupId" % (POM_NS))
    if currentGroupId is not None:
        currentGroupId.text=EURONET_PACKAGE
    writeXML(tree,open(newPomFilename,'wb'))


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

    dependenciesTranslation = initDependenciesTranslation()
    print
    print
    print
    for pomFilename in getPomFilenames("pom.xml.backup",searchingPath):
        print "pom found %s : " % pomFilename
        updatePom(pomFilename)