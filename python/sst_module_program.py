import logging
import re

import sst_module_common as sst_common

file_name_prefix = "event_"
file_name_suffix = "program"

#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
##########                                                                 ##########
##########    S S T _ M O D U L E _ P R O G R A M                          ##########
##########                                                                 ##########
##########    Code to generate Event entry files from the meet program     ##########
##########                                                                 ##########
##########                                                                 ##########
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################

####################################################################################
## Parse the report file and generate an output array
#####################################################################################

def process_program( meet_report_filename: str, 
                     output_dir: str, 
                     mm_license_name: str, 
                     shorten_school_names_relays: bool, 
                     shorten_school_names_individual: bool, 
                     split_relays_to_multiple_files: bool, 
                     add_new_line_to_relay_entries:bool, 
                     display_relay_swimmer_names: bool,
                     namesfirstlast: bool, 
                     quote_output: bool,
                     relayformat:int,
                     gen_overlay_files:bool ) -> int:
    """ Given the input file formatted in a specific manner,
        generate indiviual Event/Heat files for use in Wirecast displays """
    
    #####################################################################################
    ## The names are what appear in the report, and may be abbreviated, 
    ##  and not the actual full school name
    ## Multiple version of a school may be listed here for clean output
    #####################################################################################

    ## NOTE: Do not align up these headers with the TXT output.  
    ##  Wirecast will center all lines and it will be in proper position then

    program_header_len_dict = {
        'individual_long': 25,
        'diving_long': 25,
        'relay_long': 28,
    }

    program_header_dict = {
        'individual_long':   "\nLane  Name                    Year School      Seed Time",
        'individual_short':  "\n  Lane  Name                   Yr Sch  Seed Time",
        'diving_long':       "\nbLane  Name                 Year School      Seed Points",
        'diving_short':      "\n  Lane  Name                     Yr Sch  Seed Points",
        'relay_long':        "\nLane    Team                  Relay Seed Time" ,        
        'relay_short':       "\nLane  Team Relay Seed Time",    
    }

    ## Define local variables
    event_num = 0
    heat_num = 0
    num_files_generated = 0
    num_header_lines = 3
    found_header_line = 0
    output_list = []

    ## Define the regular expression to pase the meet program
    re_program_lane = re.compile('^[*]?\d{1,2} ')
    re_program_lane_ind = re.compile('^(\d{1,2})\s+([A-z\' \.]+, [A-z ]+?) ([A-Z0-9]{1,2})\s+([A-Z \'.].*)\s+([X]?[0-9:.]+|NT|XNT|NP|XNP)*')
    re_program_lane_relay = re.compile('^(\d{1,2})\s+([A-Z \'.].*)\s+([A-Z])\s+([X]?[0-9:.]+|NT|XNT)*')

    ## Remove the trailing hyphen (-) and -VA from school name
    re_program_sch_cleanup1 = re.compile(r'(.*?)-VA(\s*)$')
    re_program_sch_cleanup2 = re.compile(r'(.*?)-$(\s*)$')

    ## Search for case where team time butts up against seed time.  
    ## Need to add a space here so main regex works
    re_program_space_team_seed = re.compile(r'([A-z\-])(X\d)')

    ## For relays add a space between the persons name and next swimmer number
    re_program_space_relay_name = re.compile(r'(\S)([2-4]\))')
    re_program_check_relay_name_line = re.compile('1\)')
    
    ## Quote output for debugging
    q = "'" if quote_output else ""

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
                
                num_files = create_output_file_program( output_dir, event_num, heat_num, output_list, display_relay_swimmer_names, split_relays_to_multiple_files, relayformat, gen_overlay_files )
                
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
            ## PROGRAM: Start with Event line.  
            ##  Get the Event Number from the report
            ##  Clean it up
            #####################################################################################
            if line.lower().startswith(("event")):
                event_num, event_str = sst_common.get_event_num_from_eventline( line )
                ## H4 is the Event number/name line
                output_list.append(('H4', f"{line}" ))

            #####################################################################################
            ## PROGRAM: Remove "Timed Finals" from Heat (and flight) line
            #####################################################################################
            if line.lower().startswith(("heat", "flight")):
                line = line.replace("Timed Finals", "")
                ## Remove all those extra spaces in the line
                heat_num = sst_common.get_heat_num_from_heatline(line)

                ## H6 is the Heat info, save it in case we want to output it later
                output_list.append(('H5', f"{line}" ))

                #####################################################################################
                ## PROGRAM: Set name_list_header to be displayed above the list of swimmers
                ##          This is only set once per Event/Heat so moving this is probablimetic
                #####################################################################################
                # Determin heading based on short or full school name
                name_list_header = sst_common.get_header_line( event_num, shorten_school_names_relays, shorten_school_names_individual, program_header_dict ) 
                if name_list_header != "":
                    output_list.append(('H6', name_list_header))

            #####################################################################################
            ## PROGRAM: INDIVIDUAL Extract the individual Entry Line
            ## i.e. 2   Robison, Ryan            JR  Bishop O'Connell-PV      X2:22.35                        
            #####################################################################################
            if (event_num in sst_common.event_num_individual or event_num in sst_common.event_num_diving) and re_program_lane.search(line):
                ## Fix for case where School Name butts up to the X in seed time
                line = re_program_space_team_seed.sub(r'\1 \2', line )

                entry_line_list = re_program_lane_ind.findall(line)
                #                                  LANE     LAST, FIRST        GR          SCHOOL             SEEDTIME 
                if entry_line_list:
                    entry_lane            = str(entry_line_list[0][0]).strip()
                    entry_name_last_first = str(entry_line_list[0][1]).strip()
                    entry_grade           = str(entry_line_list[0][2]).strip()
                    entry_sch_long        = str(entry_line_list[0][3]).strip()
                    entry_seedtime        = str(entry_line_list[0][4]).strip()
                    
                    ## In case we want to use Shortened School Names, run the lookup
                    ## The length of the school name in the MM report varies by event type
                    school_name_len = program_header_len_dict['diving_long'] if event_num in sst_common.event_num_diving else program_header_len_dict['individual_long']
                    entry_sch_short = sst_common.short_school_name_lookup( entry_sch_long, school_name_len )

                    ## We can display name as given (Last, First) or change it to First Last with cli parameter
                    entry_name = sst_common.reverse_lastname_firstname( entry_name_last_first ) if namesfirstlast else entry_name_last_first

                    ## Still issues with School names ending in - or -VA
                    entry_sch_long = re_program_sch_cleanup1.sub(r'\1', entry_sch_long)
                    entry_sch_long = re_program_sch_cleanup2.sub(r'\1', entry_sch_long)

                    ## Format the output lines with either long (per meet program) or short school names
                    output_str = f" {q}{entry_lane:>2}{q} {q}{entry_name:<25}{q} {q}{entry_grade:>2}{q} {q}{entry_sch_long:<25}{q} {q}{entry_seedtime:>8}{q}"
                    
                    if shorten_school_names_individual:
                        output_str = f" {q}{entry_lane:>2}{q} {q}{entry_name:<25}{q} {q}{entry_grade:>2}{q} {q}{entry_sch_short:<4}{q} {q}{entry_seedtime:>8}{q}"
                    
                    output_list.append(('LANE', output_str))
                    
                    ## Prepare to generate a NAME ONLY (may contain lane#) for use on overlaying the lanes while swimmer in water
                    nameonly_str = f"{q}{entry_lane:>2}{q} {q}{entry_name:<25}{q}"
                    output_list.append(('NAMEONLY', nameonly_str))

            
            #####################################################################################
            ## PROGRAM: RELAY Find the replay line with LANE, SCHOOL, RELAY TEAM SEEDTIME
            ## 1 Seton Swim            A                    1:46.82      1:40.65        32
            #####################################################################################
            if event_num in sst_common.event_num_relay and re_program_lane.search(line):
                entry_line_list = re_program_lane_relay.findall(line)
                #  REGEX Positions                 LANE   SCHOOL    RELAY     SEEDTIME
                if entry_line_list:
                    entryline_lane      = str(entry_line_list[0][0]).strip()
                    entryline_sch_long  = str(entry_line_list[0][1]).strip()
                    entryline_relay     = str(entry_line_list[0][2]).strip()
                    entryline_seedtime  = str(entry_line_list[0][3]).strip()

                    #####################################################################################
                    ## PROGRAM: Replace long school name with short name for RELAY events
                    #####################################################################################
                    entryline_sch_short = sst_common.short_school_name_lookup( entryline_sch_long, len(entryline_sch_long) )
                    ## Still issues with School names ending in - or -VA
                    entryline_sch_long = re_program_sch_cleanup2.sub(r'\1', entryline_sch_long)
                    
                    full_team_name = entryline_sch_long
                    if shorten_school_names_relays:
                        full_team_name = entryline_sch_short
                        output_str = f"{q}{entryline_lane:>2}{q} {q}{entryline_sch_short:<4}{q} {q}{entryline_relay:1}{q} {q}{entryline_seedtime:>8}{q}"
                    else:
                        full_team_name = sst_common.find_proper_team_name( entryline_sch_long )
                        output_str = f"{q}{entryline_lane:>2}{q} {q}{full_team_name:<28}{q} {q}{entryline_relay:1}{q} {q}{entryline_seedtime:>8}{q}"

                    output_list.append(( "LANE", output_str ))
                    nameonly_str = f"{q}{entryline_lane:>2}{q} {q}{full_team_name:<25}{q}"
                    output_list.append(('NAMEONLY', nameonly_str))

            #####################################################################################
            ## PROGRAM: RELAY Add the swimmers name to the list. It may or may not be use for output
            #####################################################################################
            ## If this is a relay, add a space between the last swimmer name and the next swimmer number
            ## This line  1) LastName1, All2) LastName2, Ashley3) LastName3, All4) LastName4, Eri
            ## becomes    1) LastName1, All 2) LastName2, Ashley 3) LastName3, All 4) LastName4, Eri
            if event_num in sst_common.event_num_relay and re_program_check_relay_name_line.search(line):
                output_str = re_program_space_relay_name.sub( r'\1 \2',line )
                output_list.append(( "NAME", output_str ))

    #####################################################################################
    ## Reached end of file
    ## Write out last event
    #####################################################################################

    num_files = create_output_file_program( output_dir, event_num, heat_num, output_list, display_relay_swimmer_names, split_relays_to_multiple_files, relayformat, gen_overlay_files )
    num_files_generated += num_files

    #####################################################################################
    ## PROGRAM: All done. Return counts of files created
    #####################################################################################
    return num_files_generated


####################################################################################
## Determine type of output file to generate
#####################################################################################
def create_output_file_program( output_dir_root: str, 
                                event_num: int, 
                                heat_num: int,
                                output_list: list, 
                                display_relay_swimmer_names: bool,
                                split_relays_to_multiple_files: bool,
                                relayformat: int,
                                gen_overlay_files: bool ) -> int:

    num_files_created = 0
    overlay_files_created = 0
    if gen_overlay_files:
        overlay_files_created = create_output_file_program_nameonly(output_dir_root, 
                                                                    event_num, 
                                                                    heat_num,
                                                                    output_list, 
                                                                    display_relay_swimmer_names)

    ## Puts Short Team, Relay and swimmers on same line
    ##  6 SST  A 1) Garvey, L       2) Flynn, E        3) Condon, C       4) Pennefather, M 
    if event_num in sst_common.event_num_relay and relayformat == 2:
        num_files_created = create_output_file_program_format2( output_dir_root, 
                                event_num, 
                                heat_num,
                                output_list, 
                                display_relay_swimmer_names,
                                split_relays_to_multiple_files )


    else:
        ## Standard format for individual
        ## For relays, lists team name/relay/seed time and optional swimmers on second line (but usually requires splitting into two files)
        num_files_created = create_output_file_program_format1( output_dir_root, 
                                event_num, 
                                heat_num,
                                output_list, 
                                display_relay_swimmer_names,
                                split_relays_to_multiple_files )
    
    return num_files_created + overlay_files_created



####################################################################################
## Given an array of PROGRAM lines PER HEAT, generate the output file
#####################################################################################
def create_output_file_program_format1( output_dir_root: str, 
                                event_num: int, 
                                heat_num: int,
                                output_list: list, 
                                display_relay_swimmer_names: bool,
                                split_relays_to_multiple_files: bool ) -> int:
    """ Generate the filename and open the next file """
   
    global event_num_relay
    num_files_created = 0
    split_num = 1
    output_str = ""
    
    ## Ignore the case where we get event0 heat0
    if event_num == 0:
        return 0

    output_dir = f"{output_dir_root}/"
    
    ## For non relay events
    output_file_name = f"{file_name_prefix}{event_num:0>2}_{file_name_suffix}_heat_{heat_num:0>2}.txt"

    ## Count the number of lanes in the RELAY
    num_relay_lane = 0
    if event_num in sst_common.event_num_relay:
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

        logging.debug(f"PROGRAM: e: {event_num} h: {event_num} id: {row_type} t: {row_text}")

        ## Save off the meet name, which somes at the end of the procesing as we are looping in reverse order
        if row_type in header_list:
            output_str += row_text + '\n'
            header_str += row_text + '\n'
        elif row_type == 'LANE':
            output_str += row_text + '\n'
        elif row_type == 'NAME' and display_relay_swimmer_names:
            output_str += row_text + '\n'
            ## If split, space it out for readability
            if split_relays_to_multiple_files:
                output_str += '\n'

        ## If we have more then 6 relay entries create second output file, if requested to do so
        if split_relays_to_multiple_files and num_relay_lane > 7 and count == 5:
            count = -99
            output_file_name = f"{file_name_prefix}{event_num:0>2}_{file_name_suffix}_heat_{heat_num:0>2}_split{split_num:0>2}.txt"
            
            sst_common.write_output_file(output_dir, output_file_name, output_str)
            output_str = header_str
            ## Regenerate the header?  Need a better way to do this
            num_files_created += 1
            split_num += 1
            output_file_name = f"{file_name_prefix}{event_num:0>2}_{file_name_suffix}_heat_{heat_num:0>2}_split{split_num:0>2}.txt"

        if row_type == 'LANE':
            count += 1
    
    sst_common.write_output_file(output_dir, output_file_name, output_str)
    num_files_created += 1

    return num_files_created



####################################################################################
## Given an array of PROGRAM lines PER HEAT, generate the output file
## This version only contains NAME, not Headers, or swimminer info besides NAME
## Its used to test an overlay of names on the pool
#####################################################################################
def create_output_file_program_nameonly( output_dir_root: str, 
                                event_num: int, 
                                heat_num: int,
                                output_list: list, 
                                display_relay_swimmer_names: bool ) -> int:
    """ Generate the filename and open the next file """
   
    global event_num_relay
    num_files_created = 0
    split_num = 1
    output_str = ""
    
    ## Ignore the case where we get event0 heat0
    if event_num == 0:
        return 0

    output_dir = f"{output_dir_root}/"
    
    ## For non relay events
    output_file_name = f"{file_name_prefix}{event_num:0>2}_LANE_OVERLAY_heat_{heat_num:0>2}.txt"

    #header_list = ['H4', 'H5', 'H6']
    header_list = ['H4', 'H5']

    count =0 
    for output_tuple in output_list:
        row_type = output_tuple[0]
        row_text = output_tuple[1]

        logging.debug(f"NAMEONLY: e: {event_num} h: {event_num} id: {row_type} t: {row_text}")

        ## May want header info, if it fits on screen
        if row_type == 'H4':
            output_str += row_text + '\n'
        elif row_type == 'H5':
              output_str += row_text + '\n'+ '\n'
        elif row_type == 'NAMEONLY':
            output_str += row_text + '\n'

    sst_common.write_output_file(output_dir, output_file_name, output_str)
    num_files_created += 1

    return num_files_created


####################################################################################
## Given an array of PROGRAM lines PER HEAT, generate the output file
## For relays, put names on same line
##  1. SST  1) swimmer,one 2) swimmer, two 3) swimmer, three 4) swimmer, four
#####################################################################################
def create_output_file_program_format2( output_dir_root: str, 
                                event_num: int, 
                                heat_num: int,
                                output_list: list, 
                                display_relay_swimmer_names: bool,
                                split_relays_to_multiple_files: bool ) -> int:
    """ Generate the filename and open the next file """
   
    global event_num_relay
    num_files_created = 0
    split_num = 1
    output_str = ""
    lane_str = ""
    missing_name_for_this_lane = False

    ## Ignore the case where we get event0 heat0
    if event_num == 0:
        return 0

    output_dir = f"{output_dir_root}/"
    lane_str_without_names = ""
    ## For non relay events
    output_file_name = f"{file_name_prefix}{event_num:0>2}_{file_name_suffix}_heat_{heat_num:0>2}.txt"
    
    re_relay_lane_line = re.compile('^\s*(\d{1,2})\s+(\S+)\s+(\S)')

    #header_list = ['H4', 'H5', 'H6']
    header_list = ['H4', 'H5']
    for output_tuple in output_list:
        row_type = output_tuple[0]
        row_text = output_tuple[1]

        logging.debug(f"PROGRAM: e: {event_num} h: {event_num} id: {row_type} t: {row_text}")

        ## Save off the meet name, which somes at the end of the procesing as we are looping in reverse order
        #if row_type in header_list:
        if row_type == 'H4':
            output_str += f"{row_text.rjust(55)}" + '\n'
        elif row_type == 'H5':
            output_str += f"{row_text.rjust(45)}" + '\n'
        elif row_type == 'H6':
            output_str += '\n' + "  Ln Team     Swimmers" + '\n'
        elif row_type == 'LANE':
            ##
            ## If we have a second lane, but no name for the previous lane due 
            ## to no names being entered, write out lane/team info only
            if missing_name_for_this_lane:
               output_str += lane_str_without_names 
            
            missing_name_for_this_lane = True
            lane_str = row_text
            #  1 SST  D X2:37.00
            relay_lane_line = re_relay_lane_line.findall(row_text)
            if relay_lane_line:
                relay_lane = str(relay_lane_line[0][0]).strip()
                relay_sch  = str(relay_lane_line[0][1]).strip()
                relay_name = str(relay_lane_line[0][2]).strip()
                lane_str = f"{relay_lane:>4} {relay_sch:<4} {relay_name}"
                lane_str_without_names = f"{lane_str:<2}\n"

            #output_str += row_text + '\n'
        elif row_type == 'NAME':
            missing_name_for_this_lane = False

            name_str = reformat_relay_swimmers_names( row_text )
            #output_str += row_text + '\n'
            output_str += f"{lane_str:<2} {name_str:<68}\n"
            ## If split, space it out for readability
            if split_relays_to_multiple_files:
                output_str += '\n'

    
    logging.debug(f"RELAY: {output_str}")
    sst_common.write_output_file(output_dir, output_file_name, output_str)
    num_files_created += 1

    return num_files_created


## Parse out the last name and first name of the given string, given delimeter
def split_lastname_firstname_from_string(fullname: str, delim=','):
    lastname = fullname
    firstname = ""

    if delim in fullname:
        lastname, firstname = fullname.split(delim)

    return lastname, firstname

####################################################################################
## Given names in this format
#1) Herrick, Julia 2) Rutherford, Lil 3) Sypal, Clare 8 4) Vogler, Kate SO
# format them to look like
#1) Herrick, J 2) Rutherford, L 3) Sypal, C 4) Vogler, K

####################################################################################
def reformat_relay_swimmers_names( name_line_in:str ) -> str:

    new_name_str = name_line_in
    #re_name_line = re.compile('^1\)([A-z0-9\'\-, ]+?)2\)([A-z0-9\'\-, ]+?)3\)([A-z0-9\'\-, ]+?)4\)([A-z0-9\'\-, ]+?)$')

    ## WPD Ran into issue with a hyphenated name.  For now remove the hyphen
    ##name_line_in = name_line_in.replace('-',' ')
    ## WPD if last name too long, there may not be a command and a first name. Force a comma
    # if not ',' in name_line_in:
    #     name_line_in = f"{name_line_in},"

    re_name_line = re.compile('^1\)(.*?)2\)(.*?)3\)(.*?)4\)(.*?)$')
    re_program_space_relay_name = re.compile(r'(\S)([2-4]\))')

    ## Fix the swimmers named to put a space prior to the position number (i.e.  "NameFirst2)"" to "NameFirst 2)")
    name_line = re_program_space_relay_name.sub( r'\1 \2',name_line_in )
    re_name_list = re_name_line.findall(name_line)

    if re_name_list:
        s1_fullname = str(re_name_list[0][0]).strip()
        s2_fullname = str(re_name_list[0][1]).strip()
        s3_fullname = str(re_name_list[0][2]).strip()
        s4_fullname = str(re_name_list[0][3]).strip()
 
        ## Split name string "Last, First" into separate fields
        s1_lname, s1_fname = split_lastname_firstname_from_string( s1_fullname )
        s2_lname, s2_fname = split_lastname_firstname_from_string( s2_fullname )
        s3_lname, s3_fname = split_lastname_firstname_from_string( s3_fullname )
        s4_lname, s4_fname = split_lastname_firstname_from_string( s4_fullname )

        ## Remove extra whitespace
        s1_lname = s1_lname.strip()[:8]
        s1_fname = s1_fname.strip()
        s2_lname = s2_lname.strip()[:8]
        s2_fname = s2_fname.strip()
        s3_lname = s3_lname.strip()[:8]
        s3_fname = s3_fname.strip()
        s4_lname = s4_lname.strip()[:8]
        s4_fname = s4_fname.strip()

        ## Its possible last name is too long there is no first name
        s1_name = f"{s1_lname}, {s1_fname[0]}" if len(s1_fname) > 0 else f"{s1_lname}"
        s2_name = f"{s2_lname}, {s2_fname[0]}" if len(s2_fname) > 0 else f"{s2_lname}"
        s3_name = f"{s3_lname}, {s3_fname[0]}" if len(s3_fname) > 0 else f"{s3_lname}"
        s4_name = f"{s4_lname}, {s4_fname[0]}" if len(s4_fname) > 0 else f"{s4_lname}"

        new_name_str = f"1) {s1_name:<11} 2) {s2_name:<11} 3) {s3_name:<11} 4) {s4_name:<11}"
    return new_name_str