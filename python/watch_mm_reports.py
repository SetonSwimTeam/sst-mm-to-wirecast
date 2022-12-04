#!/c/Users/SetonSwimTeam/AppData/Local/Programs/Python/Python39/python


import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
#from generate_wirecast_files import *
import subprocess
import sys, os

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
        # if event.is_directory:
        #     return None
        # print(
        #     "[{}] noticed: [{}] on: [{}] ".format(
        #         time.asctime(), event.event_type, event.src_path
        #     )
        # )

        ## Meet manager will delete/create a file when overwriting existing file
        if not event.is_directory and event.event_type == 'created':
            generate_wirecast_files(event.src_path)

    # def on_created(self, event):
    #     # if event.is_directory:
    #     #     return None
    #     print(
    #         "[{}] CREATE: [{}] on: [{}] ".format(
    #             time.asctime(), event.event_type, event.src_path
    #         )
    #     )

def generate_wirecast_files(filepath):

    input_dir_name = os.path.dirname(filepath).replace(os.sep,'/')
    input_file_name = os.path.basename(filepath)
    print(f"dir: {input_dir_name}")
    print(f"file: {input_file_name}")
    args = f"-i {input_dir_name} -f {input_file_name}"
    external_app = ['python', 'c:/Users/SetonSwimTeam/git/sst-mm-to-wirecast/python/generate_wirecast_files.py']
    arg_list = ['-i', input_dir_name, '-f', input_file_name]
    external_app.extend( arg_list )
    external_app.extend(sys.argv[1:])
    #arg_list.extend(sys.argv[1:])
    ## Generate cmd line argements to pass into generate_wirecast_files
    # for new_arg in sys.argv[1:]:
    #     print(f"new arg: {new_arg}")
    #     arg_list.append(new_arg)
        
    print(f"Created: processing for file generate_wirecast_files.py {args}")
    #subprocess.run(["python", "c:/Users/SetonSwimTeam/git/sst-mm-to-wirecast/python/generate_wirecast_files.py", arg_list])
    subprocess.run(external_app)

if __name__ == "__main__":
    w = Watcher(r'C:\Users\SetonSwimTeam\Dropbox\wc_meetreports')
    w.run()