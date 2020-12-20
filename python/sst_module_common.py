## Define the types of events in this meet (Individual, Relay and Diving)
event_num_individual = [3,4,5,6,7,8,11,12,13,14,15,16,19,20,21,22]
event_num_relay  = [1,2,17,18,23,24]
event_num_diving = [9,10]



#####################################################################################
## Write the actual output file from the generated string
#####################################################################################
def write_output_file( output_file_name: str, output_str: str ):
    """ generate the actual crawler output file """
    output_file_handler = open( output_file_name, "w+" )
    output_file_handler.write( output_str )
    output_file_handler.close()
