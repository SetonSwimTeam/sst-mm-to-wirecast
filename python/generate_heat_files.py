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
import glob

## Globals
DEBUG=False
report_type_results = "result"
report_type_program = "program"

## Define the types of events in this meet (Individual, Relay and Diving)
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

def remove_files_from_dir( directoryName ):
    """ Remove files from previous run/meet so there are no extra heats/events left over"""
    for root, dirs, files in os.walk(directoryName):
        for file in files:
            os.remove(os.path.join(root, file))  


def create_output_file( report_type, outputFileHandler, eventNum, heatNum, relaySplitFile ):
    """ Generate the filename and open the next file """
    if report_type == report_type_program:
        fileNamePrefix = "Entry"
    else: 
        fileNamePrefix = "Results"

    ## If File Hander then close
    if outputFileHandler:
        outputFileHandler.close()

    if report_type == report_type_program and eventNum in eventNumRelay:
        outputFileName = output_dir + f"{fileNamePrefix}_Event{eventNum:0>2}_Heat{heatNum:0>2}_{relaySplitFile:0>2}.txt"
    elif report_type == report_type_program:
        outputFileName = output_dir + f"{fileNamePrefix}_Event{eventNum:0>2}_Heat{heatNum:0>2}.txt"
    elif report_type == report_type_results:
        outputFileName = output_dir + f"{fileNamePrefix}_Event{eventNum:0>2}.txt"
    else:
        outputFileName = output_dir + f"Unknown_Event{eventNum:0>2}.txt"

    outputFileHandler = open( outputFileName, "w+" )
    return outputFileHandler


def generateHeatFiles( report_type, meet_report_filename, output_dir, meet_name, shortenSchoolNames, splitRelaysToMultipleFiles, addNewLineToRelayEntries ):
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
    program_headerLineLong  = "\nLane  Name                    Year School      Seed Time"
    program_headerLineShort = "\nLane  Name                 Year School Seed Time"
    program_headerLineRelay = "\nLane  Team                         Relay                   Seed Time"       
    result_headerLineLong   = "\nName                    Yr School                 Seed Time  Finals Time      Points"
    result_headerLineShort  = "\nName                    Yr School Seed Time  Finals Time      Points"
    result_headerLineReplay = "\nTeam                       Relay                  Seed Time  Finals Time      Points"
  


    ## Define local variables
    eventNum = 0
    heatNum = 0
    eventLine = ""
    heatLine = ""
    eventHeatFile = None


    num_heats_files_generated=0
    total_files_generated=0
    ## Remove files from last run
    remove_files_from_dir( output_dir )
    
    with open(meet_report_filename, "r") as meet_report_file:
        for line in meet_report_file:

            #####################################################################################
            ## Ignore all the blank lines             
            #####################################################################################
            if line == '\n':
                continue

            #####################################################################################
            ## Remove the extra newline at end of line
            #####################################################################################
            line = line.strip()

            #####################################################################################
            ## Ignore these meet program header lines                
            #####################################################################################

            ## Meet Manager license name
            if re.search("^Seton School", line):
                continue

            if report_type == report_type_program:
                ## Meet Manager report type
                if re.search("^Meet Program", line):
                    continue

                ## For Individual Events
                if re.search("^Lane(\s*)Name", line):
                    continue

                ## For Replay Events
                if re.search("^Lane(\s*)Team", line):
                    continue
                
            if report_type == report_type_results:
                if re.search("^Results", line):
                    continue
                ## For Individual Events
                if re.search("^Name(\s*)Yr", line):
                    continue

            #####################################################################################
            ## Ignore meet name line from output
            #####################################################################################
            if re.search(meet_name, line):
                continue

            #####################################################################################
            ## Start with Event line.  
            ##  Get the Event Number from the report
            ##  Clean it up
            #####################################################################################
            if line.lower().startswith(("event")):
                eventLine = line

                ## Remove all those extra spaces in the line
                cleanEventStr = eventLine.split()
                cleanEventStr = " ".join(cleanEventStr)
                # Get the line number
                eventStr = cleanEventStr.split(' ', 4)
                eventNum = int(eventStr[1].strip())

                ## For Program, we stop here and go to next line looking for heat
                ## For Result, we continue one
                if report_type == report_type_program:
                    continue

            #####################################################################################
            ## Remove "Timed Finals" from Heat (and flight) line
            #####################################################################################
            if line.lower().startswith(("heat", "flight")):
                line = line.replace("Timed Finals", "")
                # ## Add a new line after HEAT
                # line = re.sub("$", "\n", line)
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
            if report_type == report_type_program and eventNum not in eventNumDiving:
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
            ## Replace long school name with short name for individual events
            #####################################################################################
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

                ## IF we are splitting replays into multiple file, then put a blank line after each lane and name
                # if addNewLineToRelayEntries and (re.search('^[2-9] ', line) or re.search('^\d\d ', line)):
                #     line = f"\n{line}"
                if addNewLineToRelayEntries and re.search('^1\)', line):
                    line = f"{line}\n"

            #####################################################################################
            ## Processing specific to RELAY Entries
            #####################################################################################
            if report_type == report_type_program and line.lower().startswith(("heat")):
                # Determin heading based on short or full school name
                nameListHeader = program_headerLineLong
                if shortenSchoolNames and eventNum in eventNumIndividual:
                    nameListHeader = program_headerLineShort

                
            if report_type == report_type_results and line.lower().startswith(("event")):
                # Determin heading based on short or full school name
                nameListHeader = result_headerLineLong
                if shortenSchoolNames and eventNum in eventNumIndividual:
                    nameListHeader = result_headerLineShort


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
            if report_type == report_type_program and line.lower().startswith(("heat", "flight")):
                ## Open New file for Event/Heat info
                num_heats_files_generated += 1
                total_files_generated += 1
                heatLine = line
                if eventNum > 0 and heatNum > 0:
                    eventHeatFile = create_output_file( report_type, eventHeatFile, eventNum, heatNum, 1 )
                    ## Every New file starts with Event Number/Name
                    eventHeatFile.write( eventLine  + '\n')

            if report_type == report_type_results and line.lower().startswith(("event")):
                print(f"eventnum: {eventNum}")
                if eventNum > 0:
                    heatNum = 1
                    eventHeatFile = create_output_file( report_type, eventHeatFile, eventNum, 0, 0 )
                    ## Every New file starts with Event Number/Name
                    #eventHeatFile.write( eventLine  + '\n')

            #####################################################################################
            ## Relays with at least 6 lanes, split the result up in two files
            ## Manually added the Event/Heat and Header info into second file
            #####################################################################################
            if eventNum in eventNumRelay and splitRelaysToMultipleFiles:
                if (addNewLineToRelayEntries and re.search('^\n6 ', line)) or (not addNewLineToRelayEntries and re.search('^6 ', line)):
                    ## Look for lane Relay 5
                    total_files_generated += 1 
                    eventHeatFile = create_output_file( report_type, eventNum, heatNum, 2 )
                    eventHeatFile.write( eventLine  + '\n')
                    eventHeatFile.write( heatLine  + '\n')
                    eventHeatFile.write( program_headerLineRelay  + '\n')

            #####################################################################################
            ## output the actual data line
            #####################################################################################

            if eventNum > 0 and heatNum > 0:
                logger(  f"{line}" )
                eventHeatFile.write(line  + '\n')

            #####################################################################################
            ## output the individual swimmer list headers
            #####################################################################################
            if report_type == report_type_program and line.lower().startswith(("heat")):
                logger(  f"{nameListHeader}" )
                eventHeatFile.write( nameListHeader + '\n')
            if report_type == report_type_results and line.lower().startswith(("event")):
                logger(  f"{nameListHeader}" )
                eventHeatFile.write( nameListHeader + '\n')

    return num_heats_files_generated, total_files_generated

def cleanup_new_files( filePrefix, output_dir ):
    """ Remove the one or many blank lines at end of the file """

    txtfiles = []
    fileGlob = f"{output_dir}{filePrefix}*.txt"
    for file in glob.glob(fileGlob):
        txtfiles.append(file)
    
    for file in txtfiles:
        print(f"Filename: {file}")

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
    parser.add_argument('-t', '--reporttype',       dest='reporttype',          default=report_type_program,     choices=['program','result'], help="Program type, Meet Program or Meet Results")
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
            f"\tReportType \t\t{args.reporttype} \n" + \
            f"\tInputDir \t\t{args.inputdir} \n" + \
            f"\tMeetName \t\t{args.meetname} \n" + \
            f"\tOutputDir \t\t{output_dir} \n" + \
            f"\tShort School Names \t{args.shortschoolnames} \n" + \
            f"\tSplit Relays \t\t{args.splitrelays} \n"+ \
            f"\tSpaces in Relay Names \t{args.spacerelaynames}\n"
    print( logargs )

    ## main function to generate heat files for Wirecast
    num_heats_files_generated,total_files_generated = generateHeatFiles( args.reporttype, args.inputdir, output_dir, args.meetname, args.shortschoolnames, args.splitrelays, args.spacerelaynames )

    ## We probably add multiple blank lines at end of file.  Go clean those up
    #cleanup_new_files( "Entry", output_dir )
    print(f"Process Completed: \n\tNumber of Heat Files Generated: {num_heats_files_generated}  \n\tTotal Number of files generated: {total_files_generated}")
