#!/usr/bin/python
import shutil
from listPom import getPomFilenames

for pomFilename in getPomFilenames("pom.xml.backup"):
   print "pom found %s : " % pomFilename
   pomFile = open(pomFilename,'r')
   shutil.copy(pomFilename,pomFilename[:-7])
   updatedPomFile=open(pomFilename[:-7],'w')
   for line in pomFile:
      if "<systemPath" in line:
         updatedPomFile.write(line.replace('\\','/'))
      else:
         updatedPomFile.write(line)

   updatedPomFile.close()
   pomFile.close()
