#!/usr/local/bin/python3
import os, os.path
import re
import argparse
from pathlib import Path


#meetName = "14th Annual VISAA Division II Invitational"
#shortenSchoolNames = True
DEBUG=False
eventNumIndividual = [3,4,5,6,7,8,11,12,13,14,15,16,19,20,21,22]
eventNumRelay  = [1,2,17,18,23,24]
eventNumDiving = [9,10]



def logger( logString):
    if DEBUG:
        print( logString )

def removeFilesFromDir( directoryName ):
  for root, dirs, files in os.walk(directoryName):
    for file in files:
        os.remove(os.path.join(root, file))  

def generateHeatFiles( heat_sheet_file, output_dir, meet_name, shortenSchoolNames ):
    
    #heat_sheet_file = "../data/mm8heatsheetdefault1col.txt"
    #heat_sheet_file = "../data/mm8-program-txt.txt"
    #output_dir ="../output/"
    
    ## The names are what appear in the report, and may be abbreviated, and not the actual full school name
    schoolNameDict = { 
        "BBVST": "BVST",
        "Broadwater Academy-VA": "BVST",
        "Carmel School Wildcats": "WILD",
        "CCS-VA": "CCS",
        "Christchurch School Swi": "CCS",
        "Fredericksburg Academy-VA": "FAST",
        "Fredericksburg Christian-": "FCS",
        "Hampton Roads Academy": "HRA",
        "Highland Hawks": "HL",
        "Middleburg Academy-VA": "MA",
        "Nansemond Suffolk Academy": "NSA",
        "Oakcrest School Chargers": "OAK",
        "Randolph-Macon Academy-VA": "RMA",
        "Seton Swimming": "SST", 
        "The Covenant School-VA": "TCS" ,
        "The Steward School-VA": "STEW",
        "Trinity Christian School-": "TCS!",
        "Veritas Collegiate Academ": "VCA",
        "Veritas School-VA": "VRTS",
        "Walsingham Academy-VA": "WA",
        "Wakefield H2owls-VA": "WAKE",
        "Williamsburg Christian Ac": "WCA",
    } 
    
    headerLineLong  = "Lane  Name                    Year School      Seed Time"
    headerLineShort = "Lane  Name                 Year School Seed Time"
    headerLineRelay = "Lane  Team                         Relay                   Seed Time"         

    eventNum = 0
    heatNum = 0
    eventLine = ""


    ## Remove files from last run
    removeFilesFromDir( output_dir )
    
    with open(heat_sheet_file, "r") as heat_sheet_file:
        for line in heat_sheet_file:

            ## Remove all the blank lines
            if line != '\n':

                ## Remove the extra newline
                line = line.strip()

                ## Ignore these lines
                if line.lower().startswith((" seton", "seton", "meet", "lane")):
                    continue

                ## Remove meet name from meet
                if re.search(meet_name, line):
                    continue

                ## Start with Event
                if line.lower().startswith(("event")):
                    eventLine = line

                    ## Remove all those extra spaces in the line
                    cleanEventStr = eventLine.split()
                    cleanEventStr = " ".join(cleanEventStr)
                    # Get the line number
                    eventStr = cleanEventStr.split(' ', 4)
                    eventNum = int(eventStr[1].strip())
                    continue


                # Remove "Timed Finals" from Heat line
                if line.lower().startswith(("heat")):
                    line = line.replace("Timed Finals", "")
                    ## Remove all those extra spaces in the line
                    splitHeatStr = line.split()
                    splitHeatStr = " ".join(splitHeatStr)
                    # Get the heat number
                    splitHeatStr = splitHeatStr.split(' ', 4)
                    heatNum = int(splitHeatStr[1])

                    ## Open New file for Event/Heat info
                    logger( f"Event {eventNum}: Heat {heatNum}" )
                    newFileName = output_dir + f"Entry_Event{eventNum:0>2}_Heat{heatNum:0>2}.txt"
                    if eventNum > 0 and heatNum > 0:
                        eventHeatFile = open( newFileName, "w+" )
                        eventHeatFile.write( eventLine  + '\n')

                    
                ## Replace long school name with short name for individual events
                if shortenSchoolNames == True and eventNum in eventNumIndividual:
                    for k,v in schoolNameDict.items():
                        line = line.replace(k.ljust(25,' '), v.ljust(6, ' '))
                        #print( f"just: '{k.ljust(25,' ')} with {v.ljust(6, ' ')}")


                if eventNum > 0 and heatNum > 0:
                    ## Remove space after lane# 10 for formatting
                    line = re.sub('^%s' % '10 ', '10', line)
                    logger(  f"{line}" )
                    eventHeatFile.write(line  + '\n')

                if line.lower().startswith(("heat")):

                    # Determin heading based on short or full school name
                    reportHeader = headerLineLong
                    if shortenSchoolNames and eventNum in eventNumIndividual:
                        reportHeader = headerLineShort
                    
                    ## Special header for relay events
                    if eventNum in eventNumRelay:
                        reportHeader = headerLineRelay

                    logger(  f"{reportHeader}" )
                    eventHeatFile.write( reportHeader + '\n')

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputdir',         dest='inputdir',            default="../data",     required=True, help="input directory for MM extract report")
    parser.add_argument('-m', '--meetname',         dest='meetname',            default="SST Meet",    required=True, help="Name of the meet. Need to remove this from report")
    parser.add_argument('-o', '--outputdir',        dest='outputdir',           default="../output/",  help="output directory for wirecast heat files. MUST CONTAIN TRAILING SLASH")
    parser.add_argument('-s', '--shortschoolnames', dest='shortschoolnames',    action='store_true',   help="Use Short School names for Indiviual Entries")
    parser.add_argument('-l', '--longschoolnames',  dest='shortschoolnames',    action='store_false',  help="Use Long School names for Indiviual Entries")
    parser.add_argument('-d', '--debug',            dest='debug',               action='store_true',   help="Print out results to console")
    parser.set_defaults(shortschoolnames=True)
    parser.set_defaults(DEBUG=False)
    
    args = parser.parse_args()
    
    ## Set global debug flag
    DEBUG = args.debug
    print( f"DEBUG: {Path(__file__).stem}: Parms: InputDir '{args.inputdir}': MeetName '{args.meetname}': OutputDir '{args.outputdir}':  Short School Names: '{args.shortschoolnames}'")

    ## main function to generate heat files for Wirecast
    generateHeatFiles( args.inputdir, args.outputdir, args.meetname, args.shortschoolnames )