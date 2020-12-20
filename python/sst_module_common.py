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
## Define the types of events in this meet (Individual, Relay and Diving)
event_num_individual = [3,4,5,6,7,8,11,12,13,14,15,16,19,20,21,22]
event_num_relay  = [1,2,17,18,23,24]
event_num_diving = [9,10]



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
        "Immanuel Christian High S": "ICHS",
        "Middleburg Academy-VA": "MA",
        "Nansemond Suffolk Academy": "NSA",
        "Oakcrest School Chargers": "OAK",
        "Randolph-Macon Academy-VA": "RMA",
        "Saint John Paul the Great": "JP",
        "St. Gertrude High School": "SGHS",
        "St. Paul VI Catholic HS": "PVI",
        "Seton Swimming": "SST", 
        "Seton Swimming Alumni": "ALUM",
        "The Covenant School-VA": "TCS" ,
        "The Steward School-VA": "STEW",
        "Trinity Christian School-": "TCS!",
        "Trinity Christian School": "TCS!",
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
## Write the actual output file from the generated string
#####################################################################################
def write_output_file( output_dir: str, output_file_name: str, output_str: str ):
    """ generate the actual crawler output file """
    
    ## Create output dir if not exists
    if not os.path.exists( output_dir ):
        os.makedirs( output_dir )
    
    output_full_path = f"{output_dir}/{output_file_name}"
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

    return event_num, event_str


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
    
    for file in txtfiles:
        print(f"Filename: {file}")