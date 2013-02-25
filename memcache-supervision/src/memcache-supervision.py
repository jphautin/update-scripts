#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'jean-philippe_hautin'

import sys
import memcache

def checkConsistency(_stats1,_stats2):
    (server1,stats1)=_stats1[0]
    (server2,stats2)=_stats2[0]
    if stats1['version']!=stats2['version'] or stats1['repcached_version']!=stats2['repcached_version']:
        raise IOError(10,"version of servers are not the same.")
    else:
        print "version : %s, repcached_version: %s " % (stats1['version'],stats1['repcached_version'])

    if stats1['limit_maxbytes']!=stats2['limit_maxbytes']:
        raise IOError(11,"max element size is not consistent.")
    else:
        print "limit_maxbytes : %s " % stats1['limit_maxbytes']

    if stats1['total_items']!=stats2['total_items']:
        sys.stderr.write("%s : %s \n" % (server1,stats1['total_items']))
        sys.stderr.write("%s : %s \n" % (server2,stats2['total_items']))
        raise IOError(12,"replication is not consistent on total items.")
    else:
        print "total_items    : %s " % stats1['total_items']

    if stats1['curr_items']!=stats2['curr_items']:
        raise IOError(13,"replication is not consistent on current items.")
    else:
        print "curr_items     : %s " % stats1['curr_items']

    if stats1['cmd_set']!=stats2['cmd_set']:
        raise IOError(14,"replication is not consistent on cmd_set.")
    else:
        print "cmd_set        : %s " % stats1['cmd_set']



    print "%s : cmd_get : %s " % (server1,stats1['cmd_get'])
    print "%s : cmd_get : %s " % (server2,stats2['cmd_get'])

def readConfiguration(configFilename):
    try:
        configFile=open(configFilename)
        configuration={}
        for line in configFile:
            (key,value) = line.split('=')
            configuration[key]=value.strip()
        return configuration
    except IOError, ioe:
        raise IOError(ioe.errno,"configuration file not found '%s'" % configFilename)

if __name__ == "__main__":

    DEFAULT_CONFIG_FILENAME = "servers.properties"

    if len(sys.argv) < 2:
        sys.stderr.write('Usage: '+sys.argv[0]+" <configuration file>\n")
        print "using default configuration file %s" % DEFAULT_CONFIG_FILENAME
        configurationFilename=DEFAULT_CONFIG_FILENAME
    else:
        configurationFilename=sys.argv[1]
    stats1 = None
    stats2 = None
    try :
        configuration=readConfiguration(configurationFilename)
        mc1 = memcache.Client(['%s:%s' % (configuration['node1.ip'],configuration['node1.port'])], debug=1)
        mc2 = memcache.Client(['%s:%s' % (configuration['node2.ip'],configuration['node2.port'])], debug=1)
        stats1 = mc1.get_stats()
        stats2 = mc2.get_stats()
        checkConsistency(stats1,stats2)
        print '\nOK'
    except IOError, ioe:
        sys.stderr.write("ERROR-%s : %s\n" % ( ioe.errno,ioe.strerror) )
        if stats1!=None:
            print "%r" % stats1
            print "%r" % stats2
        print "\nKO"
        sys.exit(ioe.errno)

