#!/usr/local/bin/python3

#############################################################################################
#############################################################################################
###
### generate_heat_files
###  Will generate files for use in WireCast livestreaming software.  This script will 
###  generate both meet program entry files and meet results files
###
###  meet program entries:
###  Given a Meet Manager generated Meet Program, exported as a TXT file (single column one heat per page)
###   create individual files for every event/heat, with cleaned up text 
###   for optimal visualization on the live webcast for the WireCast application
###
###  meet results:
###  Given a Meet Manager generated Meet Results file, exported as a TXT file (sinle column one event per page)\
###  create individual results file per event for wirecast
###  Also generate a meet results CRAWL, which is a single line file with the results to
###  scroll through the botton of the livecast
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
report_type_crawler = "crawler"

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

def remove_files_from_dir( reporttype, directory_name ):
    """ Remove files from previous run/meet so there are no extra heats/events left over"""
    print("remove_files_from_dir")
    for root, dirs, files in os.walk(directory_name):
        for file in files:
            if file.startswith((reporttype)):
                os.remove(os.path.join(root, file))  

def create_output_file_program(  output_file_handler, event_num, heat_num, relay_split_file_num ):
    """ Generate the filename and open the next file """
    file_name_prefix = "program"

    ## If File Hander then close
    if output_file_handler:
        output_file_handler.close()

    if  event_num in eventNumRelay:
        output_file_name = output_dir + f"{file_name_prefix}_Event{event_num:0>2}_Heat{heat_num:0>2}_{relay_split_file_num:0>2}.txt"
    elif  event_num in eventNumIndividual:
        output_file_name = output_dir + f"{file_name_prefix}_Event{event_num:0>2}_Heat{heat_num:0>2}.txt"
    else:
        output_file_name = output_dir + f"{file_name_prefix}_Event{event_num:0>2}.txt"

    output_file_handler = open( output_file_name, "w+" )
    return output_file_handler


def create_output_file_results( output_file_handler, event_num ):
    """ Generate the filename and open the next file """
   
    file_name_prefix = "results"

    ## If File Hander then close
    if output_file_handler:
        output_file_handler.close()

    output_file_name = output_dir + f"{file_name_prefix}_Event{event_num:0>2}.txt"

    output_file_handler = open( output_file_name, "w+" )
    return output_file_handler


#####################################################################################
## create_output_file_crawler
##
## Given a list of tuples (evnt num, crawler_string), generate output files
#####################################################################################
def create_output_file_crawler( crawler_list ):
    """ Given a list of tuples (evnt num, crawler_string), generate output files """
   
    num_files_generated=0
    file_name_prefix = "crawler"
    for crawler_event in crawler_list:
        event_num = crawler_event[0]
        crawler_text = crawler_event[1]

        output_file_name = output_dir + f"{file_name_prefix}_Event{event_num:0>2}.txt"
        output_file_handler = open( output_file_name, "w+" )
        output_file_handler.write( crawler_text )
        output_file_handler.close()
        num_files_generated += 1

    return num_files_generated


#####################################################################################
## get_report_header_info
## Get the header info from the reports first X lines
#####################################################################################
def get_report_header_info( report_type, meet_report_filename ):
    """ Get the header info from the reports first X lines """
            
    #####################################################################################
    ## Example headers we are processing
    ##
    ## Seton School                             HY-TEK's MEET MANAGER 8.0 - 10:02 AM  11/19/2020
    ##               2020 NoVa Catholic Invitational Championship - 1/11/2020
    ##                                     Meet Program
    #####################################################################################

    line_num = 0
    line1_header = ""
    line2_header = ""
    line3_header = ""

    with open(meet_report_filename, "r") as meet_report_file:
        for line in meet_report_file:
            line_num += 1

            #####################################################################################
            ## Remove the extra newline at end of line
            #####################################################################################
            line = line.strip()

            #####################################################################################
            ## Line1: Seton School                             HY-TEK's MEET MANAGER 8.0 - 10:02 AM  11/19/2020                 
            #####################################################################################
            if line_num == 1:
                line1_header = line

            #####################################################################################
            ## Line2:               2020 NoVa Catholic Invitational Championship - 1/11/2020                
            #####################################################################################
            if line_num == 2:
                line2_header = line

            #####################################################################################
            ## Line3:                                    Meet Program               
            #####################################################################################
            if line_num == 3:
                line3_header = line

                ## Stop the loop now. We have our headers
                break

        logger(f"Header1: {line1_header}")
        logger(f"Header2: {line2_header}")
        logger(f"Header3: {line3_header}")


        #####################################################################################
        ## Header1.  Break about license name (school name)            
        #####################################################################################
        line1_list = re.findall('^(.*?) HY-TEK',line1_header )
        license_name = line1_list[0].strip()
        logger(f"license_name: '{license_name}' ")

        #####################################################################################
        ## Header2.  Break about meet name and meet date               
        #####################################################################################
        line2_list = re.findall('^(.*?) - (\d+/\d+/\d+)',line2_header )
        meet_name = line2_list[0][0]
        meet_date = line2_list[0][1]
        logger(f"meet_name: '{meet_name}' \nmeet_date: '{meet_date}'")

        #####################################################################################
        ## Header2.  Break about meet name and meet date               
        #####################################################################################
        report_type = line3_header
        logger(f"report_type: '{report_type}'")

        return meet_name, meet_date, license_name, report_type



#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
##########
##########    P R O G R A M
##########    generate_program_files
##########
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
def generate_program_files( report_type, meet_report_filename, output_dir, mm_license_name, shortenSchoolNames, splitRelaysToMultipleFiles, addNewLineToRelayEntries ):
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
    program_headerLineLong   = "\nLane  Name                    Year School      Seed Time"
    program_headerLineShort  = "\nLane  Name                 Year School Seed Time"
    program_headerLineDiving = "\nLane  Name                 Year School      Seed Points"
    program_headerLineRelay  = "\nLane  Team                         Relay                   Seed Time"         

    ## Define local variables
    eventNum = 0
    heatNum = 0
    eventLine = ""
    heatLine = ""
    eventHeatFile = None
    meet_name = None
    num_files_generated=0
    num_header_lines = 3
    found_header_line = 0

    #####################################################################################
    ## PROGRAM: Loop through each line of the input file
    #####################################################################################
    with open(meet_report_filename, "r") as meet_report_file:
        for line in meet_report_file:

            #####################################################################################
            ## PROGRAM: Remove the extra newline at end of line
            #####################################################################################
            line = line.strip()

            #####################################################################################
            ## PROGRAM: Ignore all the blank lines             
            #####################################################################################
            if line == '\n' or line == '':
                continue

            #####################################################################################
            ## PROGRAM: Ignore these meet program header lines                
            #####################################################################################

            ## Meet Manager license name
            if re.search("^%s" % mm_license_name, line):
                found_header_line = 1
                continue

            # There are X number of header lines, starting with "Seton School"
            # ignore these X lines
            if 0 < found_header_line < num_header_lines:
                found_header_line += 1
                if not meet_name and found_header_line == 2:
                    meet_name = line
                continue

            ## For Relay Individual Events
            if re.search("^Lane(\s*)Name", line):
                continue
            ## For Relay Events
            if re.search("^Lane(\s*)Team", line):
                continue

            #####################################################################################
            ## PROGRAM: Start with Event line.  
            ##  Get the Event Number from the report
            ##  Clean it up
            #####################################################################################
            if line.lower().startswith(("event")):
                eventLine = line

                ## Remove all those extra spaces in the line
                clean_event_str = eventLine.split()
                clean_event_str = " ".join(clean_event_str)
                # Get the line number
                event_str = clean_event_str.split(' ', 4)
                eventNum = int(event_str[1].strip())

                ## For Program, we stop here and go to next line looking for heat
                continue

            #####################################################################################
            ## PROGRAM: Remove "Timed Finals" from Heat (and flight) line
            #####################################################################################
            if line.lower().startswith(("heat", "flight")):
                line = line.replace("Timed Finals", "")
                ## Remove all those extra spaces in the line
                split_heat_str = line.split()
                split_heat_str = " ".join(split_heat_str)

                #####################################################################################
                # PROGRAM: Get the heat/flight number for user later on
                #####################################################################################
                split_heat_str = split_heat_str.split(' ', 4)
                heatNum = int(split_heat_str[1])

            #####################################################################################
            ## PROGRAM: Remove space after lane# 10 for formatting so names all align up evenly
            ## 10 must be on the beginning of the line 
            #####################################################################################
            if eventNum not in eventNumDiving:
                line = re.sub('^10  ', '10 ', line)

            #####################################################################################
            ## PROGRAM: For Diving Events, remove extra space from diver # 10 and above for formatting 
            ## so names lines up with diver 1-9
            #####################################################################################
            if eventNum in eventNumDiving:
                matched = re.search('^(\d\d) ', line)
                if matched:
                    line = re.sub('^(\d\d) ', r'\1',line )

            #####################################################################################
            ## RPROGRAM: eplace long school name with short name for individual events
            #####################################################################################
            if shortenSchoolNames == True and eventNum in eventNumIndividual:
                for k,v in schoolNameDict.items():
                    line = line.replace(k.ljust(schoolNameDictFullNameLen,' '), v.ljust(schoolNameDictShortNameLen, ' '))
            
            #####################################################################################
            ## PROGRAM: Processing specific to RELAY Entries
            #####################################################################################
            ## If this is a relay, see if there are spaces between swimmer numbers
            ## If so, add a space between the last swimmer name and the next swimmer number
            ## This line  1) LastName1, All2) LastName2, Ashley3) LastName3, All4) LastName4, Eri
            ## becomes    1) LastName1, All 2) LastName2, Ashley 3) LastName3, All 4) LastName4, Eri
            if eventNum in eventNumRelay:
                m = re.search('\S[2-4]\)',line)
                if m:
                    line = re.sub(r'(\S)([2-4]\))', r'\1 \2',line )

                ## IF we are splitting relays into multiple file, then put a blank line after each lane and name
                if addNewLineToRelayEntries and re.search('^1\)', line):
                    line = f"{line}\n"


            #####################################################################################
            ## PROGRAM: Set nameListHeader to be displayed above the list of swimmers
            #####################################################################################
            if line.lower().startswith(("heat", "flight")):
                # Determine heading based on short or full school name
                nameListHeader = program_headerLineLong
                if shortenSchoolNames and eventNum in eventNumIndividual:
                    nameListHeader = program_headerLineShort
                if eventNum in eventNumDiving:
                    nameListHeader = program_headerLineDiving



            #####################################################################################
            #####################################################################################
            #####################################################################################
            #####################################################################################
            ##########
            ##########     PROGRAM: 
            ##########     Done updating.formatting lines, start outputing data
            ##########
            #####################################################################################
            #####################################################################################
            #####################################################################################
            #####################################################################################
    
            #####################################################################################
            ## PROGRAM: Start a new Output Event/Heat file 
            ##      Heats are used for swimming.  
            ##      Flights are used for diving events
            #####################################################################################
            if line.lower().startswith(("heat", "flight")):
                ## Open New file for Event/Heat info
                heatLine = line
                if eventNum > 0 and heatNum > 0:
                    num_files_generated += 1
                    eventHeatFile = create_output_file_program( eventHeatFile, eventNum, heatNum, 1 )
                    ## Every New file starts with Event Number/Name
                    eventHeatFile.write( eventLine  + '\n')

            #####################################################################################
            ## PROGRAM: Relays with at least 6 lanes, split the result up in two files
            ## Manually added the Event/Heat and Header info into second file
            #####################################################################################
            if splitRelaysToMultipleFiles and eventNum in eventNumRelay:
                if (addNewLineToRelayEntries and re.search('^6 ', line)) or (not addNewLineToRelayEntries and re.search('^(\s*)6 ', line)):
                    num_files_generated += 1 
                    eventHeatFile = create_output_file_program( eventHeatFile, eventNum, heatNum, 2 )
                    eventHeatFile.write( eventLine  + '\n')
                    eventHeatFile.write( heatLine  + '\n')
                    eventHeatFile.write( program_headerLineRelay  + '\n')

            #####################################################################################
            ## PROGRAM: output the actual data line
            #####################################################################################
            if eventNum > 0 and heatNum > 0:
                logger(  f"{line}" )
                eventHeatFile.write(line  + '\n')

            #####################################################################################
            ## PROGRAM: output the individual swimmer list headers
            #####################################################################################
            if line.lower().startswith(("heat", "flight")):
                logger(  f"{nameListHeader}" )
                eventHeatFile.write( nameListHeader + '\n')

    #####################################################################################
    ## PROGRAM: All done. Return counts of files created
    #####################################################################################
    return num_files_generated


#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
##########
##########     R E S U L T S 
##########    generate_results_files
##########
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
def generate_results_files( report_type, meet_report_filename, output_dir, mm_license_name, shortenSchoolNames, addNewLineToRelayEntries ):
    """ Given the MeetManager results file file formatted in a specific manner,
        generate indiviual result files for use in Wirecast displays """
    
    #####################################################################################
    ## The names are what appear in the report, and may be abbreviated, 
    ##  and not the actual full school name
    ## Multiple version of a school may be listed here for clean output
    #####################################################################################
    schoolNameDictFullNameLen = 25
    schoolNameDictShortNameLen = 6  # Four character name plus spaces for padding between EntryTime

    displayRelaySwimmerNames = False

    ## NOTE: Do not align up these headers with the TXT output.  
    ##  Wirecast will center all lines and it will be in proper position then
    result_headerLineLong   = "\nName                    Yr School                 Seed Time  Finals Time      Points"
    result_headerLineShort  = "\nName                    Yr School Seed Time  Finals Time      Points"
    result_headerLineRelay  = "\nTeam                       Relay                  Seed Time  Finals Time      Points"
    result_headerLineDiving = "\nName                    Yr School                           Finals Score      Points"


    ## Define local variables
    eventNum = 0
    eventLine = ""
    outputResultFile = None
    num_files_generated=0
    num_header_lines = 3
    found_header_line = 0
    meet_name = None

    #####################################################################################
    ## RESULTS: Loop through each line of the input file
    #####################################################################################
    with open(meet_report_filename, "r") as meet_report_file:
        for line in meet_report_file:

            #####################################################################################
            ## RESULTS: Remove the extra newline at end of line
            #####################################################################################
            line = line.strip()

            #####################################################################################
            ## RESULTS: Ignore all the blank lines             
            #####################################################################################
            if line == '\n' or line == '':
                continue

            #####################################################################################
            ## RESULTS: Ignore these meet program header lines                
            #####################################################################################

           ## Meet Manager license name
            if re.search("^%s" % mm_license_name, line):
                found_header_line = 1
                continue

            # There are X number of header lines, starting with "Seton School"
            # ignore these X lines
            if 0 < found_header_line < num_header_lines:
                found_header_line += 1
                if not meet_name and found_header_line == 2:
                    meet_name = line
                continue

            ## For Individual Events
            if re.search("^Name(\s*)Yr", line):
                continue
            ## For Relay Events
            if re.search("^Team(\s*)Relay", line):
                continue
                       
            #####################################################################################
            ## RESULTS: Start with Event line.  
            ##  Get the Event Number from the report
            ##  Clean it up
            #####################################################################################
            if line.lower().startswith(("event")):
                eventLine = line

                ## Remove all those extra spaces in the line
                clean_event_str = eventLine.split()
                clean_event_str = " ".join(clean_event_str)
                # Get the line number
                event_str = clean_event_str.split(' ', 4)
                eventNum = int(event_str[1].strip())

            #####################################################################################
            ## RESULTS: Replace long school name with short name for individual events
            #####################################################################################
            if shortenSchoolNames == True and eventNum in eventNumIndividual:
                for k,v in schoolNameDict.items():
                    line = line.replace(k.ljust(schoolNameDictFullNameLen,' '), v.ljust(schoolNameDictShortNameLen, ' '))
            
            #####################################################################################
            ## RESULTS: Processing specific to RELAY Entries
            #####################################################################################
            ## If this is a relay, see if there are spaces between swimmer numbers
            ## If so, add a space between the last swimmer name and the next swimmer number
            ## This line  1) LastName1, All2) LastName2, Ashley3) LastName3, All4) LastName4, Eri
            ## becomes    1) LastName1, All 2) LastName2, Ashley 3) LastName3, All 4) LastName4, Eri
            if eventNum in eventNumRelay:
                m = re.search('\S[2-4]\)',line)
                if m:
                    line = re.sub(r'(\S)([2-4]\))', r'\1 \2',line )

            #####################################################################################
            ## RESULTS: For results on relays, only display relay team, not individual names
            ## TODO: Make this a command line parm
            #####################################################################################
            if not displayRelaySwimmerNames and re.search('^1\) ',line):
                continue

            #####################################################################################
            ## RESULTS: Set nameListHeader to be displayed above the list of swimmers
            #####################################################################################
            if line.lower().startswith(("event")):
                # Determin heading based on short or full school name
                nameListHeader=""
                if eventNum in eventNumIndividual:
                    nameListHeader = result_headerLineLong
                if shortenSchoolNames and eventNum in eventNumIndividual:
                    nameListHeader = result_headerLineShort
                if eventNum in eventNumDiving:
                    nameListHeader = result_headerLineDiving

            #####################################################################################
            ## RESULTS: For results, add a space after top 1-9 swimmers so names line up with 10-12 place
            #####################################################################################
            if re.search("^[1-9] ", line):
                line = re.sub('^([1-9]) ', r'\1  ', line )
    


            #####################################################################################
            #####################################################################################
            #####################################################################################
            #####################################################################################
            ##########
            ##########    RESULTS: 
            ##########     Done updating.formatting lines, start outputing data
            ##########
            #####################################################################################
            #####################################################################################
            #####################################################################################
            #####################################################################################
    
            #####################################################################################
            ## RESULTS: Start a new Output Event/Heat file 
            ##      Heats are used for swimming.  
            ##      Flights are used for diving events
            #####################################################################################
            if line.lower().startswith(("event")):
                if eventNum > 0:
                    num_files_generated += 1
                    outputResultFile = create_output_file_results( outputResultFile, eventNum )

            #####################################################################################
            ## RESULTS: output the actual data line
            #####################################################################################
            if eventNum > 0:
                logger(  f"{line}" )
                outputResultFile.write(line  + '\n')

            #####################################################################################
            ## RESULTS: output the individual swimmer list headers
            #####################################################################################
            if line.lower().startswith(("event")):
                logger(  f"{nameListHeader}" )
                outputResultFile.write( nameListHeader + '\n')

    #####################################################################################
    ## RESULTS: All done. Return counts of files created
    #####################################################################################
    return num_files_generated


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
#####################################################################################
#####################################################################################
##########
##########     R E S U L T S    C R A W L E R
##########    generate_crawler_files
##########
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
def generate_crawler_files( report_type, meet_report_filename, output_dir, mm_license_name, shorten_school_names, display_swimmers_in_relay ):
    """  From the Meet Results File, generate the crawler files per event """

    eventNum = 0
    crawler_string = ""
    found_header_line = 0
    num_header_lines = 0
    schoolNameDictFullNameLen = 25
    schoolNameDictShortNameLen = 6  # Four character name plus spaces for padding between EntryTime

    crawler_list = []


    #####################################################################################
    ## CRAWLER: Loop through each line of the input file
    #####################################################################################
    with open(meet_report_filename, "r") as meet_report_file:
        for line in meet_report_file:

            #####################################################################################
            ## CRAWLER: Remove the extra newline at end of line
            #####################################################################################
            line = line.strip()

            #####################################################################################
            ## CRAWLER: Ignore all the blank lines             
            #####################################################################################
            if line == '\n' or line == '':
                continue

            #####################################################################################
            ## CRAWLER: Ignore these meet program header lines                
            #####################################################################################

           ## Meet Manager license name
            if re.search("^%s" % mm_license_name, line):
                found_header_line = 1
                continue

            # There are X number of header lines, starting with "Seton School"
            # ignore these X lines
            if 0 < found_header_line < num_header_lines:
                found_header_line += 1
                if not meet_name and found_header_line == 2:
                    meet_name = line
                continue

            ## For Individual Events
            if re.search("^Name(\s*)Yr", line):
                continue
            ## For Relay Events
            if re.search("^Team(\s*)Relay", line):
                continue
                       
            #####################################################################################
            ## CRAWLER: Start with Event line.  
            ##  Get the Event Number from the report
            ##  Clean it up
            #####################################################################################
            if line.lower().startswith(("event")):
                ## Found an event.  If its not the first one, the we are done generating the string
                ## from the last event. Save this event data and prepare for next event
                if eventNum > 0:
                    crawler_list.append( (eventNum, crawler_string  ))

                ##
                ## Start processing next event
                ##

                ## Remove all those extra spaces in the line
                clean_event_str = line.split()
                clean_event_str = " ".join(clean_event_str)
                # Get the event number
                event_str = clean_event_str.split(' ', 4)
                eventNum = int(event_str[1].strip())

                ## Clear out old string and start new for next event
                output_str = ""
                for element in event_str:
                    output_str += f" {element}"
                crawler_string = output_str

  

            #####################################################################################
            ## CRAWLER: Replace long school name with short name for ALL events
            #####################################################################################
            for k,v in schoolNameDict.items():
                line = line.replace(k.ljust(schoolNameDictFullNameLen,' '), v.ljust(schoolNameDictShortNameLen, ' '))
            

            #####################################################################################
            ## CRAWLER: Processing specific to RELAY Entries
            #####################################################################################
            ## If this is a relay, see if there are spaces between swimmer numbers
            ## If so, add a space between the last swimmer name and the next swimmer number
            ## This line  1) LastName1, All2) LastName2, Ashley3) LastName3, All4) LastName4, Eri
            ## becomes    1) LastName1, All 2) LastName2, Ashley 3) LastName3, All 4) LastName4, Eri
            if eventNum in eventNumRelay:
                m = re.search('\S[2-4]\)',line)
                if m:
                    line = re.sub(r'(\S)([2-4]\))', r'\1 \2',line )

            #####################################################################################
            ## CRAWLER: For results on relays, only display relay team, not individual names
            ## TODO: Make this a command line parm
            #####################################################################################
            if not display_swimmers_in_relay and re.search('^1\) ',line):
                continue

            #####################################################################################
            ## CRAWLER: INDIVIDUAL Find the Place Winner line, place, name, school, time, points, etc
            ## i.e. 1 Last, First           SR SCH   5:31.55      5:23.86        16
            ## Note: For ties an asterick is placed before the place number and the points could have a decimal
            #####################################################################################
            if eventNum in eventNumIndividual and re.search('^[*]?\d{1,2} ', line):
                #print( f"PlaceWinner: {line}")
                #                               place     last first   GR         SCHOOL           SEEDTIME    FINALTIME      POINTS
                place_line_list = re.findall('^([*]?\d{1,2}) (\w+, \w+)\s+(\w+) ([A-Z0-9]{1,4})\s+([0-9:.]+)\s+([0-9:.]+)\s+([0-9.])*', line)
                #                               place     last first   GR         SCHOOL           SEEDTIME    FINALTIME      POINTS
                if place_line_list:
                    #print( f"place_line: place_line_list ")
                    placeline_place     = str(place_line_list[0][0])
                    placeline_name      = str(place_line_list[0][1])
                    placeline_grade     = str(place_line_list[0][2])
                    placeline_school    = str(place_line_list[0][3])
                    placeline_seedtime  = str(place_line_list[0][4])
                    placeline_finaltime = str(place_line_list[0][5])
                    placeline_points    = str(place_line_list[0][6])

                    #print(f"placeline place {placeline_place}: name {placeline_name}: grade {placeline_grade}: school {placeline_school}: seed {placeline_seedtime}: final {placeline_finaltime}: point {placeline_points}")

                    output_str = f" {placeline_place}) {placeline_name} {placeline_school}"
                    crawler_string += output_str
    
            #####################################################################################
            ## CRAWLER: RELAY Find the Place Winner line, place, name, school, time, points, etc
            ## 1 SST            A                    1:46.82      1:40.65        32
            ## Note: For ties an asterick is placed before the place number and the points could have a decimal
            #####################################################################################
            if eventNum in eventNumRelay and re.search('^[*]?\d{1,2} ', line):
                #                               PLACE        SCHOOL    RELAY     SEEDTIME    FINALTIME      POINTS
                place_line_list = re.findall('^([*]?\d{1,2}) (\w+) \s+([A-Z])\s+([0-9:.]+)\s+([0-9:.]+)\s+([0-9.])*', line)
                #                               PLACE        SCHOOL    RELAY     SEEDTIME    FINALTIME      POINTS
                if place_line_list:
                    #print( f"RELAY place_line: {place_line_list} ")
                    placeline_place     = str(place_line_list[0][0])
                    placeline_school    = str(place_line_list[0][1])
                    placeline_relay     = str(place_line_list[0][2])
                    placeline_seedtime  = str(place_line_list[0][3])
                    placeline_finaltime = str(place_line_list[0][4])
                    placeline_points    = str(place_line_list[0][5])

                    #print(f"placeline place {placeline_place}: school {placeline_school}: placeline_relay {placeline_relay}: seed {placeline_seedtime}: final {placeline_finaltime}: point {placeline_points}")

                    output_str = f" {placeline_place}) {placeline_school} {placeline_relay}"
                    crawler_string += output_str  


    total_files_generated = create_output_file_crawler( crawler_list )

    return total_files_generated

#####################################################################################
#####################################################################################
##  M A I N
#####################################################################################
#####################################################################################
if __name__ == "__main__":

    #####################################################################################
    ## Parse out command line arguments
    #####################################################################################

    spacerelaynames = True
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputdir',         dest='inputdir',            default="../data",              required=True,   
                                                                                                                help="input directory for MM extract report")
    parser.add_argument('-m', '--license_name',     dest='license_name',        default="Seton School",         help="MM license name as printed out on reports")
    parser.add_argument('-t', '--reporttype',       dest='reporttype',          default=report_type_program,    choices=['program','result', 'crawler',' headers'], 
                                                                                                                help="Program type, Meet Program or Meet Results")
    parser.add_argument('-o', '--outputdir',        dest='outputdir',           default="../output/",           help="output directory for wirecast heat files.")
    parser.add_argument('-s', '--shortschoolnames', dest='shortschoolnames',    action='store_true',            help="Use Short School names for Indiviual Entries")
    parser.add_argument('-l', '--longschoolnames',  dest='shortschoolnames',    action='store_false',           help="Use Long School names for Indiviual Entries")
    parser.add_argument('-r', '--splitrelays',      dest='splitrelays',         action='store_true',            help="Split Relays into multiple files")
    parser.add_argument('-R', '--displayRelayNames',dest='displayRelayNames',   action='store_true',            help="Display relay swimmer names, not just the team name in results")
    parser.add_argument('-d', '--debug',            dest='debug',               action='store_true',            help="Print out results to console")
    parser.add_argument('-D', '--delete',           dest='delete',              action='store_true',            help="Delete existing files in OUTPUT_DIR")
    parser.set_defaults(shortschoolnames=True)
    parser.set_defaults(splitrelays=False)
    parser.set_defaults(displayRelayNames=False)
    parser.set_defaults(DEBUG=False)
    parser.set_defaults(delete=False)

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
              f"\tMeetName \t\t{args.license_name} \n" + \
              f"\tOutputDir \t\t{output_dir} \n" + \
              f"\tShort School Names \t{args.shortschoolnames} \n" + \
              f"\tSplit Relays \t\t{args.splitrelays} \n"+ \
              f"\tDisplay Relays Names \t\t{args.displayRelayNames} \n"+ \
              f"\tSpaces in Relay Names \t{spacerelaynames}\n" + \
              f"\tDelete exiting output files \t{args.delete}\n"
    print( logargs )

    #####################################################################################
    ## Remove files from last run
    #####################################################################################
    if args.delete:
        remove_files_from_dir( args.reporttype, output_dir )

    #####################################################################################
    ## main function to generate heat files for Wirecast
    #####################################################################################
    total_files_generated = 0

    #####################################################################################
    ## Get header info from the meet file
    #####################################################################################
    meet_name, meet_date, license_name, report_type = get_report_header_info( args.reporttype, args.inputdir )

    #####################################################################################
    ## Generate wirecast files from a MEET PROGRAM txt file
    #####################################################################################
    if args.reporttype == report_type_program:
        total_files_generated = generate_program_files( args.reporttype, args.inputdir, output_dir, args.license_name, args.shortschoolnames, args.splitrelays, spacerelaynames )

    #####################################################################################
    ## Generate wirecast files from a MEET RESULTS txt file
    #####################################################################################
    if args.reporttype == report_type_results:
        total_files_generated =  generate_results_files( args.reporttype, args.inputdir, output_dir, args.license_name, args.shortschoolnames, spacerelaynames )
    
    #####################################################################################
    ## Generate wirecast files for the crawler of results
    #####################################################################################
    if args.reporttype == report_type_crawler:
        total_files_generated=   generate_crawler_files( args.reporttype, args.inputdir, output_dir, args.license_name, args.shortschoolnames, args.displayRelayNames )
    
    ## We probably add multiple blank lines at end of file.  Go clean those up
    #cleanup_new_files( "Entry", output_dir )
    print(f"Process Completed: \n\tTotal Number of files generated: {total_files_generated}")