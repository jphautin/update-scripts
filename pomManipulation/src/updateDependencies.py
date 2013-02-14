#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
__author__ = 'jean-philippe_hautin'

import sys
import os
import string
import shutil
import csv
from listPom import getPomFilenames

from xmlutil import writeXML,ET

POM_NS = "{http://maven.apache.org/POM/4.0.0}"

#structure of dependencies-translation.csv
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

#structure of pom.missing.dependencies.csv
ADDGROUPID=0
ADDARTIFACTID=1
ADDVERSION=2
ADDSCOPE=3
ADDCLASSIFIER=4

#Parent package of every pom (most probably company package)
EURONET_PACKAGE="com.raileurope.euronet"

def initDependenciesTranslation():
    global searchingPath
    result = {}
    csvfile=open(searchingPath+'/dependencies-translation.csv','rb')
    csvreader = csv.reader(csvfile)
    for line in csvreader:

        key=getKeyFromElements(line[OLDGROUPID], line[OLDARTIFACTID],  line[OLDVERSION], line[OLDSCOPE])
        #print "%s / %s / %s / %s --> %s / %s / %s / %s " % (line[OLDGROUPID], line[OLDARTIFACTID], line[OLDVERSION],line[OLDSCOPE], line[NEWGROUPID], line[NEWARTIFACTID], line[NEWVERSION], line[NEWSCOPE])
        templateDependency={}
        templateDependency['groupId']=line[NEWGROUPID]
        templateDependency['artifactId']=line[NEWARTIFACTID]
        templateDependency['version']=line[NEWVERSION]
        templateDependency['scope']=line[NEWSCOPE]
        templateDependency['classifier']=line[NEWCLASSIFER]
        templateDependency['systemPath']=''
        if len(templateDependency['artifactId'])>0:
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
        #print "looking for version in systemPath %s" % (systemPath)
        (name,version)=systemPath.rsplit("-",1)
        # remove the extension .war, .jar .ear
        version=version[:-4]
        #print "found version %s" % (version)
        dependency['%sversion' % (POM_NS)]=dependency['%sversion' % (POM_NS)].replace("%version%",version)
    return dependency

def updateDependency(dependencies,dependency):
    props = {}
    for element in dependency:
        props[element.tag] = element.text.strip()
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
            #print "info : removing dependency %s " % (key)
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


def updateDependencies(tree):
    dependenciesNodes=tree.findall("//%sdependencies" % (POM_NS))
    for dependencies in dependenciesNodes :
        if dependencies is not None :
            print "update dependencies"
            for dependency in dependencies.findall("%sdependency" % (POM_NS)):
                updateDependency(dependencies,dependency)

def addMissingDependency(tree,line):
    projectDependenciesNode=tree.find("/%sdependencies" % (POM_NS))
    if projectDependenciesNode is not None :
        print "adding dependency %r " % line
        addedDependencyNode=ET.SubElement(projectDependenciesNode,"%sdependency" % (POM_NS))
        ET.SubElement(addedDependencyNode,"%sgroupId" % (POM_NS)).text=line[ADDGROUPID]
        ET.SubElement(addedDependencyNode,"%sartifactId" % (POM_NS)).text=line[ADDARTIFACTID]
        ET.SubElement(addedDependencyNode,"%sversion" % (POM_NS)).text=line[ADDVERSION]
        scope=line[ADDSCOPE]
        if scope is not None and len(scope)>0:
            ET.SubElement(addedDependencyNode,"%sscope" % (POM_NS)).text=scope
        classifier=line[ADDCLASSIFIER]
        if classifier is not None and len(classifier)>0:
            ET.SubElement(addedDependencyNode,"%sclassifier" % (POM_NS)).text=classifier



def addMissingDependencies(tree,pomFilename):
    directory=os.path.dirname(os.path.realpath(pomFilename))
    missingDependenciesFileName=directory+"/pom.missing.dependencies.csv"
    if os.path.exists(missingDependenciesFileName):
        csvMissingDepsFile=open(missingDependenciesFileName,'rb')
        csvreader = csv.reader(csvMissingDepsFile)
        for line in csvreader:
            addMissingDependency(tree,line)

def updateExpressions(pomFilename):
    shutil.copy(pomFilename,pomFilename[:-4]+".dependencies.xml")
    pomFile = open(pomFilename[:-4]+".dependencies.xml",'r')
    updatedPomFile=open(pomFilename,'w')
    for line in pomFile:
        # deprecated expression in maven 3.x
        if "${artifactId}" in line:
            line=line.replace('${artifactId}','${project.artifactId}')
        if "${groupId}" in line:
            line=line.replace('${groupId}','${project.groupId}')
        if "${pom.version}" in line:
            line=line.replace('${pom.version}','${project.version}')
        if "${pom.name}" in line:
            line=line.replace('${pom.name}','${project.name}')
            #update path to use java separator and not windows separator (will not work on Linux Integration Server :) )
        if "<systemPath" in line:
            line=line.replace('\\','/')
        updatedPomFile.write(line)
    updatedPomFile.close()
    pomFile.close()

def retrieveParentGroupId(pomFilename,artifactId):
    absolutePathName= os.path.abspath(pomFilename)
    result=retrieveGroupId(pomFilename,artifactId)
    #le parent d'un core ne peut être que un assembly.
    if EURONET_PACKAGE+".core" in result:
        return EURONET_PACKAGE+".core.assembly"
    else:
        return result

def retrieveGroupId(pomFilename,artifactId):
    absolutePathName= os.path.abspath(pomFilename)
    if artifactId.text == "version_update" or artifactId.text == "commons" :
        return EURONET_PACKAGE+".commons"
    elif "vault" in absolutePathName:
        return  EURONET_PACKAGE+".vault"
    elif "BR_WS_DEV_" in absolutePathName:
        return  EURONET_PACKAGE+".ws"
    elif "BR_EURONETFO_DEV_" in absolutePathName:
        if "EuronetBuild" in absolutePathName:
            return EURONET_PACKAGE+".core.assembly"
        else:
            return EURONET_PACKAGE+".core"
    elif "BR_DET_DEV_" in absolutePathName:
        return  EURONET_PACKAGE+".det"
    else:
        print "warn : return default package for pom file %s " % pomFilename
        return  EURONET_PACKAGE

def updateParentReference(tree,pomFilename,correctedVersion):
    print "update parent reference"
    parentGroupId=tree.find("/%sparent/%sgroupId" % (POM_NS,POM_NS))
    parentArtifactId=tree.find("/%sparent/%sartifactId" % (POM_NS,POM_NS))
    parentVersion= tree.find("/%sparent/%sversion" % (POM_NS,POM_NS))
    if parentGroupId is not None:
        parentGroupId.text=retrieveParentGroupId(pomFilename,parentArtifactId)
        parentVersion.text=correctedVersion

def updateCurrentReference(tree,pomFilename,correctedVersion):
    print "update current reference"
    currentGroupId=tree.find("%sgroupId" % (POM_NS))
    currentArtifactId=tree.find("%sartifactId" % (POM_NS))
    currentVersion=tree.find("%sversion" % (POM_NS))
    if currentGroupId is not None:
        currentGroupId.text=retrieveGroupId(pomFilename,currentArtifactId)
        currentVersion.text=correctedVersion

def updateDistributionManagement(tree):
    if tree.find("/%sparent" % (POM_NS)) is None:
        propertiesNode = tree.find("/%sproperties" % (POM_NS))
        if propertiesNode is None:
            propertiesNode = ET.SubElement(tree.getroot(),"properties")
        ET.SubElement(propertiesNode,"repository.releases.url").text="http://localhost:8080/nexus/content/repositories/releases"
        ET.SubElement(propertiesNode,"repository.snapshots.url").text="http://localhost:8080/nexus/content/repositories/snapshots"
        distributionManagementNode = ET.SubElement(tree.getroot(),"distributionManagement")
        repositoryNode = ET.SubElement(distributionManagementNode,"repository")
        ET.SubElement(repositoryNode,"id").text="nexus"
        ET.SubElement(repositoryNode,"name").text="internal release repository"
        ET.SubElement(repositoryNode,"url").text="${repository.releases.url}"
        snapshotRepositoryNode = ET.SubElement(distributionManagementNode,"snapshotRepository")
        ET.SubElement(snapshotRepositoryNode,"id").text="nexus"
        ET.SubElement(snapshotRepositoryNode,"name").text="internal release repository"
        ET.SubElement(snapshotRepositoryNode,"url").text="${repository.snapshots.url}"



def updatePom(pomFilename,correctedVersion):
    global dependenciesTranslation
    paths = []
    tree = ET.parse(pomFilename)
    newPomFilename = pomFilename[:-7]
    updateDependencies(tree)
    addMissingDependencies(tree,pomFilename)
    updateParentReference(tree,pomFilename,correctedVersion)
    updateCurrentReference(tree,pomFilename,correctedVersion)
    pomFile=open(newPomFilename,'wb')
    updateDistributionManagement(tree)
    writeXML(tree,pomFile)
    pomFile.close()
    updateExpressions(newPomFilename)

if __name__ == "__main__":

    if len(sys.argv) < 3:
        sys.stderr.write('Usage: '+sys.argv[0]+" <searching path for pom.xml files> <snapshot version>")
        sys.exit(1)

    searchingPath=sys.argv[1]
    correctedVersion=sys.argv[2]
    if searchingPath[-1:]=='/':
        searchingPath=searchingPath[:-1]

    if not os.path.exists(searchingPath):
        sys.stderr.write('ERROR: %s was not found!' % (searchingPath))
        sys.exit(1)

    try:
        dependenciesTranslation = initDependenciesTranslation()
        print
        print
        print
        for pomFilename in getPomFilenames("pom.xml.backup",searchingPath):
            print "updating pom  %s ..." % pomFilename
            updatePom(pomFilename,correctedVersion)
    except IOError, e:
        print
        print "error: check the file 'dependencies-translation.csv' exists in the searching directory"
