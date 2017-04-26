#!/usr/bin/python

import sys
import os
import subprocess
import re

stp_cfg_repo = "../../../"  
common_files = "wrat/beans/dpad/"

#############################################################################
# Converts a radio config file to use common files
#############################################################################
def convertFile(filename):
    # Set to True if we are excluding a section of the file
    excluding = False
    with open(filename) as theFile:
        outfile = open('tmpfile', 'w')
        content = theFile.readlines()

        # Patterns for finding stuff we want to change
        if environment == "LN":
            sectorRefPattern = \
                re.compile("ref bean.+node-antenna-sector(\d)-3x(\d)")
        else:
            sectorRefPattern = \
                re.compile("ref bean.+node-antenna-3x(\d)-sector(\d)")
        antennaResourcePattern = \
            re.compile("bean class=\"RadioUnitAntennaResource")
        cellResourcePattern = re.compile("bean class=\"NodeBCellResource")
        branchResourcePattern = \
            re.compile("bean class=\"RadioUnitAntennaBranchResource")
        beanEndPattern = re.compile("</bean>")
        bandPattern = re.compile("frequencyBand")
        cellRefPattern = re.compile("ref bean=\"" + nodenameCell + \
            "_node-S\dC\d")

        for line in content:
            outline = line
            
            if (sectorRefPattern.search(line) or cellRefPattern.search(line)) \
                and not excluding:

                # Replace nodename by DPAD
                outline = line.replace(nodenameCell, "DPAD")

                match = sectorRefPattern.search(line)
                if match:
                    if environment == "LN":
                        sector = match.group(1)
                        numberOfSectors = match.group(2)
                    else:
                        sector = match.group(2)
                        numberOfSectors = match.group(1)

                    outline = outline.replace( "3x" + numberOfSectors + \
                        "-sector" + sector, "sector" + sector + "-3x" + \
                        numberOfSectors)

                    beanFile = "dpad_node_antennaSectors_3x" + \
                               numberOfSectors + ".xml"
                    # Make a link if we haven't done so already
                    if not os.path.exists(beanFile):
                        os.system("ln -s " + stp_cfg_repo + \
                                  common_files + beanFile + " " + beanFile)

            # Change frequency band to 8
            if bandPattern.search(line) and not excluding:
                outline = line.replace("1", "8")

            # Exclude beans found in common files
            if (antennaResourcePattern.search(line) or \
                cellResourcePattern.search(line) or \
                branchResourcePattern.search(line)):
                excluding = True

            if not excluding:
                outfile.write(outline)

            # Stop excluding when we find the end of the bean
            if excluding and beanEndPattern.search(line):
                excluding = False

    os.system("rm " + filename)
    os.system("mv tmpfile " + filename)

#############################################################################
# Replaces node-unique files with links to common files
#############################################################################
def replaceFiles():
    # Remove files
    antennaBranchesFile = nodename + "_antennaBranches.xml"
    cellsFile = nodename + "_cells.xml"

    if os.path.exists(antennaBranchesFile):
        os.system("rm " + antennaBranchesFile)

    if os.path.exists(cellsFile):
        os.system("rm " + cellsFile)

    # Replace with links
    os.system("ln -s " + stp_cfg_repo + \
              common_files + "dpad_node_antennaBranches.xml  " + \
              "dpad_node_antennaBranches.xml")

    os.system("ln -s " +stp_cfg_repo + \
              common_files + "dpad_node_cells.xml dpad_node_cells.xml")

#############################################################################
# Finds and fixes XML files
#############################################################################
def fixRadioConfigs():
    # Find XML files
    p = subprocess.Popen('ls -1', shell=True, stdout=subprocess.PIPE, \
                         stderr=subprocess.STDOUT)

    filenamePattern = re.compile(nodename + ".*.xml")

    for line in p.stdout.readlines():
        if filenamePattern.match(line):
            convertFile(line[:-1])

#=============================================================================
# Now begins the actual script
#=============================================================================

if len(sys.argv) > 2:
    environment = sys.argv[2]
else:
    environment = "LN"
    print "Site is assumed to be LN"

if len(sys.argv) > 1:
    nodename = sys.argv[1]

    if environment == "LI":
        nodenameCell = nodename
    else:
        nodenameCell = nodename.upper()

    replaceFiles()
    fixRadioConfigs()
else:
    print "Usage: python commonator.py <NODENAME> [<SITE>]"
    
