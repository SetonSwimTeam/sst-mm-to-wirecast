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

## Define the header types in the output list so we can include/exclude as necessary
headerNum1 = -1   ## HyTek licensee and HytTek software
headerNum2 = -2   ## Meet Name
headerNum3 = -3   ## Report type
unofficial_results = "    ** UNOFFICIAL RESULTS **"

## Define the types of events in this meet (Individual, Relay and Diving)
eventNumIndividual = [3,4,5,6,7,8,11,12,13,14,15,16,19,20,21,22]
eventNumRelay  = [1,2,17,18,23,24]
eventNumDiving = [9,10]

#####################################################################################
## Text used for REGEX to convert long names to short names
## Some names are truncated. May be able to define full name and then define max
## lenght of school name depending on report
#####################################################################################
schoolNameDict = { 
        "Benedictine College Prep": "BCP",
        "Bishop O'Connell-PV": "DJO",
        "Bishop O'Connell": "DJO",
        "Bishop Ireton Swim and Dive": "BI",
        "Bishop Sullivan Catholic High": "BSCHS",
        "BBVST": "BVST",
        "Broadwater Academy-VA": "BVST",
        "Cape Henry Collegiate": "CHC",
        "Carmel School Wildcats": "WILD",
        "CCS-VA": "CCS",
        "Chatham Hall": "CH",
        "Christchurch School Swim Team": "CCS",
        "Collegiate School": "COOL",
        "Fredericksburg Academy-VA": "FAST",
        "Fredericksburg Christian-": "FCS",
        "Fresta Valley Christian": "FVCS",
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
        "H2owls-VA": "WAKE",
        "Williamsburg Christian Ac": "WCA",
        "Woodberry Forest-VA": "WFS",
        "Valley Christian School": "VCS",
        "Valley Christian S": "VCS",
    } 


#####################################################################################
## Control logging/not logging of messages with CLI param
#####################################################################################
def logger( log_string ):
    """ Prints out logs if DEBUG command line parm was enabled """
    if DEBUG:
        print( log_string )


#####################################################################################
## CLI param to remove existing files from directory.  This is needed when
## old heats won't be overwritten so we need to make sure they are removed
#####################################################################################
def remove_files_from_dir( reporttype, directory_name ):
    """ Remove files from previous run/meet so there are no extra heats/events left over"""
    for root, dirs, files in os.walk(directory_name):
        for file in files:
            if file.startswith((reporttype)):
                os.remove(os.path.join(root, file))  



#####################################################################################
## Given an array of data lines PER EVENT, generate the output file
#####################################################################################
def create_output_file_results( output_dir_root, event_num, output_list, displayRelaySwimmerNames ):
    """ Generate the filename and open the next file """
    
    num_files_generated = 0
    output_str = ""


    file_name_prefix = "results"

    output_dir = f"{output_dir_root}{file_name_prefix}/"

    ## Create output dir if not exists
    if not os.path.exists( output_dir ):
        os.makedirs( output_dir )

    ## Loop through list in reverse order
    #for num in range( num_events-1, -1, -1):
    for output_tuple in output_list:
        row_type = output_tuple[0]
        row_text = output_tuple[1]

        logger(f"RESULTS: e: {event_num} id: {row_type} t: {row_text}")

        ## Save off the meet name, which somes at the end of the procesing as we are looping in reverse order
        if row_type == 'H4':
            output_str += row_text + '\n'
            output_str += '\n'
        elif row_type == 'H6':
            output_str += row_text + '\n'
        elif row_type == 'PLACE':
            output_str += row_text + '\n'
        elif row_type == 'NAME' and displayRelaySwimmerNames:
            output_str += row_text + '\n'

    output_file_name = output_dir + f"{file_name_prefix}_Event{event_num:0>2}.txt"
    output_file_handler = open( output_file_name, "w+" )
    output_file_handler.writelines( output_str )
    output_file_handler.close()
    num_files_generated += 1

    return num_files_generated


####################################################################################
## Given an array of data lines PER HEAT, generate the output file
#####################################################################################
def create_output_file_program( output_dir_root, event_num, heat_num, output_list, displayRelaySwimmerNames, splitRelaysToMultipleFiles ):
    """ Generate the filename and open the next file """
   
    num_files_created = 0
    split_num = 1
    output_str = ""
    

    file_name_prefix = "program"
    output_dir = f"{output_dir_root}{file_name_prefix}/"

    ## Create output dir if not exists
    if not os.path.exists( output_dir ):
        os.makedirs( output_dir )
    
    ## For non relay events
    output_file_name = output_dir + f"{file_name_prefix}_Event{event_num:0>2}_Heat{heat_num:0>2}.txt"

    ## Count the number of lanes in the RELAY
    num_relay_lane = 0
    if event_num in eventNumRelay:
        for output_tuple in output_list:
            row_type = output_tuple[0]
            
            if row_type == 'LANE':
                num_relay_lane += 1

    header_list = ['H4', 'H5', 'H6']
    header_str = ""
    ## Loop through list in reverse order
    #for num in range( num_events-1, -1, -1):
    count =0 
    for output_tuple in output_list:
        row_type = output_tuple[0]
        row_text = output_tuple[1]

        ## Save off the meet name, which somes at the end of the procesing as we are looping in reverse order
        if row_type in header_list:
            output_str += row_text + '\n'
            header_str += row_text + '\n'
        elif row_type == 'LANE':
            output_str += row_text + '\n'
        elif row_type == 'NAME' and displayRelaySwimmerNames:
            output_str += row_text + '\n'
            ## If split, space it out for readability
            if splitRelaysToMultipleFiles:
                output_str += '\n'

        ## If we have more then 6 relay entries create second output file
        if splitRelaysToMultipleFiles and num_relay_lane > 7 and count == 5:
            count = -99
            output_file_name = output_dir + f"{file_name_prefix}_Event{event_num:0>2}_Heat{heat_num:0>2}_Split{split_num:0>2}.txt"
            output_file_handler = open( output_file_name, "w+" )
            output_file_handler.writelines( output_str )
            output_file_handler.close()
            output_str = header_str
            ## Regenerate the header?  Need a better way to do this
            num_files_created += 1
            split_num += 1
            output_file_name = output_dir + f"{file_name_prefix}_Event{event_num:0>2}_Heat{heat_num:0>2}_Split{split_num:0>2}.txt"
            ## IF we are splitting relays into multiple file, then put a blank line after each lane and name
            #if addNewLineToRelayEntries and re.search('^1\)', line):
            #    line = f"{line}\n"

        if row_type == 'LANE':
            count += 1

    output_file_handler = open( output_file_name, "w+" )
    output_file_handler.writelines( output_str )
    output_file_handler.close()
    num_files_created += 1

    return num_files_created


#####################################################################################
## CRAWLER:  Generate the actual output file
#####################################################################################
def write_output_file_crawler( output_file_name, output_str ):
    """ generate the actual crawler output file """
    output_file_handler = open( output_file_name, "w+" )
    output_file_handler.write( output_str )
    output_file_handler.close()



#####################################################################################
## create_output_file_crawler
##
## Given a list of tuples (evnt num, crawler_string), generate output files
## Generate crawler files for actual events (event_num > 0) and for meet name (event_num = -2)
#####################################################################################
def create_output_file_crawler( report_type, output_dir_root, crawler_list ):
    """ Given a list of tuples (evnt num, crawler_string), generate output files """
    
    file_name_prefix = "crawler"
    output_dir = f"{output_dir_root}{file_name_prefix}/"
    num_files_generated=0

    ## Create output dir if not exists
    if not os.path.exists( output_dir ):
        os.makedirs( output_dir )

    ## Generate individual files per meet
    for crawler_event in crawler_list:
        event_num = crawler_event[0]
        crawler_text = crawler_event[1]

        logger(f"crawler: e: {event_num} t: {crawler_text}")
        ## Generate event specific file
        if event_num > 0:
            output_file_name = output_dir + f"{file_name_prefix}_{report_type}_event{event_num:0>2}.txt"
            write_output_file_crawler( output_file_name, crawler_text )
            num_files_generated += 1
        ## Genreate special file for the meet name
        elif event_num == headerNum2:
            output_file_name = output_dir + f"{file_name_prefix}__MeetName.txt"
            write_output_file_crawler( output_file_name, crawler_text )
            num_files_generated += 1

    ## Generate single file for all scored events in reverse order
    crawler_text = ""
    meet_name = ""
    num_events = len(crawler_list)

    ## Loop through list in reverse order
    for num in range( num_events-1, -1, -1):
        crawler_event = crawler_list[num]
        event_num = crawler_event[0]
        event_text = crawler_event[1]

        ## Save off the meet name, which somes at the end of the procesing as we are looping in reverse order
        if event_num > 0:
            crawler_text += f" | {event_text}"
        elif event_num == headerNum2:
            meet_name = event_text
        
    ## Add meet_name to front of string
    crawler_text = f"{meet_name} {crawler_text}"

    ## Create the crawler file with ALL events completed so far
    output_file_name = output_dir + f"{file_name_prefix}__AllEventsReverse.txt"
    write_output_file_crawler( output_file_name, crawler_text )
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

        #####################################################################################
        ## Header1.  Break about license name (school name)            
        #####################################################################################
        line1_list = re.findall('^(.*?) HY-TEK',line1_header )
        license_name = str(line1_list[0].strip())
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
def generate_program_files( report_type, meet_report_filename, output_dir, mm_license_name, shortenSchoolNames, splitRelaysToMultipleFiles, addNewLineToRelayEntries, displayRelaySwimmerNames, namesfirstlast ):
    """ Given the input file formatted in a specific manner,
        generate indiviual Event/Heat files for use in Wirecast displays """
    
    #####################################################################################
    ## The names are what appear in the report, and may be abbreviated, 
    ##  and not the actual full school name
    ## Multiple version of a school may be listed here for clean output
    #####################################################################################
    programRelayDictFullNameLen = 24
    programIndDictFullNameLen   = 25
    programDiveDictFullNameLen  = 25    
    schoolNameDictShortNameLen  = 4  

    unofficial_results = ""  ## Not used for Programs

    ## NOTE: Do not align up these headers with the TXT output.  
    ##  Wirecast will center all lines and it will be in proper position then
    program_headerLineLong        = "\nLane  Name                    Year School      Seed Time"
    program_headerLineShort       = "\nLane  Name                 Year School Seed Time"
    program_headerLineDivingLong  = "\nLane  Name                 Year School      Seed Points"
    program_headerLineDivingShort = "\nLane  Name Year School      Seed Points"
    program_headerLineRelayLong   = "\nLane  Team                         Relay                   Seed Time"         
    program_headerLineRelayShort  = "\nLane  Team Relay Seed Time"         

    ## Define local variables
    eventNum = 0
    heatNum = 0
    num_files_generated = 0
    num_header_lines = 3
    found_header_line = 0
    output_list = []

    re_program_lane = re.compile('^[*]?\d{1,2} ')
    re_program_lane_ind = re.compile('^(\d{1,2})\s+([A-z\' \.]+, [A-z ]+) ([A-Z0-9]{1,2})\s+([A-Z \'.].*)\s+([X]?[0-9:.]+|NT|XNT|NP|XNP)*')
    re_program_lane_relay = re.compile('^(\d{1,2})\s+([A-Z \'.].*)\s+([A-Z])\s+([X]?[0-9:.]+|NT|XNT)*')

    ## Remove the trailing hyphen (-) and -VA from school name
    re_program_sch_cleanup1 = re.compile(r'(.*?)-VA(\s*)$')
    re_program_sch_cleanup2 = re.compile(r'(.*?)-$(\s*)$')

    ## Search for headers to remove
    re_program_header_ind   = re.compile("^Lane(\s*)Name")
    re_program_header_relay = re.compile("^Lane(\s*)Team")

    ## Search for case where team time butts up against seed time.  
    ## Need to add a space here so main regex works
    re_program_space_team_seed = re.compile(r'([A-z])(X\d)')

    ## For relays add a space between the persons name and next swimmer number
    re_program_space_relay_name = re.compile(r'(\S)([2-4]\))')
    re_program_check_relay_name_line = re.compile('1\)')

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
            ## Meet Manager license name
            ## We have one event/heat per page, so this starts the next event/heat
            #####################################################################################
            if re.search("^%s" % mm_license_name, line):
                found_header_line = 1
                
                num_files = create_output_file_program( output_dir, eventNum, heatNum, output_list, displayRelaySwimmerNames, splitRelaysToMultipleFiles )
                num_files_generated += num_files

                ## Reset and start processing the next event/heat
                output_list = []
                output_list.append( ('H1', line ))
                continue

            #####################################################################################
            ## if the previous line was the first header (found_header_line=1)
            ## then save  the next two lines which are also part of the header and got to next line
            #####################################################################################
            if 0 < found_header_line < num_header_lines:
                found_header_line += 1
                if found_header_line == 2:
                    output_list.append( ('H2', line ))
                elif found_header_line == 3:
                    output_list.append( ('H3', line ))
                continue

            #####################################################################################
            ## Ignore these lines as we will add our own back in depending on the output format
            #####################################################################################
            ## For Relay Individual Events
            if re_program_header_ind.search(line):
                continue
            ## For Relay Events
            if re_program_header_relay.search(line):
                continue

            #####################################################################################
            ## PROGRAM: Start with Event line.  
            ##  Get the Event Number from the report
            ##  Clean it up
            #####################################################################################
            if line.lower().startswith(("event")):

                ## Remove all those extra spaces in the line
                clean_event_str = line.split()
                clean_event_str = " ".join(clean_event_str)
                # Get the line number
                event_str = clean_event_str.split(' ', 4)
                eventNum = int(event_str[1].strip())

                ## H4 is the Event number/name line
                output_list.append(('H4', f"{line} {unofficial_results}" ))


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

                ## H6 is the Heat info, save it in case we want to output it later
                output_list.append(('H5', f"{line}" ))

                #####################################################################################
                ## PROGRAM: Set nameListHeader to be displayed above the list of swimmers
                ##          This is only set once per Event/Heat so moving this is probablimetic
                #####################################################################################
                # Determin heading based on short or full school name
                nameListHeader = ""
                if eventNum in eventNumIndividual:
                    nameListHeader = program_headerLineShort if shortenSchoolNames else program_headerLineLong   
                elif eventNum in eventNumDiving:
                    nameListHeader = program_headerLineDivingShort if shortenSchoolNames else program_headerLineDivingLong
                elif eventNum in eventNumRelay:
                    nameListHeader = program_headerLineRelayShort if shortenSchoolNames else program_headerLineRelayLong
                
                if nameListHeader != "":
                    output_list.append(('H6', nameListHeader))


            #####################################################################################
            ## PROGRAM: INDIVIDUAL Extract the individual Entry Line
            ## i.e. 2   Robison, Ryan            JR  Bishop O'Connell-PV      X2:22.35                        
            #####################################################################################
            if (eventNum in eventNumIndividual or eventNum in eventNumDiving) and re_program_lane.search(line):
                ## Fix for case where School Name butts up to the X in seed time
                #if re.search('[A-z]X\d', line):
                line = re_program_space_team_seed.sub(r'\1 \2', line )

                entry_line_list = re_program_lane_ind.findall(line)
                #                                  LANE     LAST, FIRST        GR          SCHOOL             SEEDTIME 
                if entry_line_list:
                    entry_lane            = str(entry_line_list[0][0]).strip()
                    entry_name_last_first = str(entry_line_list[0][1]).strip()
                    entry_grade           = str(entry_line_list[0][2]).strip()
                    entry_sch_long        = str(entry_line_list[0][3]).strip()
                    entry_seedtime        = str(entry_line_list[0][4]).strip()
                    
                    ## If we want to use Shortened School Names, run the lookup
                    if shortenSchoolNames:
                        ## The length of the school name in the MM report varies by event type
                        school_name_len = programDiveDictFullNameLen if eventNum in eventNumDiving else programIndDictFullNameLen

                        entry_sch_short = entry_sch_long
                        for k,v in schoolNameDict.items():
                            entry_sch_short = entry_sch_short.replace(k[:school_name_len], v.ljust(schoolNameDictShortNameLen, ' '))
                            if entry_sch_short != entry_sch_long:
                                break

                    ## We can display name as given (Last, First) or change it to First Last with cli parameter
                    if namesfirstlast:
                        entry_name_last, entry_name_first = entry_name_last_first.split(',',1)
                        entry_name_first = entry_name_first.strip()
                        entry_name_last  = entry_name_last.strip()
                        entry_name_first_last = f"{entry_name_first} {entry_name_last}"
                        entry_name = entry_name_first_last
                    else:
                        entry_name = entry_name_last_first

                    ## Still issues with School names ending in - or -VA
                    entry_sch_long = re_program_sch_cleanup1.sub(r'\1', entry_sch_long)
                    entry_sch_long = re_program_sch_cleanup2.sub(r'\1', entry_sch_long)
                    ## Format the output lines with either long (per meet program) or short school names
                    output_str = f" {entry_lane:>2} {entry_name:<25} {entry_grade:>2} {entry_sch_long:<25} {entry_seedtime:>8}"

                    if shortenSchoolNames:
                        output_str = f" {entry_lane:>2} {entry_name:<25} {entry_grade:>2} {entry_sch_short:<4} {entry_seedtime:>8}"
                    
                    output_list.append(('LANE', output_str))
            
            #####################################################################################
            ## PROGRAM: RELAY Find the replay line with LANE, SCHOOL, RELAY TEAM SEEDTIME
            ## 1 Seton Swim            A                    1:46.82      1:40.65        32
            #####################################################################################
            if eventNum in eventNumRelay and re_program_lane.search(line):
                entry_line_list = re_program_lane_relay.findall(line)
                #  REGEX Positions                 LANE   SCHOOL    RELAY     SEEDTIME
                if entry_line_list:
                    entryline_place     = str(entry_line_list[0][0])
                    entryline_sch_long  = str(entry_line_list[0][1])
                    entryline_relay     = str(entry_line_list[0][2])
                    entryline_seedtime  = str(entry_line_list[0][3])

                    #####################################################################################
                    ## PROGRAM: Replace long school name with short name for RELAY events
                    #####################################################################################
                    if shortenSchoolNames:
                        entryline_sch_short = entryline_sch_long

                        for k,v in schoolNameDict.items():
                            entryline_sch_short = entryline_sch_short.replace(k.ljust(programRelayDictFullNameLen,' ')[:programRelayDictFullNameLen], v.ljust(schoolNameDictShortNameLen, ' '))
                            if entryline_sch_short != entryline_sch_long:
                                break
                        output_str = f"{entryline_place:>2} {entryline_sch_short:<4} {entryline_relay:1} {entryline_seedtime:>8}"
                    else:
                        ## Still issues with School names ending in - or -VA
                        entryline_sch_long = re_program_sch_cleanup1.sub(r'\1', entryline_sch_long)
                        entryline_sch_long = re_program_sch_cleanup2.sub(r'\1', entryline_sch_long)

                    output_str = f"{entryline_place:>2} {entryline_sch_long:<28} {entryline_relay:1} {entryline_seedtime:>8}"

                output_list.append(( "LANE", output_str ))

            #####################################################################################
            ## PROGRAM: RELAY Add the swimmers name to the list as well
            #####################################################################################
            ## If this is a relay, add a space between the last swimmer name and the next swimmer number
            ## This line  1) LastName1, All2) LastName2, Ashley3) LastName3, All4) LastName4, Eri
            ## becomes    1) LastName1, All 2) LastName2, Ashley 3) LastName3, All 4) LastName4, Eri
            if eventNum in eventNumRelay:
                #found = re.search('\S[2-4]\)',line)
                found = re_program_check_relay_name_line.search(line)
                if found:
                    output_str = re_program_space_relay_name.sub( r'\1 \2',line )
                    output_list.append(( "NAME", output_str ))


    #####################################################################################
    ## Reached end of file
    ## Write out last event
    #####################################################################################

    num_files = create_output_file_program( output_dir, eventNum, heatNum, output_list, displayRelaySwimmerNames, splitRelaysToMultipleFiles )
    num_files_generated += num_files

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
def generate_results_files( report_type, meet_report_filename, output_dir, mm_license_name, shortenSchoolNames, addNewLineToRelayEntries, displayRelaySwimmerNames, namesfirstlast ):
    """ Given the MeetManager results file file formatted in a specific manner,
        generate indiviual result files for use in Wirecast displays """
    
    #####################################################################################
    ## The names are what appear in the report, and may be abbreviated, 
    ##  and not the actual full school name
    ## Multiple version of a school may be listed here for clean output
    #####################################################################################
    resultRelayDictFullNameLen = 22
    resultsIndDictFullNameLen  = 25
    schoolNameDictShortNameLen = 4  # Four character name plus spaces for padding between EntryTime
    resultsDiveDictFullNameLen = 25

    ## NOTE: Do not align up these headers with the TXT output.  
    ##  Wirecast will center all lines and it will be in proper position then
    result_headerLineLong   = "Name                    Yr School                 Seed Time  Finals Time      Points"
    result_headerLineShort  = "Name                    Yr School Seed Time  Finals Time      Points"
    result_headerLineRelayLong  = "   Team                       Relay                  Seed Time  Finals Time      Points"
    result_headerLineRelayShort = "   Team       Relay Seed Time  Finals Time Points"
    result_headerLineDivingLong  = "Name                    Yr School                           Finals Score      Points"
    result_headerLineDivingShort = "Name    Yr School                           Finals Score      Points"


    ## Define local variables
    eventNum = 0
    num_files_generated = 0
    num_header_lines = 3
    found_header_line = 0
    output_list = []

    re_results_lane = re.compile('^[*]?\d{1,2} ')

    # #                                 TIE? PLACE       LAST          FIRST     GR           SCHOOL           SEEDTIME|NT    FINALTIME      POINTS
    #re_results_lane_ind = re.compile('^([*]?\d{1,2})\s+(\w+, \w+)\s+(\w+) ([A-Z \'.].*?)\s*([0-9:.]+|NT)\s+([0-9:.]+)\s*([0-9]*)')
    re_results_lane_ind  = re.compile('^([*]?\d{1,2})\s+([A-z\' \.]+, [A-z ]+) ([A-Z0-9]{1,2})\s+([A-Z \'.].*?)\s*([0-9:.]+|NT)\s+([0-9:.]+)\s*([0-9]*)')

    #                                     TIE? PLACE   SCHOOL           RELAY     SEEDTIME|NT    FINALTIME     POINTS
    re_results_lane_relay = re.compile('^([*]?\d{1,2})\s+([A-Z \'.].*)\s+([A-Z])\s+([0-9:.]+|NT)\s+([0-9:.]+)\s*([0-9]*)')

    re_results_space_relay_name = re.compile(r'(\S)([2-4]\))')
    re_results_check_relay_name_line = re.compile('1\)')

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
            ## Meet Manager license name
            ## We have one event per page, so this starts the next event
            #####################################################################################
            if re.search("^%s" % mm_license_name, line):
                found_header_line = 1
                
                ## Start the next event file
                num_files = create_output_file_results( output_dir, eventNum, output_list, displayRelaySwimmerNames )
                num_files_generated += num_files

                ## Reset and start processing the next event
                output_list = []
                output_list.append( ('H1', line ))
                continue

            #####################################################################################
            ## if the previous line was the first header (found_header_line=1)
            ## then ignore the next two lines which are also part of the header
            #####################################################################################
            if 0 < found_header_line < num_header_lines:
                found_header_line += 1
                if found_header_line == 2:
                    output_list.append( ('H2', line ))
                elif found_header_line == 3:
                    output_list.append( ('H3', line ))
                continue

            #####################################################################################
            ## Ignore these lines
            #####################################################################################
            ## Ignore the Header for the place winners
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

                ## Remove all those extra spaces in the line
                clean_event_str = line.split()
                clean_event_str = " ".join(clean_event_str)
                # Get the line number
                event_str = clean_event_str.split(' ', 4)
                eventNum = int(event_str[1].strip())

                ## H4 is the Event number/name line
                output_list.append(('H4', f"{line} {unofficial_results}" ))

                #####################################################################################
                ## RESULTS: Set nameListHeader to be displayed above the list of swimmers
                #####################################################################################
                # Set the default (LONG) headers here. 
                nameListHeader = ""
                if eventNum in eventNumIndividual:
                    nameListHeader = result_headerLineShort if shortenSchoolNames else result_headerLineLong
                elif eventNum in eventNumDiving:
                        nameListHeader = result_headerLineDivingShort if shortenSchoolNames else result_headerLineDivingLong
                elif eventNum in eventNumRelay:
                    nameListHeader = result_headerLineRelayShort if shortenSchoolNames else result_headerLineRelayLong

                if nameListHeader != "":
                    output_list.append(('H6', nameListHeader))

            #####################################################################################
            ## RESULTS: For place winner results, add a space after top 1-9 swimmers 
            ##          so names line up with 10-12 place
            #####################################################################################
            if re.search("^[1-9] ", line):
                line = re.sub('^([1-9]) ', r'\1  ', line )
    
            #####################################################################################
            ## RESULTS: INDIVIDUAL Find the Place Winner line, place, name, school, time, points, etc
            ## i.e. 1 Last, First           SR SCH   5:31.55      5:23.86        16
            ## Note: For ties an asterick is placed before the place number and the points could have a decimal
            #####################################################################################
            if (eventNum in eventNumIndividual or eventNum in eventNumDiving) and re_results_lane.search(line):
                place_line_list = re_results_lane_ind.findall(line)
                if place_line_list:
                    placeline_place       = str(place_line_list[0][0]).strip()
                    placeline_name_last_first = str(place_line_list[0][1]).strip()
                    placeline_grade       = str(place_line_list[0][2]).strip()
                    placeline_school_long = str(place_line_list[0][3]).strip()
                    placeline_seedtime    = str(place_line_list[0][4]).strip()
                    placeline_finaltime   = str(place_line_list[0][5]).strip()
                    placeline_points      = str(place_line_list[0][6]).strip()

                    logger(f"RESULTS: place {placeline_place}: name {placeline_name_last_first}: grade {placeline_grade}: sch {placeline_school_long}: seed {placeline_seedtime}: final {placeline_finaltime}: points {placeline_points}:")
                    ## If we want to use Shortened School Names, run the lookup
                    if shortenSchoolNames:
                        ## The length of the school name in the MM report varies by event type
                        school_name_len = resultsIndDictFullNameLen if eventNum in eventNumIndividual else resultsDiveDictFullNameLen
                        

                        placeline_school_short = placeline_school_long
                        for k,v in schoolNameDict.items():
                            placeline_school_short = placeline_school_short.replace(k[:school_name_len], v.ljust(schoolNameDictShortNameLen, ' '))
                            if placeline_school_short != placeline_school_long:
                                break

                    ## We can display name as given (Last, First) or change it to First Last with cli parameter
                    if namesfirstlast:
                        result_name_last, result_name_first = placeline_name_last_first.split(',',1)
                        result_name_first = result_name_first.strip()
                        result_name_last  = result_name_last.strip()
                        placeline_name_first_last = f"{result_name_first} {result_name_last}"
                        result_name = placeline_name_first_last
                    else:
                        result_name = placeline_name_last_first

                    ## Format the output lines with either long (per meet program) or short school names
                    output_str = f"{placeline_place:>3} {result_name:<25} {placeline_grade:>2} {placeline_school_long:<25} {placeline_seedtime:>8} {placeline_finaltime:>8} {placeline_points:>2}"
                    if shortenSchoolNames:
                        output_str = f"{placeline_place:>3} {result_name:<25} {placeline_school_short:<4} {placeline_grade:>2} {placeline_seedtime:>8} {placeline_finaltime:>8} {placeline_points:>2}"
                    
                    output_list.append(('PLACE', output_str))
            
            #####################################################################################
            ## RESULTS: RELAY Find the Place Winner line, place, name, school, time, points, etc
            ## 1 SST            A                    1:46.82      1:40.65        32
            ## Note: For ties an asterick is placed before the place number and the points could have a decimal
            #####################################################################################
            if eventNum in eventNumRelay and re_results_lane.search(line):
                place_line_list = re_results_lane_relay.findall(line)

                if place_line_list:
                    placeline_place     = str(place_line_list[0][0])
                    placeline_sch_long  = str(place_line_list[0][1])
                    placeline_relay     = str(place_line_list[0][2])
                    placeline_seedtime  = str(place_line_list[0][3])
                    placeline_finaltime = str(place_line_list[0][4])
                    placeline_points    = str(place_line_list[0][5])

                    #####################################################################################
                    ## RESULTS: Replace long school name with short name for RELAY events
                    #####################################################################################
                    if shortenSchoolNames:
                        placeline_sch_short = placeline_sch_long

                        for k,v in schoolNameDict.items():
                            placeline_sch_short = placeline_sch_short.replace(k.ljust(resultRelayDictFullNameLen,' ')[:resultRelayDictFullNameLen], v.ljust(schoolNameDictShortNameLen, ' '))
                            if placeline_sch_short != placeline_sch_long:
                                break

                        output_str = f" {placeline_place:>3} {placeline_sch_short:<4} {placeline_relay} {placeline_seedtime:>8} {placeline_finaltime:>8} {placeline_points:>2}"
                    else:
                        output_str = f" {placeline_place:>3} {placeline_sch_long:<25} {placeline_relay} {placeline_seedtime:>8} {placeline_finaltime:>8} {placeline_points:>2}"
                    output_list.append(( "PLACE", output_str ))

            #####################################################################################
            ## RESULTS: Processing specific to RELAY Entries
            #####################################################################################
            ## If this is a relay, see if there are spaces between swimmer numbers
            ## If so, add a space between the last swimmer name and the next swimmer number
            ## This line  1) LastName1, All2) LastName2, Ashley3) LastName3, All4) LastName4, Eri
            ## becomes    1) LastName1, All 2) LastName2, Ashley 3) LastName3, All 4) LastName4, Eri
            #####################################################################################
            #####################################################################################
            ## RESULTS: For results on relays and the swimmers name as well to the list
            ##          Its up to the output function to determine to display them or not
            #####################################################################################
            if displayRelaySwimmerNames and eventNum in eventNumRelay:
                found = re_results_check_relay_name_line.search(line)
                if found:
                    line = re_results_check_relay_name_line.sub( r'\1 \2',line )
                    output_list.append(( "NAME", line )) 


    #####################################################################################
    ## Reached end of file
    ## Write out last event
    #####################################################################################

    create_output_file_results( output_dir, eventNum, output_list, displayRelaySwimmerNames )
    num_files_generated += 1

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
##########    C R A W L E R    R E S U L T S    
##########    generate_crawler_result_files
##########
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
def generate_crawler_result_files( report_type, meet_report_filename, output_dir, mm_license_name, shorten_school_names, display_swimmers_in_relay ):
    """  From the Meet Results File, generate the crawler files per event """

    eventNum = 0
    #official_results = "OFFICIAL RESULTS"
    official_results = "UNOFFICIAL RESULTS"
    crawler_string = official_results
    found_header_line = 0
    num_header_lines = 3
    schoolNameDictFullNameLen = 25
    schoolNameDictShortNameLen = 4

    ## Tracking searcing for/finding/processing the three header records on each input file
    ## For crawler, we only want the header once
    processed_header_list = {"found_header_1": False, "found_header_2": False, "found_header_3": False}
    crawler_list = []

    re_crawler_lane = re.compile('^[*]?\d{1,2} ')
    #                                     TIE? place    last first   GR    SCHOOL           SEEDTIME    FINALTIME      POINTS
    re_crawler_lane_ind = re.compile('^([*]?\d{1,2})\s+(\w+, \w+)\s+(\w+) ([A-Z \'.].*?)\s*([0-9:.]+|NT)\s+([0-9:.]+)\s*([0-9]*)')
    
    #  REGEX Positions                    TIE? PLACE   SCHOOL    RELAY     SEEDTIME    FINALTIME     POINTS
    re_crawler_lane_relay = re.compile('^([*]?\d{1,2})\s+([A-Z \'.].*)\s+([A-Z])\s+([0-9:.]+|NT)\s+([0-9:.]+)\s*([0-9]*)')


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
            ##  Once we find the first header line, the next two lines we process are also headers            
            #####################################################################################
            ## Meet Manager license name
            if re.search("^%s" % mm_license_name, line):
                found_header_line = 1
                #if not recorded_header1:
                if not processed_header_list['found_header_1']:
                    processed_header_list['found_header_1'] = True
                    crawler_list.append( (headerNum1, line ))
                continue

            ## if the previous line was the first header (found_header_line=1)
            ## then ignore the next two lines which are also part of the header
            if 0 < found_header_line < num_header_lines:
                found_header_line += 1
                if not processed_header_list['found_header_2'] and found_header_line == 2:
                    crawler_list.append( (headerNum2, line ))
                    processed_header_list['found_header_2'] = True
                elif not processed_header_list['found_header_3'] and found_header_line == 3:
                    crawler_list.append( (headerNum3, line ))
                    processed_header_list['found_header_3'] = True

                continue

            ## Ignore these lines too
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
                    crawler_string = official_results

                #####################################################################################
                ## Start processing next event
                #####################################################################################

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
                crawler_string += output_str


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
            if (eventNum in eventNumIndividual  or eventNum in eventNumDiving) and re_crawler_lane.search(line):
                place_line_list = re_crawler_lane_ind.findall(line)
                if place_line_list:
                    placeline_place     = str(place_line_list[0][0])
                    placeline_name      = str(place_line_list[0][1])
                    #placeline_grade     = str(place_line_list[0][2])
                    placeline_sch_long  = str(place_line_list[0][3])
                    #placeline_seedtime  = str(place_line_list[0][4])
                    #placeline_finaltime = str(place_line_list[0][5])
                    #placeline_points    = str(place_line_list[0][6])


                    #####################################################################################
                    ## CRAWLER: Replace long school name with short name for ALL events
                    #####################################################################################
                    school_name_short = placeline_sch_long
                    for k,v in schoolNameDict.items():
                        school_name_short = school_name_short.replace(k, v)
                        if school_name_short != placeline_sch_long:
                            break
                        
                    if shorten_school_names:
                        output_str = f" {placeline_place}) {placeline_name} {school_name_short}"
                    else:
                        output_str = f" {placeline_place}) {placeline_name} {placeline_sch_long}"
                    crawler_string += output_str


            #####################################################################################
            ## CRAWLER: RELAY Find the Place Winner line, place, name, school, time, points, etc
            ## 1 SST            A                    1:46.82      1:40.65        32
            ## Note: For ties an asterick is placed before the place number and the points could have a decimal
            #####################################################################################
            if eventNum in eventNumRelay and re_crawler_lane.search(line):
                place_line_list = re_crawler_lane_relay.findall(line)

                if place_line_list:
                    placeline_place     = str(place_line_list[0][0]).strip()
                    placeline_sch_long  = str(place_line_list[0][1]).strip()
                    placeline_relay     = str(place_line_list[0][2]).strip()
                    #placeline_seedtime  = str(place_line_list[0][3]).strip()
                    #placeline_finaltime = str(place_line_list[0][4]).strip()
                    #placeline_points    = str(place_line_list[0][5]).strip()

                    if shorten_school_names:
                        placeline_sch_short = placeline_sch_long
                        x = len(placeline_sch_long)

                        for k,v in schoolNameDict.items():
                            placeline_sch_short = placeline_sch_short.replace(k.ljust(len(k),' '), v)
                            if placeline_sch_short != placeline_sch_long:
                                break
                        output_str = f" {placeline_place}) {placeline_sch_short} {placeline_relay}"
                    else:
                        output_str = f" {placeline_place}) {placeline_sch_long} {placeline_relay}"

                    crawler_string += output_str  


    #####################################################################################
    ## Save last event string
    #####################################################################################
    crawler_list.append( (eventNum, crawler_string ))

    #####################################################################################
    ## Write data saved in list to files
    #####################################################################################
    total_files_generated = create_output_file_crawler( report_type, output_dir, crawler_list )

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
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-i', '--inputdir',         dest='inputdir',            default="../data",              required=True,   
                                                                                                                help="input directory for MM extract report")
    parser.add_argument('-t', '--reporttype',       dest='reporttype',          default=report_type_program,    choices=['program','result', 'crawler', 'headers'], 
                                                                                                                help="Program type, Meet Program or Meet Results")
    parser.add_argument('-o', '--outputdir',        dest='outputdir',           default="../output/",           help="root output directory for wirecast heat files.")
    parser.add_argument('-n', '--namesfirstlast',   dest='namesfirstlast',      action='store_true',            help="Swap Non Relay names to First Last from Last, First")
    parser.add_argument('-s', '--shortschoolnames', dest='shortschoolnames',    action='store_true',            help="Use Short School names for Indiviual Entries")
    parser.add_argument('-l', '--longschoolnames',  dest='shortschoolnames',    action='store_false',           help="Use Long School names for Indiviual Entries")
    parser.add_argument('-L', '--licenseName',      dest='licenseName',         default="Seton School",         help="MM license name as printed out on reports")
    parser.add_argument('-r', '--splitrelays',      dest='splitrelays',         action='store_true',            help="Split Relays into multiple files")
    parser.add_argument('-R', '--displayRelayNames',dest='displayRelayNames',   action='store_true',            help="Display relay swimmer names, not just the team name in results")
    parser.add_argument('-d', '--debug',            dest='debug',               action='store_true',            help="Print out results to console")
    parser.add_argument('-D', '--delete',           dest='delete',              action='store_true',            help="Delete existing files in OUTPUT_DIR")
    parser.add_argument('-h', '--help',             dest='help',                action='help', default=argparse.SUPPRESS,                 help="Tested with MM 8")
    parser.set_defaults(shortschoolnames=True)
    parser.set_defaults(splitrelays=False)
    parser.set_defaults(displayRelayNames=False)
    parser.set_defaults(namesfirstlast=False)
    parser.set_defaults(DEBUG=False)
    parser.set_defaults(delete=False)

    args = parser.parse_args()
    
    ## Set global debug flag
    DEBUG = args.debug
    total_files_generated = 0


    #####################################################################################
    ## Get header info from the meet file
    ## We need to dynamically get the meet name and license_name for use in processing files
    ## The license_name is the first line on the start of every new page/event/heat
    #####################################################################################
    meet_name, meet_date, license_name, report_type = get_report_header_info( args.reporttype, args.inputdir )



    output_dir = args.outputdir
    ## The outputdir string MUST have a trailing slash.  Check string and add it if necesssary
    if output_dir[-1] != '/':
        output_dir = f"{output_dir}/"
    
    logargs = f"{Path(__file__).stem}  \n" + \
              f"\n   Params: \n" + \
              f"\tOutputReportType \t{args.reporttype} \n" + \
              f"\tInputDir \t\t{args.inputdir} \n" + \
              f"\tRoot OutputDir \t\t{output_dir} \n" + \
              f"\tLicensee: \t\t'{args.licenseName}' \n" + \
              f"\tShort School Names \t{args.shortschoolnames} \n" + \
              f"\tNamesFirstlast \t{args.namesfirstlast} \n" + \
              f"\tSplit Relays \t\t{args.splitrelays} \n"+ \
              f"\tDisplay Relays Names \t{args.displayRelayNames} \n"+ \
              f"\tSpaces in Relay Names \t{spacerelaynames}\n" + \
              f"\tDelete exiting files \t{args.delete}\n" + \
              f"\n   Headers: \n" + \
              f"\tMeet Name: \t\t'{meet_name}' \n" + \
              f"\tMeet Date: \t\t'{meet_date}' \n" + \
              f"\tLicensee: \t\t'{license_name}' \n" + \
              f"\tSourceReport: \t\t'{report_type}' \n" 
    print( logargs )

    #####################################################################################
    ## Remove files from last run
    #####################################################################################
    if args.delete:
        remove_files_from_dir( args.reporttype, output_dir )

    #####################################################################################
    ## Generate wirecast files from a MEET PROGRAM txt file
    #####################################################################################
    if args.reporttype == report_type_program:
        total_files_generated = generate_program_files( args.reporttype, args.inputdir, output_dir, args.licenseName, args.shortschoolnames, args.splitrelays, spacerelaynames, args.displayRelayNames, args.namesfirstlast )
        print(f"Process Completed: \n\tNumber of files generated: {total_files_generated}")


    #####################################################################################
    ## Generate wirecast files RESULTS and CRAWLER from a MEET RESULTS txt file
    #####################################################################################
    if args.reporttype == report_type_results:
        total_files_generated_results =  generate_results_files( report_type_results, args.inputdir, output_dir, args.licenseName, args.shortschoolnames, args.displayRelayNames, args.displayRelayNames, args.namesfirstlast )
        total_files_generated_crawler =  generate_crawler_result_files( report_type_results, args.inputdir, output_dir, args.licenseName, args.shortschoolnames, args.displayRelayNames )
        total_files_generated = total_files_generated_results + total_files_generated_crawler
        print(f"Process Completed: \n\tNumber of files generated total:\t{total_files_generated}")
        print(f"\tNumber of files generated results:\t{total_files_generated_results}")
        print(f"\tNumber of files generated crawler:\t{total_files_generated_crawler}")

    #####################################################################################
    ## Generate wirecast CRAWLER iles from a MEET RESULTS txt file
    #####################################################################################
    if args.reporttype == report_type_crawler:
        total_files_generated_crawler =  generate_crawler_result_files( report_type_results, args.inputdir, output_dir, args.licenseName, args.shortschoolnames, args.displayRelayNames )
        print(f"Process Completed: \n\tNumber of files generated total:\t{total_files_generated_crawler}")
