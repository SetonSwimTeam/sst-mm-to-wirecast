import logging
import re

import sst_module_common as sst_common


#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
##########                                                                 ##########
##########    S S T _ M O D U L E _ R E S U L T _ S C O R E S              ##########
##########                                                                 ##########
##########    This module processes Scores which come on the end           ##########
##########    of the result page.  Quite a bit different then the          ##########
##########    format of the score report itself                            ##########
##########                                                                 ##########
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################


#####################################################################################
## SCORES_CHAMP Report
## This function processes the champsionship scores which are at the end
## of a results report.  
## Unfortunatlity this report is quite a bit different then the seperate score report
#####################################################################################
def process_champsionship_results_score( meet_report_filename: str, 
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
    gender = ""
    score_header = "Place   School                   Points"
    high_event_num = 0
    start_scoring = False
    need_header_h5 = True

    #1. St. Paul VI Catholic HS          419       2. Seton Swimming                  384.5
    #3. Seton Swimming                 199.5       4. Bishop Ireton Swim and Dive       145
    #5. Saint John Paul the Great        133       6. Benedictine College Prep        123.5
    #1. Bishop O'Connell              410.25       2. St. Paul VI High School        361.25

    #re_score_result  = re.compile('^(\d{1,2})\.\s+([A-z\' \.\-]{32})\s+(\d+)\s*(\d{1,2})?\.?\s*([A-z\' \.\-]{32})?\s*(\d+)?')
    re_score_result  = re.compile('^(\d{1,2})\.\s*([A-z\' \.\-]{32})\s*([0-9.]+)?\s*(\d{1,2})?\.\s*([A-z\' \.\-]{32})?\s*([0-9.]+)?')

    #####################################################################################
    ## RESULTS_SCORES_CHAMP: Loop through each line of the input file
    #####################################################################################
    with open(meet_report_filename, "r") as meet_report_file:
        for line in meet_report_file:

            #####################################################################################
            ## RESULTS_SCORES_CHAMP: Remove the extra newline at end of line
            #####################################################################################
            line = line.strip()

            #####################################################################################
            ## RESULTS_SCORES_CHAMP: Ignore all the blank lines             
            #####################################################################################
            if line == '\n' or line == '':
                continue

            #####################################################################################
            ## Meet Manager license name
            ## We have one event per page, so this starts the next event
            #####################################################################################
            if re.search("^%s" % mm_license_name, line):
                found_header_line = 1
                
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

            if line.lower().startswith(("event")):

                event_num, event_str = sst_common.get_event_num_from_eventline( line )
                if event_num < 100:
                    high_event_num = event_num

            if line.startswith("Scores - "):
                if not start_scoring:
                    output_list.append( ('H5', f"Scores Through Event {high_event_num}" ))

                start_scoring = True
                score_line_list = line.split('-')
                gender = score_line_list[1].strip()

                ## Add the header above the indivial team scores
                ## Gender. Make sure its upper case so it stands out
                output_list.append( ('H4', gender.upper() ))

            if start_scoring:
                score_line = re_score_result.findall(line)
                if score_line:
                    place1 = score_line[0][0].strip()
                    team1  = score_line[0][1].strip()
                    pnts1  = score_line[0][2].strip()
                    place2 = score_line[0][3].strip()
                    team2  = score_line[0][4].strip()
                    pnts2  = score_line[0][5].strip()

                    if score_line:
                        output_str = f"{place1:>2}. {team1:<30} {pnts1:>6}"
                        output_list.append( (f"SCORE_{gender}", output_str ))

                        if len(place2) > 0:
                            output_str = f"{place2:>2}. {team2:<30} {pnts2:>6}"
                            output_list.append( (f"SCORE_{gender}", output_str ))

                            logging.debug(f"RE MATCH: {place2} {team2} {pnts2}")

    create_output_result_scores_champ( output_dir, output_list, numresults )
    return num_files_generated


#####################################################################################
## SCORES_CHAMP Report
## Wrapper to generate mens and womens scores both on same page and on separate pages.
## Too many teams won't find combined on single page so generate both for the 
## webcast crew too choose
#####################################################################################
def create_output_result_scores_champ(output_dir_root: str, 
                                       output_list: list,
                                       num_results_to_display: int ) -> int:

    ## Sepearate files for mens/womens scores
    num_by_gender = create_output_result_scores_champ_by_gender( output_dir_root, output_list, num_results_to_display )

    ## Mens/womens scores on same page
    num_combined = create_output_result_scores_champ_combined( output_dir_root, output_list, num_results_to_display )
    return num_by_gender + num_combined


####################################################################################
## Given an array of PROGRAM lines PER HEAT, generate the output file
#####################################################################################
def create_output_result_scores_champ_by_gender( output_dir_root: str, 
                                       output_list: list,
                                       num_results_to_display: int ) -> int:
    num_files_generated = 0
    num_results_generated = 0
    output_dir = f"{output_dir_root}"


    for gender in ["Women", "Men"]:
        output_str = ""
        for output_tuple in output_list:
            row_type = output_tuple[0]
            row_text = output_tuple[1]

            logging.debug(f"RSCORES: g: {gender} {row_type} t: {row_text}")

            ## Save off the meet name, which somes at the end of the procesing as we are looping in reverse order
            if row_type == 'H2':
                output_str += row_text + '\n'
            elif row_type == 'H3':
                output_str += '\n'
            ## We may change case of gender for display purposes. Do case insensitive compare
            elif row_type == 'H4' and row_text.casefold() == f"Scores - {gender}".casefold():
                output_str += row_text + '\n'
                output_str += '\n'
            elif row_type == 'H4' and row_text.casefold() == f"{gender}".casefold():
                output_str += row_text + '\n'
                output_str += '\n'
            elif row_type == 'H5':
                output_str += row_text + '\n'
            elif row_type == 'H6':
                output_str += row_text + '\n'
            elif row_type == f"SCORE_{gender}":
                output_str += row_text + '\n'

            # num_results_generated += 1
            # if num_results_generated >= num_results_to_display:
            #     break;

        gender_lowercase = gender.lower()
        logging.warning(f"SCORES: {output_str}")
        output_file_name =  f"score_{gender_lowercase}.txt"
        sst_common.write_output_file( output_dir, output_file_name, output_str )
        num_files_generated += 1
    
    return num_files_generated


####################################################################################
## Given an array of PROGRAM lines PER HEAT, generate the output file
#####################################################################################
def create_output_result_scores_champ_combined( output_dir_root: str, 
                                                output_list: list,
                                                num_results_to_display: int ) -> int:
    num_files_generated = 0
    num_results_generated = 0
    output_dir = f"{output_dir_root}"


    output_str = ""
    for output_tuple in output_list:
        row_type = output_tuple[0]
        row_text = output_tuple[1]

        logging.debug(f"RSCORES: g: combined {row_type} t: {row_text}")

        ## Save off the meet name, which somes at the end of the procesing as we are looping in reverse order
        if row_type == 'H2':
            output_str += f"{row_text:<40}" + '\n'
        elif row_type == 'H3':
            pass
        elif row_type == 'H4':
            output_str += '\n' +  row_text + '\n'
        elif row_type == 'H5':
            output_str += row_text + '\n'
        elif row_type == 'H6':
            output_str += row_text + '\n'
        elif row_type.startswith("SCORE"):
            output_str += row_text + '\n'

        # num_results_generated += 1
        # if num_results_generated >= num_results_to_display:
        #     break;

    output_file_name =  f"score_combined.txt"
    sst_common.write_output_file( output_dir, output_file_name, output_str )
    num_files_generated += 1
    
    return num_files_generated