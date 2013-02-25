#!/usr/bin/python

import sys
import os
import os.path
import tarfile
import zipfile
import glob
import fnmatch

def locate(pattern, root=os.curdir):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.'''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)

def extract_file(path, to_directory='.'):
    '''Extract compressed file to supplied directory (or current directory if not provided)
    '''
    path=os.path.abspath(path)
    if path.endswith('.zip') or path.endswith('.jar') or path.endswith('.war') or path.endswith('.ear') and zipfile.is_zipfile(path):
        opener, mode = zipfile.ZipFile, 'r'
    elif path.endswith('.tar.gz') or path.endswith('.tgz'):
        opener, mode = tarfile.open, 'r:gz'
    elif path.endswith('.tar.bz2') or path.endswith('.tbz'):
        opener, mode = tarfile.open, 'r:bz2'
    else: 
        raise ValueError, "Could not extract `%s` as no appropriate extractor is found" % path
    
    cwd = os.getcwd()
    os.chdir(to_directory)
    
    try:
        file = opener(path, mode)
        try: 
            file.extractall()
        finally: 
            file.close()
    finally:
        os.chdir(cwd)

def lookForClass(zipFilename,pattern = ''):
    '''Look for a pattern in a zip file
    '''
    opener, mode = zipfile.ZipFile, 'r'
    try:
        file = opener(zipFilename, mode)
        try:
           fileInfos= file.infolist()
           for fileInfo in fileInfos:
              if pattern in fileInfo.filename:
                  print "FOUND : %s : %s" % (zipFilename,fileInfo.filename)
        finally: file.close()
    finally:
        pass

if __name__ == "__main__":

    if len(sys.argv) < 2:
        sys.stderr.write('Usage: '+sys.argv[0]+" <searching path for jar files or ear filepath> <searched pattern>")
        sys.exit(1)

    searchingPath=sys.argv[1]
    if searchingPath[-1:]=='/':
        searchingPath=searchingPath[:-1]
    if not os.path.exists(searchingPath):
        sys.stderr.write('ERROR: %s was not found!' % (searchingPath))
        sys.exit(1)

    pattern = sys.argv[2]
    #EARFILE="EuronetEAR_11.0.00_bDBP1_DB_DC_MERGE_b02.07.ear"
    if searchingPath.endswith(".ear"):
        currentDir=os.getcwd()
        earfile=searchingPath
        dirName=earfile+'.dir'
        if not os.path.exists(dirName):
            os.mkdir(dirName)
        print 'extracting ear archive %s' % earfile
        extract_file(earfile,dirName)
        os.chdir(dirName)
        for warfile in glob.glob('*.war'):
          print 'extracting war archive %s' % warfile
          if not os.path.exists(warfile+".dir"):
             os.mkdir(warfile+".dir")
          extract_file(currentDir+"/"+dirName+'/'+warfile,warfile+".dir")
        os.chdir(currentDir)
        searchingPath=dirName

    for jarFile in locate('*.jar', searchingPath):
        print 'DEBUG : found jar %s' % jarFile
        lookForClass(jarFile,pattern)
