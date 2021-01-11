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
                                 quote_output: bool,
                                 numresults: int ):


    num_header_lines = 3
    found_header_line = 0
    output_list = []
    num_files_generated = 0
    ## Quote output for debuggin
    q = "'" if quote_output else ""

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
                    line2_list = re.findall('^(.*?) - (\d+/\d+/\d+)',line )
                    meet_name = line2_list[0][0].strip()
                    meet_date = line2_list[0][1].strip()
                    output_list.append( ('H2', meet_name ))
                elif found_header_line == 3:
                    output_list.append( ('H3', line ))
                continue

            #logging.debug(f"SCORE: line: {line}")
            # Look for Boys/Girls Team Scores heading
            # Girls - Team Scores
            if " - Team Scores" in line:
                gender, team_score = line.split(' - ')



            #####################################################################################
            #12345678901234567890123456789012345678901234567890
            # 1   Bishop O'Connell                     Bishop O'Connell                    487
            #re_score_result  = re.compile('^([*]?\d{1,2}|---)\s+([A-z\' \.]+, [A-z ]+?) ([A-Z0-9]{1,2})\s+([A-Z \'.].*?)([0-9:.]+|NT|NP)\s+([xX0-9:.]+)\s*([0-9]*)')
            re_score_result  = re.compile('^(\d{1,2})\s+([A-z\' \.]{25})\s+([A-z\' \.]{25})\s+(\d+)\s*(\d*)')

            score_line = re_score_result.findall(line)
            if score_line:
                scoreline_place       = str(score_line[0][0]).strip()
                scoreline_school1      = str(score_line[0][1]).strip()
                scoreline_school2      = str(score_line[0][2]).strip()
                scoreline_points      = str(score_line[0][3]).strip()

                ## A decimal point comes over a space.  Convert "123 50' to '123.50' if present"
                scoreline_points2     = str(score_line[0][4]).strip()
                if scoreline_points2:
                    scoreline_points += "." + scoreline_points2

                #logging.debug( f"*** SCORE: p: {scoreline_place} s1: {scoreline_school1} s2: {scoreline_school2} p: {scoreline_points}" )
                output_str = f"{q}{scoreline_place:>2}{q} {q}{scoreline_school1:<25}{q} {q}{scoreline_points:>8}{q}"
                output_list.append( ('SCORE', output_str ))

                logging.debug( f"SCORE: output: {output_str}" )

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