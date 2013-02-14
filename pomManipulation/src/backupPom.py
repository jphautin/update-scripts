#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
__author__ = 'jean-philippe_hautin'

import glob
import shutil
from listPom import getPomFilenames

pomFilenames=getPomFilenames()
for pomFilename in pomFilenames :
  print "backup of pom %s" % pomFilename
  shutil.copy(pomFilename,pomFilename+".backup")
