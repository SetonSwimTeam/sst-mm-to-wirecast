import logging
import sys
import sst_module_common as sst_common
import datetime

#####################################################################################
####
#### The schools module will read in a school report (saved as a text file)
#### and builds a dictionary of school name, short name and abbreviation
####
#####################################################################################


#####################################################################################
## Readin in school report
#####################################################################################
def process_schools_report( school_report_filename: str ):

    line_num=0
    try:
        with open(school_report_filename, "r") as school_report_file:
            for in_line in school_report_file:

                line = in_line.strip()

                ## The first three lines are headers so  skip those
                ## Ignore blank lines
                if len(line) > 0 and line_num >= 3:

                    print( f"Line {line_num}: '{line}'")

                    ## The format of the schhol report is
                    # 7    SST         Seton Swimming                              Seton
                    #0123456789012345678901234567890123456789012345678901234567890123456789
                    school_abbr_full = line[5:16].strip()
                    school_name_full = line[17:60].strip()
                    school_name_short = line[61:].strip()
                    school_lsc = ""

                    ## some schools have USA swimming region attached to it, ie.e "BW-VA".
                    ## (Remove the -VA if it exists
                    if len(school_abbr_full) > 3 and school_abbr_full[-3] == "-":
                        school_lsc = school_abbr_full[-2:]
                        school_abbr_short = school_abbr_full[:-3]
                    else:
                        school_abbr_short = school_abbr_full
                        
                    logging.debug(f"'{school_abbr_full}' '{school_abbr_short}' '{school_name_full}' '{school_name_short}'")

                    ## Create a dictionary
                    school_name_dict = { "school_abbr_full":  school_abbr_full,   # BW-PV
                                        "school_abbr_short": school_abbr_short,   # BW
                                        "school_name_full":  school_name_full,    # Brookewood School
                                        "school_name_short": school_name_short,   # Brookewood 
                                        "school_lsc": school_lsc                  # VA
                                        }

                    ## Load the school_dict array
                    sst_common.school_name_list.append( school_name_dict )

                line_num += 1
    except FileNotFoundError as fnfe:
        logging.error(f"Required School Report file not found: {school_report_filename}")
        sys.exit(4)
    print(f"process_school_reports: {sst_common.school_name_list}")

#####################################################################################
## Return a School_Dict object matching by school_full_name
#####################################################################################
def get_schools_dict_by_full_name( element_name_full ) -> dict:

    for school_dict in sst_common.school_name_list:
        ## Test long school names without LSC
        school_name_full = school_dict["school_name_full"]
        if school_name_full[:22] == element_name_full[:22]:
            return school_dict
        # Test long school names with LSC (No idea why MM access LSC to long name, but it does)
        if len(element_name_full) > 3 and element_name_full[-3] == "-":
            if school_name_full == element_name_full[:-3]:
                return school_dict

        ## Worst case, if there is something wrong with the regex, see if the school name is a substring
        if school_name_full in element_name_full:
            return school_dict

    ## Should not get here. No school match
    raise Exception(f"NoSuchSchoolFullName: {element_name_full}")
            
    #return {element_name_full}

#####################################################################################
## Return a School_Dict object matching by school_full_name
#####################################################################################
def get_schools_dict_by_full_abbr( element_abbr_full ) -> dict:

    for school_dict in sst_common.school_name_list:
        if school_dict["school_abbr_full"] == element_abbr_full:
            return school_dict

    ## Should not get here. No school match
    raise Exception(f"NoSuchSchoolFullAbbr: {element_abbr_full}")


#####################################################################################
## For testing
#####################################################################################
if __name__ == "__main__":
    process_schools_report("data/schools.txt")
    school_dict = get_schools_dict_by_full_name( "Seton Swimming" )
    print(f"FOUND_NAME_FULL: {school_dict}")

    school_dict = get_schools_dict_by_full_abbr( "SST" )
    print(f"FOUND_ABBR_FULL: {school_dict}")
