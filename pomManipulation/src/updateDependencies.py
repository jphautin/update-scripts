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

NEXUS_URL="http://iceuronet:8081/nexus"

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
        #key2=getKeyFromElements(line[OLDGROUPID].lower(), line[OLDARTIFACTID],  line[OLDVERSION], line[OLDSCOPE])
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
           #result[key2]=templateDependency

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
    key="%s_%s_%s" % ( artifactId,  version, scope)
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
        #print "found version %s" % (version)
        dependency['%sversion' % (POM_NS)]=dependency['%sversion' % (POM_NS)].replace("%version%",version)
    return dependency

def updateDependency(dependencies,dependency,correctedVersion):
    global dependenciesTranslation
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
        # on met a jour touts les elements existants
        for element in dependency:
            if element.tag in newvalue:
                element.text=newvalue[element.tag]
        #On ajoute en tag classifier s'il n'existe pas dans l'arbre
        #puis on mets a jour avec la bonne valeur
        if  len(newvalue['%sclassifier' % (POM_NS)])!=0:
            classifier=dependency.find("%sclassifier" % (POM_NS))
            if classifier is None:
                classifier=ET.SubElement(dependency,"classifier")
            classifier.text=newvalue['%sclassifier' % (POM_NS)]
        systemPath=dependency.find("%ssystemPath" % (POM_NS))
        scope=dependency.find("%sscope" % (POM_NS))
        artifactId = dependency.find("%sartifactId" % (POM_NS))
        #On supprime la dépendence si nécessaire
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
        #print "warn keys are %r" % list(dependenciesTranslation)


def updateDependencies(tree,correctedVersion):
    dependenciesNodes=tree.findall("//%sdependencies" % (POM_NS))
    for dependencies in dependenciesNodes :
        if dependencies is not None :
            print "update dependencies"
            for dependency in dependencies.findall("%sdependency" % (POM_NS)):
                updateDependency(dependencies,dependency,correctedVersion)

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
        ## PATCH FOR case sensitive module non correctly spelled.
        if "atbServerassembly" in line:
            line=line.replace("atbServerassembly","atbserverassembly")
        ##END PATCH
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
        if "src\\assembly" in line:
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
    elif "webservices" in absolutePathName:
        if "delivery" in absolutePathName:
            return EURONET_PACKAGE+".ws.delivery"
        else:
            return  EURONET_PACKAGE+".ws"
    elif "euronet_fo" in absolutePathName:
        if "EuronetBuild" in absolutePathName:
            return EURONET_PACKAGE+".core.assembly"
        elif "delivery" in absolutePathName:
            return EURONET_PACKAGE+".core.delivery"
        else:
            return EURONET_PACKAGE+".core"
    elif "det_sphere" in absolutePathName:
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
        ET.SubElement(propertiesNode,"repository.releases.url").text=NEXUS_URL+"/content/repositories/releases"
        ET.SubElement(propertiesNode,"repository.snapshots.url").text=NEXUS_URL+"/content/repositories/snapshots"
        distributionManagementNode = ET.SubElement(tree.getroot(),"distributionManagement")
        repositoryNode = ET.SubElement(distributionManagementNode,"repository")
        ET.SubElement(repositoryNode,"id").text="nexus"
        ET.SubElement(repositoryNode,"name").text="internal release repository"
        ET.SubElement(repositoryNode,"url").text="${repository.releases.url}"
        snapshotRepositoryNode = ET.SubElement(distributionManagementNode,"snapshotRepository")
        ET.SubElement(snapshotRepositoryNode,"id").text="nexus"
        ET.SubElement(snapshotRepositoryNode,"name").text="internal release repository"
        ET.SubElement(snapshotRepositoryNode,"url").text="${repository.snapshots.url}"


def updateEARGroupModules(tree):
    '''
    ' Update EAR Module for application.xml generation
    '''
    currentGroupId=tree.find("%sgroupId" % (POM_NS))
    currentArtifactId=tree.find("%sartifactId" % (POM_NS))
    if currentGroupId.text == 'com.raileurope.euronet.core' and 'EAR' in currentArtifactId.text:
        modulesNode = tree.find("//%smodules" % (POM_NS))
        for groupIdNode in modulesNode.findall("*/%sgroupId" % (POM_NS)):
            groupIdNode.text='com.raileurope.euronet.core'


def updateNames(tree):
    '''
    '  Update name with value ${project.artifactId}
    '  Update finaName with value ${project.artifactId}
    '''
    nameNode = tree.find("%sname" % POM_NS )
    if nameNode is not None:
        nameNode.text='${project.artifactId}'
    finaNameNode=tree.find("%sbuild/%sfinalName" % (POM_NS,POM_NS) )
    if finaNameNode is not None:
        finaNameNode.text='${project.artifactId}-${project.version}'

def updateVersionUpdatePom(tree,correctedVersion):
    '''
    ' PATCH TO SET CORRECT SNAPSHOT VERSION IN VERSION_UPDATE file.
    ' this project should disappear in the target build system
    '''
    currentArtifactId=tree.find("%sartifactId" % (POM_NS))
    if currentArtifactId.text == "version_update":
        print 'update version_update POM (PATCH)'
        wsVersionNode=tree.find("%sproperties/%sws_version" % (POM_NS,POM_NS) )
        wsVersionNode.text=correctedVersion
        commonsVersionNode=tree.find("%sproperties/%scommons_version" % (POM_NS,POM_NS) )
        commonsVersionNode.text=correctedVersion
        passVersionNode=tree.find("%sproperties/%spass_version" % (POM_NS,POM_NS) )
        passVersionNode.text=correctedVersion
        vaultVersionNode=tree.find("%sproperties/%svault_version" % (POM_NS,POM_NS) )
        vaultVersionNode.text=correctedVersion
        euronetCoreNode=tree.find("%sproperties/%seuronet_jar_version" % (POM_NS,POM_NS) )
        euronetCoreNode.text="11.0-SNAPSHOT"

def updateServerGenPom(tree):
    '''
    ' PATCH TO SET correct mainClass of project
    '''
    currentArtifactId=tree.find("%sartifactId" % (POM_NS))
    if currentArtifactId.text == "server-gen":
        print 'update server-gen POM (PATCH)'
        #
        # wanted xpath expression not supported :(
        # //%sartifactId[text()='exec-maven-plugin']/../configuration
        #
        artifactIdNodes=tree.findall("//%sartifactId" % POM_NS)
        for artifactIdNode in artifactIdNodes:
            if artifactIdNode.text == "exec-maven-plugin" :
                configurationNode=artifactIdNode.find("../%sconfiguration" % POM_NS)
                classpathScope=configurationNode.find("%sclasspathScope"  % POM_NS)
                executableDependency=configurationNode.find("%sexecutableDependency"  % POM_NS)
                mainClass=configurationNode.find("%smainClass" % POM_NS)
                mainClass.text="com.raileurope.web.ServerMaker"
                configurationNode.remove(classpathScope)
                configurationNode.remove(executableDependency)
                ibmj2eeJar=["com.ibm","j2ee","7.0","",""]
                addMissingDependency(tree,ibmj2eeJar)


def updateGenPoms(tree):
    '''
    '  PATCH TO REMOVE UNNEEDED PLUGIN DEPENDENCY
    '''
    currentArtifactId=tree.find("%sartifactId" % (POM_NS))
    if currentArtifactId.text == "schema-gen-pom" or currentArtifactId.text == "interface-gen-pom":
        print 'update %s POM (PATCH)' % currentArtifactId.text
        #
        # wanted xpath expression not supported :(
        # //%sartifactId[text()='xml-maven-plugin']/../dependencies
        #
        artifactIdNodes=tree.findall("//%sartifactId" % POM_NS)
        for artifactIdNode in artifactIdNodes:
            if artifactIdNode.text == "xml-maven-plugin" :
                dependenciesNode=artifactIdNode.find("../%sdependencies" % POM_NS)
                dependencyNodes=dependenciesNode.findall("%sdependency" % POM_NS)
                for dependencyNode in dependencyNodes:
                    currentArtifactIdNode=dependencyNode.find("%sartifactId" % POM_NS)
                    if currentArtifactIdNode.text=="mtxslt":
                        dependenciesNode.remove(dependencyNode)

def updatePom(pomFilename,correctedVersion):
    global dependenciesTranslation
    paths = []
    tree = ET.parse(pomFilename)
    newPomFilename = pomFilename[:-7]
    updateDependencies(tree,correctedVersion)
    addMissingDependencies(tree,pomFilename)
    updateParentReference(tree,pomFilename,correctedVersion)
    updateCurrentReference(tree,pomFilename,correctedVersion)
    updateNames(tree)
    updateEARGroupModules(tree)
    updateVersionUpdatePom(tree,correctedVersion)
    updateServerGenPom(tree)
    updateGenPoms(tree)
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
