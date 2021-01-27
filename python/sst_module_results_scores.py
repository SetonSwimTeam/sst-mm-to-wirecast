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

def process_score_dualmeet( meet_report_filename: str, 
                                 output_dir: str, 
                                 mm_license_name: str, 
                                 quote_output: bool,
                                 numresults: int ):


    num_header_lines = 3
    found_header_line = 0
    output_list = []
    num_files_generated = 0
    ## Quote output for debugging
    q = "'" if quote_output else ""
    gender = ""
    score_header = ""
    scores_for_gender = "" 

    #                      Seton Swimming  182.00    114.00  Trinity Christian School
    re_score_result  = re.compile('^(\d{1,2})\s+([A-z\' \.]{27})\s+([A-z\' \.]{27})\s+(\d+)\s*(\d*)')

    #####################################################################################
    ## SCORES_DUAL: Loop through each line of the input file
    #####################################################################################
    with open(meet_report_filename, "r") as meet_report_file:
        for line in meet_report_file:

            #####################################################################################
            ## SCORES_DUAL: Remove the extra newline at end of line
            #####################################################################################
            line = line.strip()

            #####################################################################################
            ## SCORES_DUAL: Ignore all the blank lines             
            #####################################################################################
            if line == '\n' or line == '':
                continue
            logging.debug(f"LINE: {line}")

            #####################################################################################
            ## Meet Manager license name
            ## We have one event per page, so this starts the next event
            #####################################################################################
            if re.search("^%s" % mm_license_name, line):
                found_header_line = 1
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

            ## Determine which gener the scores are for
            if re.search("^\s*Men\s*$", line):
                logging.debug(f"Found Men")
                scores_for_gender = "Men"
                output_list.append( ('H6Men', "Men" ))

            if re.search("^\s*Women\s*$", line):
                logging.debug(f"Found Women")
                scores_for_gender = "Women"
                output_list.append( ('H6Women', "Women" ))

            ## Search for the actual score line.
            ## Parse out the fields, and regenerate our own line without hyteks formatting/centering
            re_score_dual  = re.compile('^\s*([A-z\' \.]+?)\s+(\d{1,3}\.\d{2})\s+(\d{1,3}\.\d{2})\s+([A-z\' \.]+?)$')
            score_line = re_score_dual.findall(line)
            if score_line:
                score_team1  = str(score_line[0][0]).strip()
                score_score1 = str(score_line[0][1]).strip()
                score_score2 = str(score_line[0][2]).strip()
                score_team2  = str(score_line[0][3]).strip()

                #logging.debug(f"SCORE: t1 {score_team1}: s1 {score_score1}: s2 {score_score2}: t2: {score_team2}")

                output_str = f"{q}{score_team1:>22}{q} {q}{score_score1:>5}{q} {q}{score_score2:>5}{q} {q}{score_team2:<30}{q}"
                logging.debug(f"SCORE: {output_str}")

                ## Add the score to the output list
                output_list.append( (scores_for_gender, output_str ))

    num_files_generated = create_output_file_scores_dual_combined( output_dir, output_list, numresults )
    num_files_generated = create_output_file_scores_dual_by_gender( output_dir, output_list, numresults )
    return num_files_generated

#####################################################################################
## SCORES_CHAMP Report
## This function processes a separate scores report for a championship meeet
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
    gender = ""
    score_header = "Place   School                   Points"


    # 1   Bishop O'Connell                     Bishop O'Connell                    487
    re_score_result  = re.compile('^(\d{1,2})\s+([A-z\' \.]{27})\s+([A-z\' \.]{27})\s+(\d+)\s*(\d*)')

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
                if gender != "":
                    num_files = create_output_file_scores_champ( output_dir, output_list, gender, numresults )
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

                ## Add the header above the indivial team scores
                output_list.append( ('H4', line ))
                output_list.append( ('H6', score_header ))

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
                output_str = f"{q}{scoreline_place:>2}{q} {q}{scoreline_school1:<27}{q} {q}{scoreline_points:>8}{q}"
                output_list.append( ('SCORE', output_str ))

                logging.debug( f"SCORE: output: {output_str}" )

    create_output_file_scores_champ( output_dir, output_list, gender, numresults )
    return num_files_generated

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

    # 1   Bishop O'Connell                     Bishop O'Connell                    487
    #re_score_result  = re.compile('^(\d{1,2})\s+([A-z\' \.]{27})\s+([A-z\' \.]{27})\s+(\d+)\s*(\d*)')

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
                start_scoring = True
                score_line_list = line.split('-')
                gender = score_line_list[1].strip()

                logging.error(f"RESULTS: {gender} Scores: Through event {high_event_num}")
                #if gender == "Men":
                    ## Started Processing mens scores. 

                ## Add the header above the indivial team scores
                output_list.append( ('H4', line ))
                #output_list.append( ('H6', score_header ))

            #1. St. Paul VI Catholic HS          419       2. Seton Swimming                  384.5
            #re_score_result  = re.compile('^(\d{1,2})\.\s+([A-z\' \.\-]{32})\s+(\d+)')
            re_score_result  = re.compile('^(\d{1,2})\.\s+([A-z\' \.\-]{32})\s+(\d+)\s*(\d{1,2})?\.?\s*([A-z\' \.\-]{32})?\s*(\d+)?')

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
                        #logging.error(f"RE MATCH: {score_line}")
                        logging.error(f"RE MATCH: {place1} {team1} {pnts1}")
                        output_str = f"{place1} {team1} {pnts1}"
                        output_list.append( (f"SCORE_{gender}", output_str ))

                        if len(place2) > 0:
                            output_str = f"{place2} {team2} {pnts2}"
                            output_list.append( (f"SCORE_{gender}", output_str ))

                            logging.error(f"RE MATCH: {place2} {team2} {pnts2}")

    create_output_file_scores_champ( output_dir, output_list, gender, numresults )
    return num_files_generated

####################################################################################
## Given an array of DUAL meet scores, generate both boys and girls as two different files
# #####################################################################################
def create_output_file_scores_dual_by_gender( output_dir_root: str, 
                                    output_list: list,
                                    num_results_to_display: int ) -> int:
    num_files_generated = 0
    num_results_generated = 0
    output_str = ""
    output_dir = f"{output_dir_root}"


    for report_type in ["Men", "Women"]:
        output_str = ""
        num_results_generated = 0
        for output_tuple in output_list:
            row_type = output_tuple[0]
            row_text = output_tuple[1]

            logging.debug(f"DUAL SCORES: g: {report_type} r: {row_type} t: {row_text}")

            ## Save off the meet name, which somes at the end of the procesing as we are looping in reverse order
            if row_type == 'H2':
                output_str += row_text + '\n'
            elif row_type == 'H3':
                output_str += row_text + '\n'
                output_str += '\n'
            elif row_type == 'H4':
                output_str += row_text + '\n'
                output_str += '\n'
            elif row_type == 'H6'+ report_type:
                output_str += row_text + '\n'
            elif row_type == report_type:
                output_str += row_text + '\n'

                num_results_generated += 1
                if num_results_generated >= num_results_to_display:
                    break;

        gender_lowercase = report_type.lower()
        output_file_name =  f"score_dual_{gender_lowercase}.txt"
        sst_common.write_output_file( output_dir, output_file_name, output_str )
        num_files_generated += 1

    return num_files_generated


####################################################################################
## Given an array of DUAL meet scores, generate both boys and girls on same file
#####################################################################################
def create_output_file_scores_dual_combined( output_dir_root: str, 
                                    output_list: list,
                                    num_results_to_display: int ) -> int:
    num_files_generated = 0
    num_results_generated = 0
    output_str = ""
    output_dir = f"{output_dir_root}"
    print_header = True


    for report_type in ["Men", "Women"]:
        num_results_generated = 0
        for output_tuple in output_list:
            row_type = output_tuple[0]
            row_text = output_tuple[1]

            logging.debug(f"DUAL SCORES: g: {report_type} r: {row_type} t: {row_text}")

            ## Save off the meet name, which somes at the end of the procesing as we are looping in reverse order
            if row_type == 'H2' and print_header:
                output_str += f"{row_text:>50}" + '\n'
            elif row_type == 'H3' and print_header:
                output_str += f"{row_text:>55}" + '\n'
                output_str += '\n'
            elif row_type == 'H4' and print_header:
                output_str += row_text + '\n'
            elif row_type == 'H6'+ report_type:
                output_str += '\n' + f"{row_text:>38}" + '\n'
                print_header = False
            elif row_type == report_type:
                output_str += row_text + '\n'

                num_results_generated += 1
                if num_results_generated >= num_results_to_display:
                    break;

    output_file_name =  f"score_dual_combined.txt"
    sst_common.write_output_file( output_dir, output_file_name, output_str )
    num_files_generated += 1

    return num_files_generated
####################################################################################
## Given an array of PROGRAM lines PER HEAT, generate the output file
#####################################################################################
def create_output_file_scores_champ( output_dir_root: str, 
                               output_list: list,
                               gender_of_scores: str,
                               num_results_to_display: int ) -> int:
    num_files_generated = 0
    num_results_generated = 0
    output_str = ""
    output_dir = f"{output_dir_root}"

    for output_tuple in output_list:
        row_type = output_tuple[0]
        row_text = output_tuple[1]

        logging.debug(f"SCORES: {row_type} t: {row_text}")

        ## Save off the meet name, which somes at the end of the procesing as we are looping in reverse order
        if row_type == 'H2':
            output_str += row_text + '\n'
        elif row_type == 'H3':
            output_str += row_text + '\n'
            output_str += '\n'
        elif row_type == 'H4':
            output_str += row_text + '\n'
            output_str += '\n'
        elif row_type == 'H6':
            output_str += row_text + '\n'
        elif row_type == 'SCORE':
            output_str += row_text + '\n'

        num_results_generated += 1
        if num_results_generated >= num_results_to_display:
            break;

    gender_lowercase = gender_of_scores.lower()
    output_file_name =  f"score_champsionship_{gender_lowercase}.txt"
    sst_common.write_output_file( output_dir, output_file_name, output_str )
    num_files_generated += 1
    
    return num_files_generated
