import logging
import re
import sst_module_common as sst_common
import datetime

g_unofficial_results = "    ** UNOFFICIAL RESULTS **"

## Define file names for output files
g_file_name_prefix = "event_"
g_file_name_suffix = "RESULTS"
g_file_name_awards = "AWARDS"
g_crawler_name_prefix = "x_crawler_results"

#####################################################################################
### If we can display colors on wirecast
### this will define our color pallet
#####################################################################################
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ANSI_RESET = "\u001B[0m";
    ANSI_BLACK = "\u001B[30m";
    ANSI_RED = "\u001B[31m";
    ANSI_GREEN = "\u001B[32m";
    ANSI_YELLOW = "\u001B[33m";
    ANSI_BLUE = "\u001B[34m";
    ANSI_PURPLE = "\u001B[35m";
    ANSI_CYAN = "\u001B[36m";
    ANSI_WHITE = "\u001B[37m";


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
                    awards:bool,
                    awardsRelayNames: bool ) -> int:
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
        'individual_long':   "Name                    Yr School               Final Time     Change      Points",
        'individual_short':  "        Name                 School Yr   Final   Change   Pts",
        'diving_long':       "Name                    Yr School                           Finals Score      Points",
        'diving_short':      "        Name                 School Yr  Final    Change  Pts",
        'relay_long':         "           Team               Relay  Final   Change  Pts",        
        'relay_short':       "   Team Relay Final    Change   Pts",    
    }
    # result_header_dict = {
    #     'individual_long':   "Name                    Yr School                 Seed Time  Finals Time            ",
    #     'individual_short':  "        Name                  Sch  Yr    Seed    Finals      ",
    #     'diving_long':       "Name                    Yr School                           Finals Score           ",
    #     'diving_short':      "        Name                 School Yr   Seed     Final     ",
    #     'relay_long':         "           Team                  Relay  Seed   Finals     ",        
    #     'relay_short':       "   Team       Relay Seed Time  Finals Time       ",    
    # }
    result_header_dict = {
        'individual_long':   "Name                    Yr School                 Finals Time   Change   ",
        'individual_short':  "        Name                  Sch  Yr   Time    Change    ",
        'diving_long':       "Name                    Yr School                         Time Score      ",
        'diving_short':      "        Name                 School Yr      Final     ",
        'relay_long':         "           Team              Relay  Time    Change  ",        
        'relay_short':       "   Team       Relay Seed Time  Finals Time  Change",    
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
    continue_processing_current_event = True

    # re_results_lane = re.compile('^[*]?\d{1,2} ')
    # re_results_lane = re.compile('^--- ')
    re_results_lane = re.compile('^([*]?\d{1,2} )|(--- )')


    # #                                 TIE? PLACE       LAST          FIRST     GR           SCHOOL           SEEDTIME|NT|NP    [xX]FINALTIME      POINTS
    #re_results_lane_ind  = re.compile('^([*]?\d{1,2})\s+([A-z\' \.]+, [A-z ]+?) ([A-Z0-9]{1,2})\s+([A-Z \'.].*?)([0-9:.]+|NT)\s+([0-9:.]+)\s*([X]?[0-9]*)')
    #re_results_lane_ind  = re.compile('^([*]?\d{1,2}|---)\s+([A-z\' \.]+, [A-z ]+?) ([A-Z0-9]{1,2})\s+([A-Z \'.].*?)([0-9:.]+|NT|NP)\s+([X]DQ|[xX0-9:.]+)\s*([0-9]*)')
    #re_results_lane_ind  = re.compile('^([*]?\d{1,2}|---)\s+([A-z\' \.]{4,25}) ([A-Z0-9]{1,2})\s+([A-Z \'.].*?)([0-9:.]+|NT|NP)\s+([X]DQ|[xX0-9:.]+)\s*([0-9]*)')
    
    #12 Salter, Jonathan        FR Immanuel Christian High S  25.55        24.85         1
    #re_results_lane_ind  = re.compile('^([*]?\d{1,2}|---)\s+([A-z\' \.]+, [A-z ]+) ([A-Z0-9]{1,2})\s+([A-Z \'.].*?)([0-9:.]+|NT|NP)\s+([X]DQ|[xX0-9:.]+)\s*([0-9]*)')
    re_results_lane_ind  = re.compile('^([*]?\s*\d{1,2}|---)\s+(.{23})\s*([A-Z0-9 ]{1,2})\s*([A-z\- ]{25})\s*([0-9:.]+|NT|NP)\s+([X]DQ|[xX0-9:.]+)\s*([0-9]*)')
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
        for in_line in meet_report_file:

            line = sst_common.remove_accents( in_line) 

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
                if continue_processing_current_event:
                    num_files = create_output_file( output_dir, event_num, output_list, display_relay_swimmer_names, num_results_to_display, awards, awardsRelayNames )
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
                continue_processing_current_event = True

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
                continue_processing_current_event = False

                num_files = create_output_file( output_dir, event_num, output_list, display_relay_swimmer_names, num_results_to_display, awards, awardsRelayNames )
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
                    placeline_school_raw= str(place_line_list[0][3]).strip()
                    placeline_seedtime    = str(place_line_list[0][4]).strip()
                    placeline_finaltime   = str(place_line_list[0][5]).strip()
                    placeline_points      = str(place_line_list[0][6]).strip()        

                    if placeline_points == "":
                        placeline_points = "-"

                    ## Wierd case where a DQ results has part of finaltime in points column
                    if 'DQ' in placeline_finaltime:
                        placeline_points = "-"

                    ## Get formatted string of positive/negative chanage in tie
                    if event_num in sst_common.event_num_individual:
                        changeInTime = computeSeedFinalTimeDiff( placeline_seedtime, placeline_finaltime )
                    elif event_num in sst_common.event_num_diving:
                        changeInTime = computeDivingSeedFinalTimeDiff( placeline_seedtime, placeline_finaltime )
                    else:
                        changeInTime = "------"

                    logging.debug(f"RESULTS: place {placeline_place}: name {placeline_name_last_first}: grade {placeline_grade}: sch {placeline_school_raw}: seed {placeline_seedtime}: final {placeline_finaltime}: points {placeline_points}:")
                    ## If we want to use Shortened School Names, run the lookup
                    ## The length of the school name in the MM report varies by event type
                    school_name_len = result_header_len_dict['individual_long']  if event_num in sst_common.event_num_individual else result_header_len_dict['diving_long']
                    ## Normalize the long school name to clean it up to the "short full name" we want to display
                    placeline_school_long =  sst_common.short_school_name_lookup(placeline_school_raw, school_name_len)
                    placeline_school_short = sst_common.short_school_abbr_lookup( placeline_school_raw, school_name_len )

                    ## We can display name as given (Last, First) or change it to First Last with cli parameter
                    result_name = sst_common.reverse_lastname_firstname( placeline_name_last_first ) if namesfirstlast else placeline_name_last_first

                    ## Format the output lines with either long (per meet program) or short school names
                    # with points
                    
                    #full_team_name = placeline_school_long
                    full_team_name = sst_common.find_proper_team_name( placeline_school_long )

                    # output_str = f"{q}{placeline_place:>3}{q} {q}{result_name:<25}{q} {q}{placeline_grade:>2}{q} {q}{placeline_school_long:<25}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q} {q}{placeline_points:>2}{q}"

                    points_str = f"{q}{placeline_points:>4}{q}" if champsionship_result_header_dict else ""
                    #output_str = f"{q}{placeline_place:>3}{q} {q}{result_name:<25}{q} {q}{placeline_grade:>2}{q} {q}{full_team_name:<25}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q} {points_str}"
                    #output_str = f"{q}{placeline_place:>3}{q} {q}{result_name:<25}{q} {q}{placeline_grade:>2}{q} {q}{full_team_name:<25}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q} {q}{changeInTime:>8}{q} {points_str}" 
                    output_str = f"{q}{placeline_place:>3}{q} {q}{result_name:<25}{q} {q}{placeline_grade:>2}{q} {q}{full_team_name:<25}{q} {q}{placeline_finaltime:>8}{q} {q}{changeInTime:>8}{q} {points_str}" 
                    
                    if shorten_school_names_individual:
                        #output_str = f"{q}{placeline_place:>3}{q} {q}{result_name:<25}{q} {q}{placeline_school_short:<4}{q} {q}{placeline_grade:>2}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q} {q}{placeline_points:>2}{q}"
                        #output_str = f"{q}{placeline_place:>3}{q} {q}{result_name:<25}{q} {q}{placeline_school_short:<4}{q} {q}{placeline_grade:>2}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q}{points_str}"
                        #output_str = f"{q}{placeline_place:>3}{q} {q}{result_name:<25}{q} {q}{placeline_school_short:<4}{q} {q}{placeline_grade:>2}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q} {q}{changeInTime:>8}{q} {points_str}"
                        output_str = f"{q}{placeline_place:>3}{q} {q}{result_name:<25}{q} {q}{placeline_school_short:<4}{q} {q}{placeline_grade:>2}{q} {q}{placeline_finaltime:>8}{q} {q}{changeInTime:>8}{q} {points_str}"
                    
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

                    if placeline_points == "":
                        placeline_points = "-"
                    if 'DQ' in placeline_finaltime:
                        placeline_points = "-"

                    ## Get formatted string of positive/negative chanage in tie
                    changeInTime = computeSeedFinalTimeDiff( placeline_seedtime, placeline_finaltime )

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
                        #output_str = f" {q}{placeline_place:>3}{q} {q}{placeline_sch_short:<4}{q} {q}{placeline_relay}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q} {points_str}"
                        output_str = f" {q}{placeline_place:>3}{q} {q}{placeline_sch_short:<4}{q} {q}{placeline_relay}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q} {q}{changeInTime:>8}{q} {points_str}"
                        #output_str = f" {q}{placeline_place:>3}{q} {q}{placeline_sch_short:<4}{q} {q}{placeline_relay}{q} {q}{placeline_finaltime:>8}{q} {q}{changeInTime:>8}{q} {points_str}"
                    else:
                        #full_team_name = placeline_sch_long
                        full_team_name = sst_common.find_proper_team_name( placeline_sch_long )

                        #output_str = f" {q}{placeline_place:>3}{q} {q}{placeline_sch_long:<25}{q} {q}{placeline_relay}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q} {q}{placeline_points:>2}{q}"
                        #output_str = f" {q}{placeline_place:>3}{q} {q}{full_team_name:<25}{q} {q}{placeline_relay}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q} {points_str}"
                        #output_str = f" {q}{placeline_place:>3}{q} {q}{full_team_name:<25}{q} {q}{placeline_relay}{q} {q}{placeline_seedtime:>8}{q} {q}{placeline_finaltime:>8}{q} {q}{changeInTime:>8}{q} {points_str}"
                        output_str = f" {q}{placeline_place:>3}{q} {q}{full_team_name:<25}{q} {q}{placeline_relay}{q} {q}{placeline_finaltime:>8}{q} {q}{changeInTime:>8}{q} {points_str}"
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
    create_output_file( output_dir, event_num, output_list, display_relay_swimmer_names, num_results_to_display, awards, awardsRelayNames )
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
                                awards: bool,
                                awardsRelayNames: bool  ) -> int:

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
                                        awardsRelayNames,
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

    re_results_header = re.compile('^(.*) (Pts|Points)$')

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
            ## Awards are top justified. Start text below logo
            # output_str += '\n' + '\n'
            output_str += row_text + '\n'
        elif row_type == 'H6':
            place_header_list = re_results_header.findall(row_text)
            if place_header_list:
                placeline_header   = str(place_header_list[0][0]).strip()
                output_str += placeline_header + '\n'
            else:
                output_str += row_text + '\n'

        elif row_type == 'PLACE':


            ## Ignore non-scoring entries (i.e. only two non-exhibition relays in event)
            if row_text.startswith(" --- "):
                break;
            ## Stop if we hit our top three winners, plus RELAY names
            if num_results_generated >= num_results_to_display:
                break;

            ## Lets try to remvoe the POINTS of the PLACE since its always the first XX place winners
            re_results_place = re.compile('^(.*) (\d){1,2}$')
            place_line_list = re_results_place.findall(row_text)

            if place_line_list:
                placeline_place   = str(place_line_list[0][0]).strip()
                placeline_points  = str(place_line_list[0][1]).strip()
                logging.error(f"PLACE: 1: {placeline_place} 2: {placeline_points}")
                output_str += placeline_place + '\n'
            else:
                output_str += row_text + '\n'
            num_results_generated += 1
       # elif row_type == 'NAME':
       #     output_str += row_text + '\n'
        elif row_type == 'NAME' and display_relay_swimmer_names:
            output_str += row_text + '\n'

    ## One more blank line to keep last line off bottom of screen
    output_str += '\n'
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

    suffix = g_file_name_awards if awards else g_file_name_suffix

    for event_num in empty_event_list:
        output_file_name =  f"{g_file_name_prefix}{event_num:0>2}_{suffix}.txt"
        sst_common.write_output_file( output_dir, output_file_name, output_str )
        num_empty_files_created += 1

    return num_empty_files_created


#####################################################################################
## convertSwimTimeToSecs
##
## Convert a swim time in string format to a python datetime object.
## Valid formats are:
## m:ss.hs  -- minute:seconds:hundreths_secs
## ss.hs    -- seconds:hundreths_secs
##
## Exhibition (x) indicators are removed
##
## Other possible strings are ignored, such as:
##  DQ, NT, NP, DNF
#####################################################################################
def convertSwimTimeToSecs( swimTimeStr: str ):
    ## We can have either SS.hh or MM:SS.hh
    swimTimeFormat = "%S.%f"
    if ":" in swimTimeStr:
        swimTimeFormat = "%M:%S.%f"

    ## See if we can convert this string to a date, if its in proper format
    ## Otherwise return None
    try:
        date_time_obj = datetime.datetime.strptime( swimTimeStr, swimTimeFormat )
        return date_time_obj
    except Exception as e:
        ## Not a proper date format
        return None

#####################################################################################
## computeSeedFinalTimeDiff
##
## Given a SEED time and FINALS time in string format see if we can
## determine the change in time.
## a negative number is an improvement in time (faster time)
## a positive number is an slower time
#####################################################################################
def computeSeedFinalTimeDiff( seedTimeStr: str, finalTimeStr: str):
    ## Remove xX for exhibition times
    if 'X' in finalTimeStr:
        finalTimeStr = finalTimeStr.replace('X','')
    if 'x' in finalTimeStr:
        finalTimeStr = finalTimeStr.replace('x','')

    ## Convert dateformat in string format to datetime object
    seedTimeDate = convertSwimTimeToSecs( seedTimeStr )
    finalTimeDate = convertSwimTimeToSecs( finalTimeStr )

    ## If both times are valid dates, continue.
    seedTimeMS = 0
    total_min = 0
    changeTimeColorBegin = ""
    changeTimeColorEnd = ""
    plusMinusStr = ""
    adjusted_seconds = 0
    if not (seedTimeDate == None or finalTimeDate == None):
        ## Add a + or - sign for increse/decrease in time
        if seedTimeDate > finalTimeDate:
            timeDiff = seedTimeDate - finalTimeDate
            plusMinusStr = "-"
            #changeTimeColorBegin = bcolors.ANSI_GREEN
            #changeTimeColorEnd =  bcolors.ANSI_RESET
        else:
            timeDiff = finalTimeDate - seedTimeDate
            plusMinusStr = "+"
            #changeTimeColorBegin =  bcolors.ANSI_RED
            #changeTimeColorEnd =  bcolors.ANSI_RESET


        ## is seed time a coaches entered time?
        ## If seemdTimeMS == 00, then don't display change/improvement and assume its coaches time
        seedTimeMS = seedTimeDate.microsecond

        # total_secs includes hundreths
        total_secs = timeDiff.total_seconds()

        ## Convert 130 seconds to 2 minutes 10 seconds
        ## Converts seconds to minutes (then subtract those seconds)
        total_min = (total_secs//60)%60
        adjusted_seconds = round(total_secs - (total_min*60),2)

    ## if seedTimeMS == 0 then we assume this is a coaches time and don't display a change/improvement
    ## WPD. Not liking the output of not display MS=0. Ignore for now, but leaving IF in place for easy revert back
    if seedTimeMS >= 0:
        if total_min > 0:
            returnStr =  f"{changeTimeColorBegin}{plusMinusStr}{total_min:.0f}:{adjusted_seconds:05.2f}{changeTimeColorEnd}"
            #print(f"totalsecs: {seedTimeStr} -> {finalTimeStr} = {plusMinusStr}{total_secs}:  {plusMinusStr}{total_min:.0f}:{adjusted_seconds:05.2f}")
        else:
            returnStr =  f"{changeTimeColorBegin}{plusMinusStr}{adjusted_seconds:05.2f}{changeTimeColorEnd}"
            #print(f"totalsecs: {seedTimeStr} -> {finalTimeStr} = {plusMinusStr}{total_secs}:  {plusMinusStr}{adjusted_seconds:05.2f}")
    else:
        returnStr =  f"------"
        #print(f"totalsecs: {seedTimeStr} -> {finalTimeStr} = -----")
    
    logging.debug(f"computeSeedFinalTimeDiff: st: {seedTimeMS} s: '{seedTimeStr}'' f: '{finalTimeStr}'' o: {returnStr}")
    return returnStr 

#####################################################################################
## computeDivingSeedFinalTimeDiff
##
## Given a SEED time and FINALS time in string format see if we can
## determine the change in time.
## a negative number is an improvement in time (faster time)
## a positive number is an slower time
#####################################################################################
def computeDivingSeedFinalTimeDiff( seedTimeStr: str, finalTimeStr: str):
    returnStr =  f"------"
    plusMinusStr = ""

    ## Remove xX for exhibition times
    if 'X' in finalTimeStr:
        finalTimeStr = finalTimeStr.replace('X','')
    if 'x' in finalTimeStr:
        finalTimeStr = finalTimeStr.replace('x','')

    try:
        # converting to integer
        seedTime = float(seedTimeStr)
        finalTime = float(finalTimeStr)
        changeInTime = finalTime - seedTime
        if changeInTime > 0:
            plusMinusStr = "+"
            returnStr = f"{plusMinusStr}{changeInTime:05.2f}"
        else:
            returnStr = f"{changeInTime:06.2f}"

    except ValueError:
        logging.info(f"computeDivingSeedFinalTimeDiff: Not a valid number: ST:{seedTimeStr} FT: {finalTimeStr}")


    return returnStr