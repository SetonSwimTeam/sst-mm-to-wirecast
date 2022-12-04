#!/c/Users/SetonSwimTeam/AppData/Local/Programs/Python/Python39/python

#############################################################################################
#############################################################################################
###
### generate_heat_files



import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
#from generate_wirecast_files import *
import subprocess
import sys, os
import pathlib

class Watcher:
    def __init__(self, path):
        self.observer = Observer()
        self.path = path

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.path, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        ## Meet manager will delete/create a file when overwriting existing file
        if event.event_type == 'created':
            generate_wirecast_files(event.src_path)

def generate_wirecast_files(filepath):

    input_dir_name = os.path.dirname(filepath).replace(os.sep,'/')
    input_file_name = os.path.basename(filepath)
    input_file_extension = pathlib.Path(input_file_name).suffix

    if input_file_extension == '.txt':

        # schools.txt is required for processing, but its just an input file so nothing to do here
        if input_file_name != 'schools.txt':

            ## Define the python application to call when a new report file has been created
            external_app = ['python', 'c:/Users/SetonSwimTeam/git/sst-mm-to-wirecast/python/generate_wirecast_files.py']

            ## Automatically generate input directory and input filename based on file that was just created
            arg_list = ['-i', input_dir_name, '-f', input_file_name]
            external_app.extend( arg_list )

            ## Pull in command line argements
            external_app.extend(sys.argv[1:])
                
            print(f"INFO: New file CREATION detected on filename {input_file_name}")
            subprocess.run(external_app)
        else:
            print(f"INFO: Found file {input_file_name}: ignoring as its a reference file")
    else:
            print(f"WARNING: Filetype not '.txt'. Ignorning file {input_file_name}")

if __name__ == "__main__":
    w = Watcher(r'C:\Users\SetonSwimTeam\Dropbox\wc_meetreports')
    w.run()