#!/usr/bin/python

##############################################################################
#
# Script that connects one or several nodes to common DPAD bean files
#
# After running this, remember to connect node to DPAD_NODE-RU* in
# Eris.
#
##############################################################################

import os
import re
import subprocess
import sys

commonFilePath = "../../../wrat/beans/dpad/"
lnName = "rbsln\d+-w\d"
liName = "seliitrbs\d+"
p = subprocess.Popen('echo $USER', shell=True, \
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
user = p.stdout.readline()[:-1]
debug = False

###############################################################################
# Issues a command
#
# If the debug flag is set to True, the command is only written to stdout.
# To be able to test script without doing damage.
#
# @par command A string containg the shell command
###############################################################################
def issueCommand(command):
    if debug:
        print(command + "\n")
    else:
        os.system(command)

###############################################################################
# Cleans a bean file
#
# Removes beans that are to be found in common bean files
#
# @par filename The name of the bean file to clean
# @par nodename Name of the node
# @par site     Site (ln or li)
###############################################################################
def cleanBeans(filename, nodename, site):
    # Set to True if we are excluding a section of the file
    beanExcluding = False
    propExcluding = False
    with open(filename) as theFile:
        outfile = open('tmpfile', 'w')
        content = theFile.readlines()

        # Patterns for finding stuff we want to change
        # Remove RadioUnitResource
        # NodeBRadioConfigurationResource, NodeBSectorResource
        # Also converts RU name to DPAD RU
 
        ruPattern = re.compile("bean class=\"RadioUnitResource")
        configPattern = \
            re.compile("bean class=\"NodeBRadioConfigurationResource")
        sectorPattern = re.compile("bean class=\"NodeBSectorResource")
        beanEndPattern = re.compile("</bean>")
        dataResourcePattern = re.compile("<bean class=\"G2NodeBDataResource.+>")
        radioConfPattern = re.compile("<property name=\"alternativeRadioConfigurations")
        cellsPattern = re.compile("<property name=\"cells")
        sectorsPattern = re.compile("<property name=\"sectors")
        rbsResourcePattern = re.compile("<bean class=\"G2RbsResource.+>")
        radioUnitsPattern = re.compile("<property name=\"radioUnits")
        propertyEndPattern = re.compile("</property>")

        if site == "ln":
            ruNameBase = nodename.upper()
        elif site == "li":
            ruNameBase = nodename.upper().replace("RBS", "DUS")

        ruNamePattern = re.compile("bean=\"" + ruNameBase + "-RU")

        for line in content:
            outline = line

            if ruNamePattern.search(line):
                outline = line.replace(ruNameBase, "DPAD_NODE")

            if dataResourcePattern.search(line):
                outline = line.replace("-NodeBData", "-NodeBData\" parent=\"DPAD_node-NodeBData")

            if rbsResourcePattern.search(line):
                outline = line.replace("_node", "_node\" parent=\"DPAD_node-RbsData")

            # Exclude beans found in common files
            if ruPattern.search(line) or \
               configPattern.search(line) or \
               sectorPattern.search(line):
                beanExcluding = True

            # Exclude properties found in abstract beans
            if not beanExcluding and (radioConfPattern.search(line) or \
               cellsPattern.search(line) or \
               sectorsPattern.search(line) or \
               radioUnitsPattern.search(line)):
                propExcluding = True

            if not (beanExcluding or propExcluding):
                outfile.write(outline)

            # Stop excluding when we find the end of the bean
            if beanExcluding and beanEndPattern.search(line):
                beanExcluding = False
            # or the end of the property
            if propExcluding and propertyEndPattern.search(line):
                propExcluding = False

    if not debug:
        issueCommand("rm " + filename)
        issueCommand("mv tmpfile " + filename)

###############################################################################
# Fixes a node
#
# Removes node unique bean files, makes links to common ones, and removes
# beans from the remaining node-unique bean file
#
# @par nodename Name of the node to fix (in lowercase)
###############################################################################
def fixNode(nodename):
    if re.compile(lnName).match(nodename):
        site = "ln"
    elif re.compile(liName).match(nodename):
        site = "li"
    else:
        site = "UNDEFINED"

    nodepath = ("/workspace/git/" + user + "/wrat/build/stp_cfg/" + \
                    site + "/" + nodename + "/beans/")

    issueCommand("rm " + nodepath + "dpad_node_antennaBranches.xml")
    issueCommand("ln -s " + commonFilePath + "dpad_node_commonBeans.xml " + \
              nodepath + "dpad_node_commonBeans.xml")
    issueCommand("git add " + nodepath + "dpad_node_commonBeans.xml")
    issueCommand("rm " + nodepath + "dpad_node_cells.xml")

    p = subprocess.Popen('ls -1 ' + nodepath + \
                         'dpad_node_antennaSectors_3x*.xml', shell=True, \
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    for line in p.stdout.readlines():
        issueCommand( "rm " + line[:-1])

    if site == "ln":
        # Remove configuration files
        p = subprocess.Popen('ls -1 ' + nodepath + nodename + "_3x*.xml", \
                         shell=True, \
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        for line in p.stdout.readlines():
            issueCommand("rm " + line[:-1])

    # Convert remaining file. 
    cleanBeans(nodepath + nodename + ".xml", nodename, site)

###############################################################################
# Deduce the nodename if run without arguments
# If we run without arguments, we have to be in the right directory
if len(sys.argv) == 1:
    directory = os.getcwd()
    nodenamePattern = re.compile("/(" + lnName + "|" + liName + ")/beans")
    nodenameMatch = nodenamePattern.search(directory)

    if nodenameMatch:
        fixNode(nodenameMatch.group(1))

# Or else, we assume that we have been given a list of node names
else:
    for node in range(1, len(sys.argv)):
        fixNode(sys.argv[node].lower())

issueCommand("git add -u")

