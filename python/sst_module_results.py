import logging
import re
import sst_module_common as sst_common


g_unofficial_results = "    ** UNOFFICIAL RESULTS **"

## Define file names for output files
g_file_name_prefix = "event_"
g_file_name_suffix = "RESULTS"
g_file_name_awards = "AWARDS"
g_crawler_name_prefix = "x_crawler_results"


#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
##########
##########    S S T _ M O D U L E _ R E S U L T S 
##########
##########    Code to generate Event entry files from the meet program
##########
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################

####################################################################################
## Parse the report file and generate an output array
#####################################################################################
def process_result( meet_report_filename: str, 
                    output_dir: str, 
                    mm_license_name: str, 
                    shorten_school_names_relays: bool, 
                    shorten_school_names_individual: bool, 
                    add_new_line_to_relay_entries: bool, 
                    display_relay_swimmer_names: bool, 
                    namesfirstlast: bool, 
                    quote_output: bool,
                    num_results_to_display: int,
                    crawler_last_xx_results: int,
                    generate_crawler: bool,
                    championshipmeet: bool,
                    awards:bool ) -> int:
    """ Given the MeetManager results file file formatted in a specific manner,
        generate indiviual result files for use in Wirecast displays """


    result_header_len_dict = {
        'individual_long': 25,
        'diving_long': 25,
        'relay_long': 22,
    }

    ## NOTE: Do not align up these headers with the TXT output.  
    ##  Wirecast will center all lines and it will be in proper position then
    champsionship_result_header_dict = {
        'individual_long':   "Name                    Yr School                 Seed Time  Finals Time      Points",
        'individual_short':  "        Name                  School Yr   Seed   Finals   Pts",
        'diving_long':       "Name                    Yr School                           Finals Score      Points",
        'diving_short':      "        Name                 School Yr   Seed     Final Pts",
        'relay_long':         "           Team                  Relay Seed     Finals  Pts",        
        'relay_short':       "   Team       Relay Seed Time  Finals Time Points",    
    }
    result_header_dict = {
        'individual_long':   "Name                    Yr School                 Seed Time  Finals Time            ",
        'individual_short':  "        Name                  Sch  Yr    Seed    Finals      ",
        'diving_long':       "Name                    Yr School                           Finals Score           ",
        'diving_short':      "        Name                 School Yr   Seed     Final     ",
        'relay_long':         "           Team                  Relay  Seed   Finals     ",        
        'relay_short':       "   Team       Relay Seed Time  Finals Time       ",    
    }
    ## Define local variables
    event_num = 0
    num_files_generated = 0
    num_crawler_files_generated = 0
    num_header_lines = 3
    found_header_line = 0
    output_list = []
    crawler_list = []
    crawler_str = ""
    contimue_processing_current_event = True

    # re_results_lane = re.compile('^[*]?\d{1,2} ')
    # re_results_lane = re.compile('^--- ')
    re_results_lane = re.compile('^([*]?\d{1,2} )|(--- )')


    # #                                 TIE? PLACE       LAST          FIRST     GR           SCHOOL           SEEDTIME|NT|NP    [xX]FINALTIME      POINTS
    #re_results_lane_ind  = re.compile('^([*]?\d{1,2})\s+([A-z\' \.]+, [A-z ]+?) ([A-Z0-9]{1,2})\s+([A-Z \'.].*?)([0-9:.]+|NT)\s+([0-9:.]+)\s*([X]?[0-9]*)')
    re_results_lane_ind  = re.compile('^([*]?\d{1,2}|---)\s+([A-z\' \.]+, [A-z ]+?) ([A-Z0-9]{1,2})\s+([A-Z \'.].*?)([0-9:.]+|NT|NP)\s+([X]DQ|[xX0-9:.]+)\s*([0-9]*)')

    #                                     TIE? PLACE   SCHOOL           RELAY     SEEDTIME|NT    FINALTIME     POINTS
    #re_results_lane_relay = re.compile('^([*]?\d{1,2})\s+([A-Z \'.].*)\s+([A-Z])\s+([0-9:.]+|NT)\s+([0-9:.]+)\s*([0-9]*)')
    re_results_lane_relay = re.compile('^([*]?\d{1,2}|---)\s+([A-Z \'.].*)\s+([A-Z])\s+([0-9:.]+|NT)\s+([X]DQ|[xX0-9:.]+)\s*([0-9]*)')

    re_results_space_relay_name = re.compile(r'(\S)([2-4]\))')
    re_results_check_relay_name_line = re.compile('1\)')

    ## Quote output for debuggin
    q = "'" if quote_output else ""

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
                
                ## The start of the next event finished off the last event. Go write out the last event
                if contimue_processing_current_event:
                    num_files = create_output_file( output_dir, event_num, output_list, display_relay_swimmer_names, num_results_to_display, awards )
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
            ## RESULTS: Start with Event line.  
            ##  Get the Event Number from the report
            ##  Clean it up
            #####################################################################################
            if line.lower().startswith(("event")):
                logging.info(f"RESULTS: EVENT LINE: {line}")
                contimue_processing_current_event = True

                # # Starting a new event. Save crawler string for this past event in the list for later procesing
                if event_num > 0:
                    crawler_list.append( (event_num, crawler_str  ))

                event_num, event_str = sst_common.get_event_num_from_eventline( line )

                ## Start new crawler_str for next event
                crawler_str = f"Unofficial Results: Event {event_num} {event_str}: "

                ## H4 is the Event number/name line
                # output_list.append(('H4', f"{line} {g_unofficial_results}" ))
                output_list.append(('H4', f"{line}" ))

                #####################################################################################
                ## RESULTS: Set name_list_header to be displayed above the list of swimmers
                #####################################################################################
                header_dict = champsionship_result_header_dict if championshipmeet else result_header_dict
                name_list_header = sst_common.get_header_line( event_num, shorten_school_names_relays, shorten_school_names_individual, header_dict ) 

                if name_list_header != "":
                    output_list.append(('H6', name_list_header))

            #####################################################################################
            ## RESULTS: Looks for a second page of results 
            ##  Stop processing when this occurs.  We can't display even a single full page
            #####################################################################################
            if line.lower().startswith(("(event")):
                contimue_processing_current_event = False

                num_files = create_output_file( output_dir, event_num, output_list, display_relay_swimmer_names, num_results_to_display, awards )
                num_files_generated += num_files


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
            if (event_num in sst_common.event_num_individual or event_num in sst_common.event_num_diving) and re_results_lane.search(line):
                place_line_list = re_results_lane_ind.findall(line)
                if place_line_list:
                    placeline_place       = str(place_line_list[0][0]).strip()
                    placeline_name_last_first = str(place_line_list[0][1]).strip()
                    placeline_grade       = str(place_line_list[0][2]).strip()
                    placeline_school_long = str(place_line_list[0][3]).strip()
                    placeline_seedtime    = str(place_line_list[0][4]).strip()
                    placeline_finaltime   = str(place_line_list[0][5]).strip()
                    placeline_points      = str(place_line_list[0][6]).strip()              

                    logging.debug(f"RESULTS: place {placeline_place}: name {placeline_name_last_first}: grade {placeline_grade}: sch {placeline_school_long}: seed {placeline_seedtime}: final {placeline_finaltime}: points {placeline_points}:")
                    ## If we want to use Shortened School Names, run the lookup
                    ## The length of the school name in the MM report varies by event type
                    school_name_len = result_header_len_dict['individual_long']  if event_num in sst_common.event_num_individual else result_header_len_dict['diving_long']
                    placeline_school_short = sst_common.short_school_name_lookup( placeline_school_long, school_name_len )

                    ## We can display name as given (Last, First) or change it to First Last with cli parameter
                    result_name = sst_common.reverse_lastname_firstname( placeline_name_last_first ) if namesfirstlast else placeline_name_last_first

                    ## Format the output lines with either long (per meet program) or short school names
                    # with points
                    
                    #full_team_name = placeline_school_long
                    full_team_name = sst_common.find_proper_team_name( placeline_school_long )

                    # output_str = f"{q}{placeline_place:>3}{q} {q}{result_name:<25}{q} {q}{placeline_grade:>2}{q} {q}{placeline_school_long:<25}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q} {q}{placeline_points:>2}{q}"

                    points_str = f"{q}{placeline_points:>4}{q}" if champsionship_result_header_dict else ""
                    output_str = f"{q}{placeline_place:>3}{q} {q}{result_name:<25}{q} {q}{placeline_grade:>2}{q} {q}{full_team_name:<25}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q} {points_str}"
                    
                    if shorten_school_names_individual:
                        #output_str = f"{q}{placeline_place:>3}{q} {q}{result_name:<25}{q} {q}{placeline_school_short:<4}{q} {q}{placeline_grade:>2}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q} {q}{placeline_points:>2}{q}"
                        output_str = f"{q}{placeline_place:>3}{q} {q}{result_name:<25}{q} {q}{placeline_school_short:<4}{q} {q}{placeline_grade:>2}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q}{points_str}"
                    
                    output_list.append(('PLACE', output_str))
                    crawler_str += gen_result_crawler_ind( placeline_place, result_name, placeline_grade,placeline_school_short, placeline_school_long, placeline_seedtime, placeline_finaltime, placeline_points )

            #####################################################################################
            ## RESULTS: RELAY Find the Place Winner line, place, name, school, time, points, etc
            ## 1 SST            A                    1:46.82      1:40.65        32
            ## Note: For ties an asterick is placed before the place number and the points could have a decimal
            #####################################################################################
            # if event_num in sst_common.event_num_relay and re_results_lane.search(line):
            if event_num in sst_common.event_num_relay:
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
                    placeline_sch_short = sst_common.short_school_name_lookup( placeline_sch_long, result_header_len_dict['relay_long'] )

                    ## Relay results are strange.  They give you 30 characters but truncate school to 22 characters
                    ## Remove remaing spaces
                    placeline_sch_short = placeline_sch_short.strip()

                    points_str = f"{q}{placeline_points:>4}{q}" if champsionship_result_header_dict else ""

                    if shorten_school_names_relays:                        
                        #output_str = f" {q}{placeline_place:>3}{q} {q}{placeline_sch_short:<4}{q} {q}{placeline_relay}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q} {q}{placeline_points:>2}{q}"
                        output_str = f" {q}{placeline_place:>3}{q} {q}{placeline_sch_short:<4}{q} {q}{placeline_relay}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q} {points_str}"
                    else:
                        #full_team_name = placeline_sch_long
                        full_team_name = sst_common.find_proper_team_name( placeline_sch_long )

                        #output_str = f" {q}{placeline_place:>3}{q} {q}{placeline_sch_long:<25}{q} {q}{placeline_relay}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q} {q}{placeline_points:>2}{q}"
                        output_str = f" {q}{placeline_place:>3}{q} {q}{full_team_name:<25}{q} {q}{placeline_relay}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q} {points_str}"
                    output_list.append(( "PLACE", output_str ))

            #####################################################################################
            ## RESULTS: For results on relays and the swimmers name as well to the list
            ##          Its up to the output function to determine to display them or not
            #####################################################################################
            if event_num in sst_common.event_num_relay and re_results_check_relay_name_line.search(line):
                line = re_results_space_relay_name.sub( r'\1 \2',line )
                output_list.append(( "NAME", line ))  
                # crawler_str += gen_result_crawler_relay( placeline_place, placeline_sch_long, placeline_sch_short,placeline_relay, placeline_seedtime, placeline_finaltime, placeline_points )


    #####################################################################################
    ## Reached end of file
    ## Write out last event
    #####################################################################################
    create_output_file( output_dir, event_num, output_list, display_relay_swimmer_names, num_results_to_display, awards )
    num_files_generated += 1
    
    ## Save the last event in the crawler list 
    crawler_list.append( (event_num, crawler_str  ))
    
    ## Write out all crawler files now that processing of the result file has completed
    if generate_crawler:
        num_crawler_files_generated = create_output_file_results_crawler( output_dir, crawler_list, crawler_last_xx_results)

    #####################################################################################
    ## RESULTS: All done. Return counts of files created
    #####################################################################################
    return num_files_generated, num_crawler_files_generated



#####################################################################################
## Given an array of RESULTS lines PER EVENT, generate the output file for this event
## Wrapper function
#####################################################################################
def create_output_file( output_dir: str, 
                                event_num: int, 
                                output_list: list, 
                                display_relay_swimmer_names: bool,
                                num_results_to_display: int,
                                awards: bool  ) -> int:

    num_results_files_generated = 0
    num_awards_files_generated = 0
    ## Generate Standard results file
    num_awards_files_generated = \
        create_output_file_results( output_dir, 
                                    event_num, 
                                    output_list, 
                                    display_relay_swimmer_names,
                                    num_results_to_display ) 

    ## Generate Awards file
    if awards:
        num_results_files_generated = \
            create_output_file_awards(  output_dir, 
                                        event_num, 
                                        output_list, 
                                        True,
                                        3 ) 

    return num_results_files_generated + num_awards_files_generated


#####################################################################################
## Given an array of RESULTS lines PER EVENT, generate the output file for this event
#####################################################################################
def create_output_file_results( output_dir: str, 
                                event_num: int, 
                                output_list: list, 
                                display_relay_swimmer_names: bool,
                                num_results_to_display: int ) -> int:
    """ Generate the filename and open the next file """
    
    num_files_generated = 0
    num_results_generated = 0
    output_str = ""

    ## Ignore the case where we get event0 heat0
    if event_num == 0:
        return 0
    
    logging.info(f"RESULTS: e: {event_num} create_output_file_results")

    ## Loop through list in reverse order
    #for num in range( num_events-1, -1, -1):
    for output_tuple in output_list:
        row_type = output_tuple[0]
        row_text = output_tuple[1]

        logging.info(f"RESULTS: e: {event_num} id: {row_type} t: {row_text}")

        ## Save off the meet name, which somes at the end of the procesing as we are looping in reverse order
        if row_type == 'H4':
            output_str += row_text + '\n'
            #output_str += '\n'
        elif row_type == 'H6':
            output_str += g_unofficial_results + '\n'
            output_str += row_text + '\n'
        elif row_type == 'PLACE':
            output_str += row_text + '\n'
            num_results_generated += 1
        elif row_type == 'NAME' and display_relay_swimmer_names:
            output_str += row_text + '\n'

        if num_results_generated >= num_results_to_display:
            break;

    output_file_name =  f"{g_file_name_prefix}{event_num:0>2}_{g_file_name_suffix}.txt"
    sst_common.write_output_file( output_dir, output_file_name, output_str )
    num_files_generated += 1

    return num_files_generated

#####################################################################################
## Given an array of RESULTS lines PER EVENT, generate the output file for this event
## for AWARDS. Only top three and display relay names
#####################################################################################
def create_output_file_awards(  output_dir: str, 
                                event_num: int, 
                                output_list: list, 
                                display_relay_swimmer_names: bool,
                                num_results_to_display: int  ) -> int:
    """ Generate the filename and open the next file """
    
    num_files_generated = 0
    num_results_generated = 0
    output_str = ""

    ## Ignore the case where we get event0 heat0
    if event_num == 0:
        return 0
    
    logging.info(f"AWARDS: e: {event_num} create_output_file_awards")

    ## Loop through list in reverse order
    #for num in range( num_events-1, -1, -1):
    for output_tuple in output_list:
        row_type = output_tuple[0]
        row_text = output_tuple[1]

        logging.info(f"AWARDS: e: {event_num} id: {row_type} t: {row_text}")

        ## Save off the meet name, which somes at the end of the procesing as we are looping in reverse order
        if row_type == 'H4':
            output_str += row_text + '\n'
        elif row_type == 'H6':
            output_str += row_text + '\n'
        elif row_type == 'PLACE':
            ## Stop if we hit our top three winners, plus RELAY names
            if num_results_generated >= num_results_to_display:
                break;
            output_str += row_text + '\n'
            num_results_generated += 1
        elif row_type == 'NAME':
            output_str += row_text + '\n'


    output_file_name =  f"{g_file_name_prefix}{event_num:0>2}_{g_file_name_awards}.txt"
    sst_common.write_output_file( output_dir, output_file_name, output_str )
    num_files_generated += 1

    return num_files_generated
####################################################################################
## Given an array of PROGRAM lines PER HEAT, generate the crawler file for individuals
#####################################################################################
def gen_result_crawler_ind( place: str, 
                            name: str, 
                            grade: str,
                            school_short: str, 
                            school_long: str, 
                            seedtime: str, 
                            finaltime: str, 
                            points: str ) -> int:

    seperator_str = " | "
    crawler_sep = "" if place == "1" else seperator_str

    ## There are cases where special characters are added to place (i.e. * for ties)
    place = re.sub("[^\d\.]", "", place)
    ## Place may be a string represenatation of a int, or it could be --- for exhibition swimmers
    try:
        place_str = get_ordinal(int(place))
    except Exception as e:
        place_str = place

    school_name = school_short.strip()
    results_str = f"{crawler_sep}{place_str}: {name} {grade} {school_name} {finaltime}"

    return results_str


####################################################################################
## Given an array of PROGRAM lines PER HEAT, generate the crawler file for relays
####################################################################################
def gen_result_crawler_relay( place: str, 
                              sch_long: str, 
                              sch_short: str,
                              relay: str, 
                              seedtime: str, 
                              finaltime: str, 
                              points: str ) -> str:

    seperator_str = " | "
    crawler_sep = "" if place == "1" else seperator_str

    ## There are cases where special characters are added to place (i.e. * for ties)
    place = re.sub("[^\d\.]", "", place)
    place_str = get_ordinal(int(place))

    school_name = sch_short.strip()
    results_str = f"{crawler_sep}{place_str}: {school_name} {relay} {finaltime}"

    return results_str



#####################################################################################
## create_output_file_results_crawler
##
## Given a list of tuples (evnt num, crawler_string), generate output files
## Generate crawler files for actual events (event_num > 0) and for meet name (event_num = -2)
#####################################################################################
def create_output_file_results_crawler( output_dir_root: str, crawler_list: list, last_num_events: int ):
    """ Given a list of tuples (evnt num, crawler_string), generate output files """
    
    output_dir = f"{output_dir_root}/"
    num_files_generated=0


    ## Generate individual files per meet
    for crawler_event in crawler_list:
        event_num = crawler_event[0]
        crawler_text = crawler_event[1]

        logging.debug(f"crawler: e: {event_num} t: {crawler_text}")
        ## Generate event specific file
        if event_num > 0:
            #output_file_name = f"{g_crawler_name_prefix}_result_event{event_num:0>2}.txt"
            output_file_name = f"{g_crawler_name_prefix}_result_event{event_num:0>2}.txt"
            sst_common.write_output_file( output_dir, output_file_name, crawler_text )
            num_files_generated += 1
        ## Genreate special file for the meet name
        elif event_num == sst_common.headerNum2:
            output_file_name = f"{g_crawler_name_prefix}__MeetName.txt"
            sst_common.write_output_file( output_dir, output_file_name, crawler_text )
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
            if last_num_events_generated < last_num_events:
                crawler_text_last_num_events += f" | {event_text}"
                last_num_events_generated += 1
        elif event_num == sst_common.headerNum2:
            meet_name = event_text        

    ## Add meet_name to front of string
    crawler_text = f"{meet_name} {crawler_text}"
    ## Create the crawler file with ALL events completed so far
    all_events_file_name = f"{g_crawler_name_prefix}__AllEventsReverse.txt"
    output_file_name = all_events_file_name
    sst_common.write_output_file( output_dir, output_file_name, crawler_text )
    num_files_generated += 1

    ## Create the crawler file with last_num events
    #last_xx_events_file_name = f"{g_crawler_name_prefix}__Last_{last_num_events:0>2}_events.txt"
    last_xx_events_file_name = f"{g_crawler_name_prefix}__Last_XX_events.txt"
    output_file_name = last_xx_events_file_name
    sst_common.write_output_file( output_dir, output_file_name, crawler_text_last_num_events )
    num_files_generated += 1

    return num_files_generated


def get_ordinal( num: int) -> str:
    """ convert a number such as 3 to 3rd """

    if num == 1:
        num_str = f"{num}st"
    elif num == 2:
        num_str = f"{num}nd"
    elif num == 3:
        num_str = f"{num}rd"
    else:
        num_str = f"{num}th"
    
    return num_str


#####################################################################################
## generate_empty_results
##
## By creating empty files with the same name as the real files, allow wirecast
## templates to be preloaded prior to the meet so the wirecast operator does not
## have to search for a file just prior to display it
#####################################################################################

def generate_empty_results( output_dir:str, awards: bool ) -> int:

    output_str = ""

    num_empty_files_created = 0
    ## Allow for commenting out any type of event quickly during a meet
    empty_event_list = []
    empty_event_list += sst_common.event_num_individual
    empty_event_list += sst_common.event_num_relay   
    empty_event_list += sst_common.event_num_diving 

    suffix = g_file_name_suffix if awards g_file_name_awards

    for event_num in empty_event_list:
        output_file_name =  f"{g_file_name_prefix}{event_num:0>2}_{suffix}.txt"
        sst_common.write_output_file( output_dir, output_file_name, output_str )
        num_empty_files_created += 1

    return num_empty_files_created
