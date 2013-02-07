#!/usr/bin/python
import glob
import shutil
from listPom import getPomFilenames

pomFilenames=getPomFilenames()
for pomFilename in pomFilenames :
  print "backup of pom %s" % pomFilename
  shutil.copy(pomFilename,pomFilename+".backup")
