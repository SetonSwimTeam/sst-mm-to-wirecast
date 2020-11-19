#!/usr/local/bin/python3

#############################################################################################
#############################################################################################
###
### generate_heat_files
###  Given a Meet Manager generated Meet Program, exported as a TXT file
###   create individual files for every event/heat, with cleaned up text 
###   for optimal visualization on the live webcast for the WireCast application
###
#############################################################################################
#############################################################################################

import os, os.path
import re
import argparse
from pathlib import Path


## Globals
DEBUG=False

eventNumIndividual = [3,4,5,6,7,8,11,12,13,14,15,16,19,20,21,22]
eventNumRelay  = [1,2,17,18,23,24]
eventNumDiving = [9,10]

schoolNameDict = { 
        "Benedictine College Prep": "BCP",
        "Bishop O'Connell-PV": "DJO",
        "Bishop Ireton Swim and Di": "BI",
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
        "Saint John Paul the Great": "JP",
        "St. Gertrude High School": "SGHS",
        "St. Paul VI Catholic HS": "PVI",
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
    

def logger( log_string ):
    """ Prints out logs if DEBUG command line parm was enabled """
    if DEBUG:
        print( log_string )

def removeFilesFromDir( directoryName ):
    """ Remove files from previous run/meet so there are no extra heats/events left over"""
    for root, dirs, files in os.walk(directoryName):
        for file in files:
            os.remove(os.path.join(root, file))  


def create_event_heat_file( eventNum, heatNum, relaySplitFile ):
    """ Generate the filename and open the next file """
    if eventNum in eventNumRelay:
        eventHeatFileName = output_dir + f"Entry_Event{eventNum:0>2}_Heat{heatNum:0>2}_{relaySplitFile:0>2}.txt"
    else:
        eventHeatFileName = output_dir + f"Entry_Event{eventNum:0>2}_Heat{heatNum:0>2}.txt"
    eventHeatFile = open( eventHeatFileName, "w+" )
    return eventHeatFile


def generateHeatFiles( heat_sheet_file, output_dir, meet_name, shortenSchoolNames, splitRelaysToMultipleFiles, addNewLineToRelayEntries ):
    """ Given the input file formatted in a specific manner,
        generate indiviual Event/Heat files for use in Wirecast displays """
    
    #####################################################################################
    ## The names are what appear in the report, and may be abbreviated, 
    ##  and not the actual full school name
    ## Multiple version of a school may be listed here for clean output
    #####################################################################################
    schoolNameDictFullNameLen = 25
    schoolNameDictShortNameLen = 6  # Four character name plus spaces for padding between EntryTime


    ## NOTE: Do not align up these headers with the TXT output.  
    ##  Wirecast will center all lines and it will be in proper position then
    headerLineLong  = "Lane  Name                    Year School      Seed Time"
    headerLineShort = "Lane  Name                 Year School Seed Time"
    headerLineRelay = "Lane  Team                         Relay                   Seed Time"         


    ## Define local variables
    eventNum = 0
    heatNum = 0
    eventLine = ""
    heatLine = ""

    num_heats_files_generated=0
    total_files_generated=0
    ## Remove files from last run
    removeFilesFromDir( output_dir )
    
    with open(heat_sheet_file, "r") as heat_sheet_file:
        for line in heat_sheet_file:

            #####################################################################################
            ## Ignore all the blank lines             
            #####################################################################################
            if line == '\n':
                continue

            #####################################################################################
            ## Ignore these meet program header lines                
            #####################################################################################
            # if line.lower().startswith((" seton", "seton", "meet", "lane")):
            #     continue

            if re.search("^(\s+)Seton School", line):
                continue
            if re.search("^(\s+)Meet Program", line):
                continue
            if re.search("^(\s*)Lane(\s+)Team", line):
                continue

            #####################################################################################
            ## Ignore meet name line from output
            #####################################################################################
            if re.search(meet_name, line):
                continue

            #####################################################################################
            ## Remove the extra newline at end of line
            #####################################################################################
            line = line.strip()

            #####################################################################################
            ## Start with Event line.  Clean it up
            #####################################################################################
            if line.lower().startswith(("event")):
                eventLine = line

                ## Remove all those extra spaces in the line
                cleanEventStr = eventLine.split()
                cleanEventStr = " ".join(cleanEventStr)
                # Get the line number
                eventStr = cleanEventStr.split(' ', 4)
                eventNum = int(eventStr[1].strip())
                continue

            #####################################################################################
            ## Remove "Timed Finals" from Heat (and flight) line
            #####################################################################################
            if line.lower().startswith(("heat", "flight")):
                line = line.replace("Timed Finals", "")
                ## Remove all those extra spaces in the line
                splitHeatStr = line.split()
                splitHeatStr = " ".join(splitHeatStr)

                # Get the heat/flight number
                splitHeatStr = splitHeatStr.split(' ', 4)
                heatNum = int(splitHeatStr[1])

            #####################################################################################
            ## Remove space after lane# 10 for formatting so names all align up evenly
            ## 10 must be on the beginning of the line 
            #####################################################################################
            if eventNum not in eventNumDiving:
                line = re.sub('^%s' % '10 ', '10', line)

            #####################################################################################
            ## For Diving Events, remove extra space from diver # 10 and above for formatting 
            ## so names lines up with diver 1-9
            #####################################################################################
            if eventNum in eventNumDiving:
                matched = re.search('^(\d\d) ', line)
                if matched:
                    line = re.sub('^(\d\d) ', r'\1',line )

            #####################################################################################
            ## Processing specific to Individual Entries
            #####################################################################################
            ## Replace long school name with short name for individual events
            if shortenSchoolNames == True and eventNum in eventNumIndividual:
                for k,v in schoolNameDict.items():
                    line = line.replace(k.ljust(schoolNameDictFullNameLen,' '), v.ljust(schoolNameDictShortNameLen, ' '))
            
            #####################################################################################
            ## Processing specific to RELAY Entries
            #####################################################################################
            ## If this is a relay, see if there are spaces between swimmer numbers
            ## If so, add a space between the last swimmer name and the next swimmer number
            ## This line  1) LastName1, All2) LastName2, Ashley3) LastName3, All4) LastName4, Eri
            ## becomes    1) LastName1, All 2) LastName2, Ashley 3) LastName3, All 4) LastName4, Eri
            if eventNum in eventNumRelay:
                m = re.search('\S[2-4]\)',line)
                if m:
                    line = re.sub(r'(\S)([2-4]\))', r'\1 \2',line )

                ## IF we are splitting replays into multiple file, then put a blank line between each lane
                if addNewLineToRelayEntries and (re.search('^\d ', line) or re.search('^\d\d ', line)):
                    line = f"\n{line}"


            #####################################################################################
            #####################################################################################
            #####
            ##### Done updating.formatting lines, start outputing data
            #####
            #####################################################################################
            #####################################################################################
    
            #####################################################################################
            ## Start a new Output Event/Heat file 
            ##      Heats are used for swimming.  
            ##      Flights are used for diving events
            #####################################################################################
            if line.lower().startswith(("heat", "flight")):
                ## Open New file for Event/Heat info
                num_heats_files_generated += 1
                total_files_generated += 1
                heatLine = line
                if eventNum > 0 and heatNum > 0:
                    eventHeatFile = create_event_heat_file( eventNum, heatNum, 1 )

                    ## Every New file starts with Event Number/Name
                    eventHeatFile.write( eventLine  + '\n')
            
            #####################################################################################
            ## Relays with at least 6 lanes, split the result up in two files
            ## Manually added the Event/Heat and Header info into second file
            #####################################################################################
            if splitRelaysToMultipleFiles and eventNum in eventNumRelay:
                if (addNewLineToRelayEntries and re.search('^\n6 ', line)) or (not addNewLineToRelayEntries and re.search('^6 ', line)):
                    ## Look for lane Relay 5
                    total_files_generated += 1 
                    eventHeatFile = create_event_heat_file( eventNum, heatNum, 2 )
                    eventHeatFile.write( eventLine  + '\n')
                    eventHeatFile.write( heatLine  + '\n')
                    eventHeatFile.write( headerLineRelay  + '\n')


            if eventNum > 0 and heatNum > 0:
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

    return num_heats_files_generated, total_files_generated



#####################################################################################
#####################################################################################
##  M A I N
#####################################################################################
#####################################################################################
if __name__ == "__main__":

    #####################################################################################
    ## Parse out command line arguments
    #####################################################################################
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputdir',         dest='inputdir',            default="../data",     required=True,   help="input directory for MM extract report")
    parser.add_argument('-m', '--meetname',         dest='meetname',            default="SST Meet",    required=True,   help="Name of the meet. Need to remove this from report")
    parser.add_argument('-o', '--outputdir',        dest='outputdir',           default="../output/",                   help="output directory for wirecast heat files.")
    parser.add_argument('-s', '--shortschoolnames', dest='shortschoolnames',    action='store_true',                    help="Use Short School names for Indiviual Entries")
    parser.add_argument('-l', '--longschoolnames',  dest='shortschoolnames',    action='store_false',                   help="Use Long School names for Indiviual Entries")
    parser.add_argument('-r', '--splitrelays',      dest='splitrelays',         action='store_true',                   help="Split Relays into multiple files")
    parser.add_argument('-n', '--spacerelaynames',  dest='spacerelaynames',     action='store_true',                   help="Add a new line between relay names")
    parser.add_argument('-d', '--debug',            dest='debug',               action='store_true',                    help="Print out results to console")
    parser.set_defaults(shortschoolnames=True)
    parser.set_defaults(splitrelays=False)
    parser.set_defaults(spacerelaynames=False)
    parser.set_defaults(DEBUG=False)
    
    args = parser.parse_args()
    
    ## Set global debug flag
    DEBUG = args.debug

    output_dir = args.outputdir
    ## The outputdir string MUST have a trailing slash.  Check string and add it if necesssary
    if output_dir[-1] != '/':
        output_dir = f"{output_dir}/"
        logargs = f"{Path(__file__).stem} Params: \n" + \
            f"\tInputDir \t\t{args.inputdir} \n" + \
            f"\tMeetName \t\t{args.meetname} \n" + \
            f"\tOutputDir \t\t{output_dir} \n" + \
            f"\tShort School Names \t{args.shortschoolnames} \n" + \
            f"\tSplit Relays \t\t{args.splitrelays} \n"+ \
            f"\tSpaces in Relay Names \t{args.spacerelaynames}\n"
    print( logargs )

    ## main function to generate heat files for Wirecast
    num_heats_files_generated,total_files_generated = generateHeatFiles( args.inputdir, output_dir, args.meetname, args.shortschoolnames, args.splitrelays, args.spacerelaynames )

    print(f"Process Completed: \n\tNumber of Heat Files Generated: {num_heats_files_generated}  \n\tTotal Number of files generated: {total_files_generated}")
