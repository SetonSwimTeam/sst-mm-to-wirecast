#####################################################################################
## Given an array of RESULTS lines PER EVENT, generate the output file for this event
#####################################################################################
def create_output_file_results( output_dir_root: str, 
                                event_num: int, 
                                output_list: list, 
                                display_relay_swimmer_names: bool,
                                num_results_to_display: int ) -> int:
    """ Generate the filename and open the next file """
    
    num_files_generated = 0
    num_results_generated = 0
    output_str = ""

    file_name_prefix = "results"

    output_dir = f"{output_dir_root}{file_name_prefix}/"

    ## Ignore the case where we get event0 heat0
    if event_num == 0:
        return 0

    ## Create output dir if not exists
    if not os.path.exists( output_dir ):
        os.makedirs( output_dir )

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
            output_str += unofficial_results + '\n'
            output_str += row_text + '\n'
        elif row_type == 'PLACE':
            output_str += row_text + '\n'
            num_results_generated += 1
        elif row_type == 'NAME' and display_relay_swimmer_names:
            output_str += row_text + '\n'

        if num_results_generated >= num_results_to_display:
            break;

    output_file_name = output_dir + f"{file_name_prefix}_Event{event_num:0>2}.txt"
    sst_common.write_output_file( output_file_name, output_str )
    num_files_generated += 1

    return num_files_generated

