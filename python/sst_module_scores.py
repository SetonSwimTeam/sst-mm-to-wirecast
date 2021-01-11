import logging
import re

import sst_module_common as sst_common


#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
##########                                                                 ##########
##########    S S T _ M O D U L E _ S C O R E S                            ##########
##########                                                                 ##########
##########    Code to generate Score Results files from the meet program   ##########
##########                                                                 ##########
##########                                                                 ##########
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################

def process_score_champsionship( meet_report_filename: str, 
                                 output_dir: str, 
                                 mm_license_name: str, 
                                 quote: bool,
                                 numresults: int ):


    num_header_lines = 3
    found_header_line = 0
    output_list = []
    num_files_generated = 0

    #####################################################################################
    ## SCORES_CHAMP: Loop through each line of the input file
    #####################################################################################
    with open(meet_report_filename, "r") as meet_report_file:
        for line in meet_report_file:

            #####################################################################################
            ## SCORES_CHAMP: Remove the extra newline at end of line
            #####################################################################################
            line = line.strip()

            #####################################################################################
            ## SCORES_CHAMP: Ignore all the blank lines             
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
                num_files = create_output_file_scores( output_dir, output_list )
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

    create_output_file_scores( output_dir, output_list )
    


####################################################################################
## Given an array of PROGRAM lines PER HEAT, generate the output file
#####################################################################################
def create_output_file_scores( output_dir_root: str, 
                               output_list: list ) -> int:
    num_files_created = 0

    logging.warning("\n create_output_file_scores")
    for output_tuple in output_list:
        row_type = output_tuple[0]
        row_text = output_tuple[1]

        logging.warning(f"SCORES: {row_type} t: {row_text}")


    return num_files_created