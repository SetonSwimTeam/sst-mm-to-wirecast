#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
########## 
##########    S S T _ M O D U L E _ C O M M O N
##########
##########    Common functions used by other SST modules
##########
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################

import os
from os import path
from datetime import datetime, timedelta
import logging
import unicodedata



event_num_individual = []
event_num_relay      = []
event_num_diving     = []


## Define the header types in the output list so we can include/exclude as necessary
headerNum1 = -1   ## HyTek licensee and HytTek software
headerNum2 = -2   ## Meet Name
headerNum3 = -3   ## Report type


#####################################################################################
## Text used for REGEX to convert long names to short names
## Some names are truncated. May be able to define full name and then define max
## lenght of school name depending on report
#####################################################################################
school_name_dict = { 
        "Benedictine College Prep": "BCP",
        "Bishop O'Connell-PV": "DJO",
        "Bishop O'Connell": "DJO",
        "Bishop Ireton Swim and Dive": "BI",
        "Bishop Sullivan Catholic High": "BSCHS",
        "BBVST": "BVST",
        "Brookewood School-PV": "BW",
        "Broadwater Academy-VA": "BVST",
        "Cape Henry Collegiate": "CHC",
        "Carmel School Wildcats": "WILD",
        "CCS-VA": "CCS",
        "Chatham Hall": "CH",
        "Christchurch School Swim Team": "CCS",
        "Collegiate School": "COOL",
        "Fredericksburg Academy-VA": "FAST",
        "Fredericksburg Christian-": "FCS",
        "Fresta Valley Christian S": "FVCS",
        "Fresta Valley Christian": "FVCS",
        "Hampton Roads Academy": "HRA",
        "Highland Hawks": "HL",
        "Immanuel Christian High S": "ICHS",
        "Middleburg Academy-VA": "MA",
        "Nansemond Suffolk Academy": "NSA",
        "Oakcrest School Chargers": "OAK",
        "Peninsula Catholic High S": "PCHS",
        "Randolph-Macon Academy-VA": "RMA",
        "Randolph-Macon Academy": "RMA",
        "Saint John Paul the Great": "JP",
        "St. Gertrude High School": "SGHS",
        "St. Paul VI Catholic HS": "PVI",
        "St. Paul VI High School": "PVI",
        "St. Paul VI High Schoo": "PVI",
        "Seton Alumni": "SALUM",
        "SST  Alumni": "SALUM",
        "Seton Swimming": "SST", 
        "The Heights": "HTS",
        "The Covenant School-VA": "TCS",
        "The Steward School-VA": "TSS",
        "The Steward School Sparta": "TSS",
        "Trinity Christian School-": "TCS!",
        "Trinity Christian School": "TCS!",
        "Veritas Collegiate Academy-VA": "VCA",
        "Veritas Collegiate Academ": "VCA",
        "Veritas School-VA": "VRTS",
        "Walsingham Academy-VA": "WA",
        "Wakefield H2owls-VA": "WAKE",
        "H2owls-VA": "WAKE",
        "Williamsburg Christian Ac": "WCA",
        "Woodberry Forest-VA": "WFS",
        "Valley Christian School": "VCS",
        "Valley Christian S": "VCS",
        "Seton Family Homeschool": "SFH",
    } 


#####################################################################################
## Proper Schhol Names
## Replace the team name from Meet Manager, which is often truncated, with this name
#####################################################################################
proper_school_name_dict = { 
        "Benedictine College Prep": "Benedictine College Prep",
        "Bishop O'Connell-PV": "Bishop O'Connell",
        "Bishop O'Connell": "Bishop O'Connell",
        "Bishop Ireton Swim and Dive": "Bishop Ireton",
        "Bishop Sullivan Catholic High": "Bishop Sullivan Catholic High",
        "BBVST": "BVST",
        "Broadwater Academy-VA": "Broadwater Academy",
        "Brookewood School-PV": "Brookewood",
        "BW   School-PV": "Brookewood",
        "Cape Henry Collegiate": "Cape Henry Collegiate",
        "Carmel School Wildcats": "Carmel School Wildcats",
        "CCS-VA": "CCS",
        "Chatham Hall": "Chatham Hall",
        "Christchurch School Swim Team": "Christchurch School",
        "Collegiate School": "Collegiate School",
        "Fredericksburg Academy-VA": "Fredericksburg Academy",
        "Fredericksburg Christian-": "Fredericksburg Christian",
        "Fresta Valley Christian": "Fresta Valley Christian",
        "Hampton Roads Academy": "Hampton Roads Academy",
        "Highland Hawks": "Highland Hawks",
        "Immanuel Christian High S": "Immanuel Christian",
        "Middleburg Academy-VA": "Middleburg Academy",
        "Nansemond Suffolk Academy": "Nansemond Suffolk Academy",
        "Oakcrest School Chargers": "Oakcrest School Chargers",
        "Peninsula Catholic High S": "Peninsula Catholic",
        "Randolph-Macon Academy-VA": "Randolph-Macon Academy",
        "Saint John Paul the Great": "Saint John Paul the Great",
        "St. Gertrude High School": "St. Gertrude High School",
        "St. Paul VI Catholic HS": "St. Paul VI Catholic HS",
        "St. Paul VI High Schoo": "St. Paul VI Catholic HS",
        "Seton Alumni Swimming": "Seton Alumni",
        "Seton Swimming": "Seton", 
        "The Covenant School-VA": "The Covenant School" ,
        "The Heights": "The Heights" ,
        "The Steward School-VA": "The Steward School",
        "The Steward School Sparta": "The Steward School",
        "Trinity Christian School-": "Trinity Christian School",
        "Trinity Christian School": "Trinity Christian School",
        "Veritas Collegiate Academ": "VCA",
        "Veritas School-VA": "VRTS",
        "Walsingham Academy-VA": "WA",
        "Wakefield H2owls-VA": "WAKE",
        "H2owls-VA": "WAKE",
        "Williamsburg Christian Ac": "Williamsburg Christian",
        "Woodberry Forest-VA": "Woodberry Forest",
        "Valley Christian School": "VCS",
        "Valley Christian S": "VCS",
        "Seton Family Homeschool": "Seton Family Homeschool",
    } 


def setEvents( meet_type: str ) -> bool:
    global event_num_individual
    global event_num_relay
    global event_num_diving

    success = True

    if meet_type == "SetonTimeTrials":
        # Seton time trial events
        event_num_individual = [1,2,3,4,5,6,7,8,9,10,11,12]
        event_num_relay      = []
        event_num_diving     = []
    elif meet_type == "HighSchool":
        # Standard High School Meet order of events (Dual Meet and Championship)
        event_num_individual = [3,4,5,6,7,8,11,12,13,14,15,16,19,20,21,22]
        event_num_relay      = [1,2,17,18,23,24]
        event_num_diving     = [9,10]
    elif meet_type == "JV":
        ## JV Invite Order of EVENTS
        event_num_individual = [3,4,5,6,9,10,11,12,15,16,17,18]
        event_num_relay      = [1,2,7,8,13,14,19,20]
        event_num_diving     = []
    else:
        success = False
        logging.error(f"Unknow Meet  Type: {meet_type}")

    return success

#####################################################################################
## Some school names have -VA added to end.  Since MM often truncated the name
## around between 24 and 27 chars (difference reports), we sometimes truncate
## the school name.  Remove the training -VA, -V or -
#####################################################################################
def clean_up_team_name( team_name_in: str) -> str:

    team_name_split = team_name_in.split('-')
    team_name_out = team_name_split[0]
    return team_name_out

#####################################################################################
## MM generatee a truncated team name.  See if we can find the full long name
#####################################################################################
def find_proper_team_name( team_name_in: str ):
    team_name_out = team_name_in

    ## Input may be a truncated version of the school name
    ## Search for a substring
    proper_name = ""
    for team_name in proper_school_name_dict:
        team_name_in_strip = team_name_in.strip()
        if team_name_in_strip.strip() in team_name:
            proper_name = f"{proper_school_name_dict[team_name]:<25}"
            break;

    logging.debug(f"Proper Name i:' {team_name_in}' o: '{proper_name}'")
    return proper_name 

#####################################################################################
## In some wierd cases, we overwrite a good file with some extra text that 
## wrapped to next page.  If a file was just created, and we try to write over it
## again too soon, create it as a second file too soon.
## If file was there from previous run, then we want to overwrite
#####################################################################################
def has_file_been_modified_recently( file_name: str, secs: int) -> bool:
    "Has file been modified in last xxx seconds"

    modified_recently = False
    try:
        file_mod_time = datetime.fromtimestamp(os.stat(file_name).st_mtime)
        
        now = datetime.today()
        file_modified_secs_ago = now - file_mod_time
        max_age = timedelta(seconds=secs)

        if file_modified_secs_ago <= max_age:
            modified_recently = True
        
    except FileNotFoundError as fnfe:
        # Ignore case where file doesn't yet exist
        pass


    return  modified_recently


#####################################################################################
## Write the actual output file from the generated string
#####################################################################################
def write_output_file( output_dir: str, output_file_name: str, output_str: str ):
    """ generate the actual crawler output file """
    
    ## Create output dir if not exists
    if not os.path.exists( output_dir ):
        os.makedirs( output_dir )
    
    ## If this file has been created in last xx secs, then this is really results data
    ## from the next page. Don't overwrite existing file
    output_full_path = f"{output_dir}{output_file_name}"
    if not has_file_been_modified_recently( output_full_path, 5 ):
        logging.info(f"generating file {output_full_path}")
        output_file_handler = open( output_full_path, "w+" )
        output_file_handler.write( output_str )
        output_file_handler.close()


def get_event_num_from_eventline( line: str ) -> int:
    """ Extract the event number from the event line """

    ## Remove all those extra spaces in the event line
    clean_event_str = line.split()
    clean_event_str = " ".join(clean_event_str)
    event_str = clean_event_str.split(' ', 4)
    event_num = int(event_str[1].strip())
    event_name = ""
    for i in range(2,5):
        event_name += event_str[i].strip() + " "

    return event_num, event_name


def get_heat_num_from_heatline( line: str ) -> int:
    """ Extract the heat number from heat/flight line """
    split_heat_str = line.split()
    split_heat_str = " ".join(split_heat_str)
    split_heat_str = split_heat_str.split(' ', 4)
    heat_num = int(split_heat_str[1])

    return heat_num

#####################################################################################
## The header line is for the list of swimmers/winners.
## Determine which header string to return
#####################################################################################
def get_header_line( event_num: int, shorten_school_names_relays: bool, shorten_school_names_individual: bool, header_dict: dict ) -> str:
    """ Return the proper header list for the report type """

    name_list_header = ""
    if event_num in event_num_individual:
        name_list_header = header_dict['individual_short'] if shorten_school_names_individual else header_dict['individual_long']   
    elif event_num in event_num_diving:
        name_list_header = header_dict['diving_short'] if shorten_school_names_individual else header_dict['diving_long']
    elif event_num in event_num_relay:
        name_list_header = header_dict['relay_short'] if shorten_school_names_relays else header_dict['relay_long']

    return name_list_header




def short_school_name_lookup( long_school_name: str, long_school_name_len: int, trunc_len :int = 0 ) -> str:
    "Given a long school name, search for a shorter school name.  If not found, return the long school name"
    
    school_name_dict_short_name_len  = 4
    short_school_name = long_school_name

    ## Handle some strange error conditions
    if long_school_name_len == 0:
        return short_school_name

    ## If not set, defaiult tuncate_len to full len
    if trunc_len == 0:
        trunc_len = long_school_name_len

    for k,v in school_name_dict.items():
        kstr = k[:long_school_name_len][:trunc_len]
        #logging.debug(f"Sch: s: '{long_school_name}' '{kstr}' len: {long_school_name_len} trunc: {trunc_len}")
        short_school_name = short_school_name.replace(k[:long_school_name_len][:trunc_len], v.ljust(school_name_dict_short_name_len, ' '))
        if short_school_name != long_school_name:
            #logging.debug(f"Sch: match: {short_school_name}")
            break
    return short_school_name




def reverse_lastname_firstname( name_last_first ):
    """ Convert the string "lastnane, firstname" to "firstname lastname" """

    name_last, name_first = name_last_first.split(',', 1)
    name_first = name_first.strip()
    name_last  = name_last.strip()
    name_first_last = f"{name_first} {name_last}"

    return name_first_last


def cleanup_new_files( file_prefix: str, output_dir: str ):
    """ Remove the one or many blank lines at end of the file """

    txtfiles = []
    file_glob = f"{output_dir}{file_prefix}*.txt"
    for file in glob.glob(file_glob):
        txtfiles.append(file)
    
    # for file in txtfiles:
    #     print(f"Filename: {file}")


#####################################################################################
## Verify the input file exists before opening it to determine the file type
#####################################################################################
def verify_dirs_files(  input_dir: str, input_file:str, output_dir: str ):

    ## Check input directory exists
    error_msg = ""
    if not os.path.isdir( input_dir ):
        error_msg = f"\tInput directory not found: {input_dir}"
    else:
        fullFile = f"{input_dir}/{input_file}"
        if not os.path.isfile( fullFile ):
            error_msg = f"\tInput file not found: {fullFile}"

    try: 
        if not os.path.isdir( output_dir ):
            os.makedirs(output_dir, exist_ok = True) 
            logging.warning(f"Output Directory '{output_dir}' created successfully") 
    except OSError as error: 
        logging.error(f"Output Directory '{output_dir}' can not be created: {error}" ) 

    return error_msg
 

#####################################################################################
## Remove characters such as Céilí 
#####################################################################################
def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])