#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
__author__ = 'jean-philippe_hautin'

import shutil
from listPom import getPomFilenames

for pomFilename in getPomFilenames("pom.xml.backup"):
   print "pom found %s : " % pomFilename
   pomFile = open(pomFilename,'r')
   shutil.copy(pomFilename,pomFilename[:-7])
   updatedPomFile=open(pomFilename[:-7],'w')
   for line in pomFile:
      # deprecated expression in maven 3.x
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
