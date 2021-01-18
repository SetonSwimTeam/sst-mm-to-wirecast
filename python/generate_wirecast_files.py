#!/c/Users/SetonSwimTeam/AppData/Local/Programs/Python/Python39/python
# # ! d/usr/local/bin/python3

#############################################################################################
#############################################################################################
###
### generate_heat_files
###  This program will generate files (heat program files, event results and crawler results)
### for use in WireCast livestreaming software.  This script will 
###  generate both meet program entry files and meet results files.
###
### The code to generate each of the output files have been moved to their own modules file
### to separate the code base.
###
### reports need to be created with the following options set
###     1 event/heat per page
###     Top How Many needs to be set to ensure all results fit on a single page 
###         Wirecast can only display approx 14 results on their screen
###      Records is not selected
###      Splits is set to None
###
###  meet program entries:
###  Given a Meet Manager generated Meet Program, exported as a TXT file (single column one heat per page)
###   create individual files for every event/heat, with cleaned up text 
###   for optimal visualization on the live webcast for the WireCast application
###
###  meet results:
###  Given a Meet Manager generated Meet Results file, exported as a TXT file (sinle column one event per page)\
###  create individual results file per event for wirecast
###  Also generate a meet results CRAWL, which is a single line file with the results to
###  scroll through the botton of the livecast
###  
#############################################################################################
#############################################################################################

import os, os.path
import re
import argparse
from pathlib import Path
import glob
import logging
import sys
import fnmatch


###
### Import local modules that were split out for cleaner functionality
import sst_module_common as sst_common
import sst_module_program as sst_program
import sst_module_results as sst_results
import sst_module_scores as sst_scores

## Globals
report_type_results = "result"
report_type_program = "program"
report_type_crawler = "crawler"



#####################################################################################
## CLI param to remove existing files from directory.  This is needed when
## old heats won't be overwritten so we need to make sure they are removed
#####################################################################################
def remove_files_from_dir( reporttype: str, directory_name: str ) -> int:

    num_files_removed = 0
    """ Remove files from previous run/meet so there are no extra heats/events left over"""
    for root, dirs, files in os.walk(directory_name):
        for file in files:
            if  reporttype in file:
                os.remove(os.path.join(root, file)) 
                num_files_removed += 1

    return num_files_removed

# def remove_files_from_dir( reporttype: str, directory_name: str ) -> int:
#     rule = re.compile(fnmatch.translate('results'), re.IGNORECASE)
#     return [name for name in os.listdir(directory_name) if rule.match(name)]
#     for file in files_to_be_removed:
#         logging.warning(f"Files to be deleted: {file}")
#         # os.remove(os.path.join(root, file)) 
#         # num_files_removed += 1
    

#####################################################################################
## get_report_header_info
## Get the header info from the reports first X lines
#####################################################################################
def get_report_header_info( meet_report_filename: str ):
    """ Get the header info from the reports first X lines """
            
    #####################################################################################
    ## Example headers we are processing
    ##
    ## Seton School                             HY-TEK's MEET MANAGER 8.0 - 10:02 AM  11/19/2020
    ##               2020 NoVa Catholic Invitational Championship - 1/11/2020
    ##                                     Meet Program
    #####################################################################################

    line_num = 0
    line1_header = ""
    line2_header = ""
    line3_header = ""

    with open(meet_report_filename, "r") as meet_report_file:
        for line in meet_report_file:
            line_num += 1

            #####################################################################################
            ## Remove the extra newline at end of line
            #####################################################################################
            line = line.strip()

            #####################################################################################
            ## Line1: Seton School                             HY-TEK's MEET MANAGER 8.0 - 10:02 AM  11/19/2020                 
            #####################################################################################
            if line_num == 1:
                line1_header = line
                continue

            #####################################################################################
            ## Line2:               2020 NoVa Catholic Invitational Championship - 1/11/2020                
            #####################################################################################
            if line_num == 2:
                line2_header = line
                continue

            #####################################################################################
            ## Line3:                                    Meet Program               
            #####################################################################################
            if line_num == 3:
                line3_header = line

                ## Stop the loop now. We have our headers
                break

        #####################################################################################
        ## Header1.  Break about license name (school name)       
        #  There can be some garbage on the first line before the license name. Ignore that     
        #####################################################################################
        line1_list = re.findall('^.*?([A-z0-9 \'-]+?)\s+HY-TEK',line1_header )
        license_name = str(line1_list[0].strip())

        #####################################################################################
        ## Header2.  Break about meet name and meet date               
        #####################################################################################
        line2_list = re.findall('^(.*?) - (\d+/\d+/\d+)',line2_header )
        meet_name = line2_list[0][0].strip()
        meet_date = line2_list[0][1].strip()

        #####################################################################################
        ## Header2.  Break about meet name and meet date               
        #####################################################################################
        report_type = line3_header
        report_type_meet_name = ""

        if '-' in line3_header:
            report_type,report_type_meet_name = line3_header.split('-',1)
            report_type = report_type.strip()
            report_type_meet_name = report_type_meet_name.strip()
            
        #logging.debug(f"Header: licensee '{license_name}' meet_name: '{meet_name}' meet_date: '{meet_date}' report_type: '{report_type}'")

        return meet_name, meet_date, license_name, report_type, report_type_meet_name







#####################################################################################
#####################################################################################
##  M A I N
#####################################################################################
#####################################################################################
def process_main():
    #####################################################################################
    ## Parse out command line arguments
    #####################################################################################

    spacerelaynames = True
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-i', '--inputdir',         dest='inputdir',            default="c:\\Users\\SetonSwimTeam\\mmreports",   
                                                                                                                help="input directory for MM extract report")
    parser.add_argument('-f', '--filename',         dest='filename',            required=True        ,          help="Input file name")
    parser.add_argument('-o', '--outputdir',        dest='outputdir',           default="c:\\Users\\SetonSwimTeam\\Dropbox\\wirecast",           help="root output directory for wirecast heat files.")
    parser.add_argument('-c', '--crawler',          dest='crawler',             action='store_true',            help="Generate crawler files")
    parser.add_argument('-r', '--shortschrelay',    dest='shortschoolrelay',     action='store_true',           help="Use Short School names for Relays")
    parser.add_argument('-l', '--longschind',       dest='longschoolindividual',action='store_true',            help="Use Long School names for Indiviual Entries")
    parser.add_argument('-d', '--delete',           dest='delete',              action='store_true',            help="Delete existing files in OUTPUT_DIR")
    parser.add_argument('-n', '--numresults',       dest='numresults',          type=int, default='14',         help="Number of results listed per event")
    parser.add_argument('-x', '--lastnumevents',    dest='lastnumevents',       type=int, default='3',          help="Crawler outputs a separate file with the last N events")
    parser.add_argument('-e', '--emptyresults',     dest='emptyresults',        action='store_true',            help="Generate empty results files for wirecast template setup")

    ## Parms not used as often
    parser.add_argument('-S', '--splitrelays',      dest='splitrelays',         action='store_true',            help="Split Relays into multiple files")
    parser.add_argument('-R', '--displayRelayNames',dest='displayRelayNames',   action='store_true',            help="Display relay swimmer names, not just the team name in results")
    parser.add_argument('-N', '--namesfirstlast',   dest='namesfirstlast',      action='store_true',            help="Swap Non Relay names to First Last from Last, First")
    parser.add_argument('-T', '--reporttype',       dest='reporttype',          default="auto",                 choices=['auto','program','results', 'headers'], 
                                                                                                                help="Program type, Meet Program or Meet Results")
    ## For debugging
    parser.add_argument('-v', '--log',              dest='loglevel',            default='warning',                 choices=['error', 'warning', 'info', 'debug'],            
                                                                                                                help="Set debugging level2")
    parser.add_argument('-q', '--quote ',           dest='quote',               action='store_true',            help="Quote the output fields for DEBUGGING")
    parser.add_argument('-h', '--help',             dest='help',                action='help', default=argparse.SUPPRESS, help="Tested with MM 8")

    parser.set_defaults(shortschoolrelay=False)
    parser.set_defaults(shortschoolindividual=False)
    parser.set_defaults(splitrelays=False)
    parser.set_defaults(displayRelayNames=False)
    parser.set_defaults(namesfirstlast=False)
    parser.set_defaults(delete=False)
    parser.set_defaults(quote=False)
    parser.set_defaults(crawler=False)
    parser.set_defaults(emptyresults=False)

    args = parser.parse_args()

    inputfile =f"{args.inputdir}/{args.filename}"

    ## Determine logging logleve
    loglevel = logging.DEBUG
    if args.loglevel == "debug":
        loglevel = logging.DEBUG
    elif args.loglevel == "info":
        loglevel = logging.INFO
    elif args.loglevel == "warning":
        loglevel = logging.WARNING
    elif args.loglevel == "error":
        loglevel = logging.ERROR

    #logging.basicConfig(flogging.DEBUGilename='example.log', filemode='w', level=logging.DEBUG) 
    # logging.basicConfig( format='%(levelname)s:%(message)s', level=logging.INFO)
    logging.basicConfig( format='%(message)s', level=loglevel)

    process_to_run = {"program": False, "results": False, "crawler": False, "scores_champsionship": False, "scores_dualmeet": False }
    
    report_type_to_run = args.reporttype

    ## Set global debug flag
    total_files_generated_program = 0
    total_files_generated_results = 0
    total_crawler_files = 0
    total_scores_files = 0

    #####################################################################################
    ## Verify the directories and input file exists
    #####################################################################################
    error_msg = sst_common.verify_dirs_files( args.inputdir, args.filename,  args.outputdir )
    if not error_msg == "":
        logging.error(f"Directory and/or input file error:\n{error_msg}")
        sys.exit(3)

    #####################################################################################
    ## Get header info from the meet file
    ## We need to dynamically get the meet name and license_name for use in processing files
    ## The license_name is the first line on the start of every new page/event/heat
    #####################################################################################
    meet_name, meet_date, license_name, report_type, report_type_meet_name = get_report_header_info( inputfile )

    #####################################################################################
    ##
    ## Determine report type based on input file header if not specified on CLI
    #####################################################################################
    if (report_type_to_run == "program")   or  (report_type_to_run == "auto" and report_type == 'Meet Program'):
        process_to_run['program'] = True
    elif (report_type_to_run == "results") or (report_type_to_run == "auto" and report_type == 'Results'):
        process_to_run['results'] = True
    elif (report_type_to_run == "Team Rankings") or (report_type_to_run == "auto" and report_type == 'Team Rankings'):
        process_to_run['scores_champsionship'] = True
    elif (report_type_to_run == "Dual Meet Scores") or (report_type_to_run == "auto" and report_type == 'Dual Meet Scores'):
        process_to_run['scores_dualmeet'] = True

    # Set the crawler flag
    process_to_run['crawler'] = args.crawler

    output_dir = args.outputdir
    ## The outputdir string MUST have a trailing slash.  Check string and add it if necesssary
    if output_dir[-1] != '/':
        output_dir = f"{output_dir}/"
    
    logargs = f"{Path(__file__).stem}  \n" + \
              f"\n   Params: \n" + \
              f"\tOutputReportType \t{args.reporttype} \n" + \
              f"\tInputFile \t\t{inputfile} \n" + \
              f"\tRoot OutputDir \t\t{output_dir} \n" + \
              f"\tShort Sch Names Relays \t{args.shortschoolrelay} \n" + \
              f"\Long Sch Names Indiv \t{args.longschoolindividual} \n" + \
              f"\tNamesFirstlast \t\t{args.namesfirstlast} \n" + \
              f"\tSplit Relays \t\t{args.splitrelays} \n"+ \
              f"\tDisplay Relays Names \t{args.displayRelayNames} \n"+ \
              f"\tSpaces in Relay Names \t{spacerelaynames}\n" + \
              f"\tDelete exiting files \t{args.delete}\n" + \
              f"\tCrawler last XX files \t{args.lastnumevents}\n" + \
              f"\tNum Reslts Generate \t{args.numresults}\n" + \
              f"\tQuote output fields \t{args.quote}\n" + \
              f"\tLog Level \t\t{args.loglevel}\n" + \
              f"\n   Headers: \n" + \
              f"\tMeet Name: \t\t'{meet_name}' \n" + \
              f"\tMeet Date: \t\t'{meet_date}' \n" + \
              f"\tHeader3 Meet Name: \t'{report_type_meet_name}' \n" + \
              f"\tLicensee: \t\t'{license_name}' \n" + \
              f"\tSourceReport: \t\t'{report_type}' \n" + \
              f"\tEmptyResults: \t\t'{args.emptyresults}' \n" 
    logging.warning( logargs )

    logging.warning(f"\n    Reports to generate: ")
    for i in process_to_run:
        if process_to_run[i]:
            logging.warning(f"\t{i} \n")

    #####################################################################################
    ## Generate wirecast files from a MEET PROGRAM txt file
    #####################################################################################
    if process_to_run['program']:

        if args.delete:
             ## Remove files from last run as we may have old events/heats mixed in
            remove_files_from_dir( 'program', output_dir )
            remove_files_from_dir( 'PROGRAM', output_dir )

        total_files_generated_program , total_crawler_files = \
            sst_program.process_program( inputfile, 
                                        output_dir, 
                                        license_name, 
                                        args.shortschoolrelay, 
                                        args.longschoolindividual, 
                                        args.splitrelays, 
                                        spacerelaynames, 
                                        args.displayRelayNames, 
                                        args.namesfirstlast, 
                                        args.quote,
                                        args.crawler)

    #####################################################################################
    ## Generate wirecast files RESULTS and CRAWLER from a MEET RESULTS txt file
    #####################################################################################
    if process_to_run['results']:

        if args.delete:
             ## Remove files from last run as we may have old eventsmixed in
            remove_files_from_dir( 'results', output_dir )
            remove_files_from_dir( 'RESULTS', output_dir )

        if args.emptyresults:
            total_empty_results =  \
                sst_results.generate_empty_results( output_dir )

        total_files_generated_results, total_crawler_files = \
               sst_results.process_result(  inputfile, 
                                            output_dir, 
                                            license_name, 
                                            args.shortschoolrelay, 
                                            args.longschoolindividual, 
                                            args.displayRelayNames, 
                                            args.displayRelayNames, 
                                            args.namesfirstlast, 
                                            args.quote ,
                                            args.numresults,
                                            args.lastnumevents,
                                            args.crawler )


    #####################################################################################
    ## Generate wirecast files CHAMPSIONSHIP SCORES from a MEET SCORES txt file
    #####################################################################################
    if process_to_run['scores_champsionship']:
        total_scores_files = \
            sst_scores.process_score_champsionship(  
                                            inputfile, 
                                            output_dir, 
                                            license_name, 
                                            args.quote,
                                            args.numresults )

    #####################################################################################
    ## Generate wirecast files DUALMEET SCORES from a MEET SCORES txt file
    #####################################################################################
    if process_to_run['scores_dualmeet']:
        total_scores_files = \
               sst_scores.process_score_dualmeet(  
                                            inputfile, 
                                            output_dir, 
                                            license_name, 
                                            args.quote,
                                            args.numresults )


    logging.warning(f"{report_type} Process Completed:")

    if total_files_generated_program > 0:
        logging.warning(f"\tNumber of 'Program' files generated: {total_files_generated_program}")
    if total_files_generated_results > 0:
        logging.warning(f"\tNumber of 'Results' files generated: {total_files_generated_results}")
    if total_crawler_files > 0:
        logging.warning(f"\tNumber of 'Crawler' files generated: {total_crawler_files}")
    if total_scores_files > 0:
        logging.warning(f"\tNumber of 'Score' files generated: {total_scores_files}")



#####################################################################################
#####################################################################################
##  M A I N
#####################################################################################
#####################################################################################
if __name__ == "__main__":
    process_main()#!/c/Users/SetonSwimTeam/AppData/Local/Programs/Python/Python39/python
# # ! d/usr/local/bin/python3
