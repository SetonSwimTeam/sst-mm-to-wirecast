import os                
import logging
import re

import sst_module_common as sst_common

#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
########## 
##########    C R A W L E R    R E S U L T S    
##########    process_crawler
##########
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
def process_crawler( meet_report_filename: str, 
                     output_dir: str, 
                     mm_license_name: str, 
                     shorten_school_names_relays: bool, 
                     shorten_school_names_individual: bool, 
                     display_swimmers_in_relay: bool, 
                     quote_output: bool,
                     num_results_to_display: int,
                     last_num_events: int ):
    """  From the Meet Results File, generate the crawler files per event """
    crawler_relay_dict_full_name_len = 22

    event_num = 0
    num_results_generated = 0
    #official_results = "OFFICIAL RESULTS"
    official_results = "UNOFFICIAL RESULTS"
    crawler_string = official_results
    found_header_line = 0
    num_header_lines = 3
    # school_name_dict_full_name_len = 25
    # school_name_dict_short_name_len = 4

    ## Tracking searcing for/finding/processing the three header records on each input file
    ## For crawler, we only want the header once
    processed_header_list = {"found_header_1": False, "found_header_2": False, "found_header_3": False}
    crawler_list = []

    re_crawler_lane = re.compile('^[*]?\d{1,2} ')
    #                                     TIE? place    last first   GR    SCHOOL           SEEDTIME    FINALTIME      POINTS
    #re_crawler_lane_ind   = re.compile('^([*]?\d{1,2})\s+(\w+, \w+)\s+(\w+) ([A-Z \'.].*?)\s*([0-9:.]+|NT)\s+([0-9:.]+)\s*([0-9]*)')
    re_crawler_lane_ind = re.compile('^([*]?\d{1,2})\s+([A-z\' \.]+, [A-z ]+) ([A-Z0-9]{1,2})\s+([A-Z \'.].*?)\s*([0-9:.]+|NT)\s+([0-9:.]+)\s*([0-9]*)')

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
                    crawler_list.append( ( sst_common.headerNum1, line ))
                continue

            ## if the previous line was the first header (found_header_line=1)
            ## then ignore the next two lines which are also part of the header
            if 0 < found_header_line < num_header_lines:
                found_header_line += 1
                if not processed_header_list['found_header_2'] and found_header_line == 2:
                    crawler_list.append( (sst_common.headerNum2, line ))
                    processed_header_list['found_header_2'] = True
                elif not processed_header_list['found_header_3'] and found_header_line == 3:
                    crawler_list.append( (sst_common.headerNum3, line ))
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
                if event_num > 0:
                    crawler_list.append( (event_num, crawler_string  ))
                    crawler_string = official_results

                #####################################################################################
                ## Start processing next event
                #####################################################################################
                event_num, clean_event_str = sst_common.get_event_num_from_eventline( line )

                ## Clear out old string and start new for next event
                num_results_generated = 0
                output_str = ""
                for element in clean_event_str:
                    output_str += f" {element}"
                crawler_string += output_str

                #logging.debug(f"CRAWLER: e: {event_num} line: {line}")

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
            if (event_num in sst_common.event_num_individual  or event_num in sst_common.event_num_diving) and re_crawler_lane.search(line):
                place_line_list = re_crawler_lane_ind.findall(line)
                if place_line_list:
                    num_results_generated += 1
                    placeline_place     = str(place_line_list[0][0]).strip()
                    placeline_name      = str(place_line_list[0][1]).strip()
                    #placeline_grade     = str(place_line_list[0][2])
                    placeline_sch_long  = str(place_line_list[0][3]).strip()
                    #placeline_seedtime  = str(place_line_list[0][4])
                    placeline_finaltime = str(place_line_list[0][5])
                    #placeline_points    = str(place_line_list[0][6])
                
                    logging.debug(f"CRAWLER: e: {event_num} line: {line}")

                    #####################################################################################
                    ## CRAWLER: Replace long school name with short name for ALL events
                    #####################################################################################
                    school_name_short = sst_common.short_school_name_lookup( placeline_sch_long, crawler_relay_dict_full_name_len )
                        
                    if shorten_school_names_individual:
                        output_str = f" {placeline_place}) {placeline_name} {school_name_short} {placeline_finaltime}"
                    else:
                        output_str = f" {placeline_place}) {placeline_name} {placeline_sch_long} {placeline_finaltime}"

                    ## Only output given number of results
                    if num_results_generated <= num_results_to_display:
                        crawler_string += output_str



            #####################################################################################
            ## CRAWLER: RELAY Find the Place Winner line, place, name, school, time, points, etc
            ## 1 SST            A                    1:46.82      1:40.65        32
            ## Note: For ties an asterick is placed before the place number and the points could have a decimal
            #####################################################################################
            if event_num in sst_common.event_num_relay and re_crawler_lane.search(line):
                place_line_list = re_crawler_lane_relay.findall(line)

                if place_line_list:
                    num_results_generated += 1
                    placeline_place     = str(place_line_list[0][0]).strip()
                    placeline_sch_long  = str(place_line_list[0][1]).strip()
                    placeline_relay     = str(place_line_list[0][2]).strip()
                    #placeline_seedtime  = str(place_line_list[0][3]).strip()
                    placeline_finaltime = str(place_line_list[0][4]).strip()
                    #placeline_points    = str(place_line_list[0][5]).strip()

                    if shorten_school_names_relays:
                        placeline_sch_short = placeline_sch_long

                        school_name_short = short_school_name_lookup( placeline_sch_long, crawler_relay_dict_full_name_len )
                        output_str = f" {placeline_place}) {school_name_short} {placeline_relay} {placeline_finaltime}"
                    else:
                        output_str = f" {placeline_place}) {placeline_sch_long} {placeline_relay} {placeline_finaltime}"

                    ## Only output given number of results
                    if num_results_generated <= num_results_to_display:
                        crawler_string += output_str  

    #####################################################################################
    ## Save last event string
    #####################################################################################
    crawler_list.append( (event_num, crawler_string ))

    #####################################################################################
    ## Write data saved in list to files
    #####################################################################################
    total_files_generated = create_output_file_crawler( output_dir, crawler_list, num_results_to_display, last_num_events )

    return total_files_generated



#####################################################################################
## create_output_file_crawler
##
## Given a list of tuples (evnt num, crawler_string), generate output files
## Generate crawler files for actual events (event_num > 0) and for meet name (event_num = -2)
#####################################################################################
def create_output_file_crawler( output_dir_root: str, crawler_list: list, num_results_to_display: int, last_num_events: int ):
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

        logging.info(f"crawler: e: {event_num} t: {crawler_text}")
        ## Generate event specific file
        if event_num > 0:
            output_file_name = output_dir + f"{file_name_prefix}_result_event{event_num:0>2}.txt"
            sst_common.write_output_file( output_file_name, crawler_text )
            num_files_generated += 1
        ## Genreate special file for the meet name
        elif event_num == sst_common.headerNum2:
            output_file_name = output_dir + f"{file_name_prefix}__MeetName.txt"
            sst_common.write_output_file( output_file_name, crawler_text )
            num_files_generated += 1

    ## Generate single file for all scored events in reverse order
    crawler_text = ""
    crawler_text_last_num_events = ""
    meet_name = ""
    num_events = len(crawler_list)
    last_num_events_generated = 0

    ## Loop through list in reverse order to generate crawler string with multiple events
    for num in range( num_events-1, -1, -1):
        crawler_event = crawler_list[num]
        event_num = crawler_event[0]
        event_text = crawler_event[1]

        ## Save off the meet name, which somes at the end of the procesing as we are looping in reverse order
        if event_num > 0:
            crawler_text += f" | {event_text}"
            if last_num_events_generated <= last_num_events:
                crawler_text_last_num_events += f" | {event_text}"
                last_num_events_generated += 1
        elif event_num == sst_common.headerNum2:
            meet_name = event_text        

    ## Add meet_name to front of string
    crawler_text = f"{meet_name} {crawler_text}"
    ## Create the crawler file with ALL events completed so far
    all_events_file_name = f"{file_name_prefix}__AllEventsReverse.txt"
    output_file_name = output_dir + all_events_file_name
    sst_common.write_output_file( output_file_name, crawler_text )
    num_files_generated += 1

    ## Create the crawler file with last_num events
    #last_xx_events_file_name = f"{file_name_prefix}__Last_{last_num_events:0>2}_events.txt"
    last_xx_events_file_name = f"{file_name_prefix}__Last_XX_events.txt"
    output_file_name = output_dir + last_xx_events_file_name
    sst_common.write_output_file( output_file_name, crawler_text_last_num_events )
    num_files_generated += 1

    return num_files_generated



