# Generate meet files for Wirecast

This program will take a Meet Manager generated MeetProgram or a Results file, saved as a text file, and reformat that text file for optimal display in wirecast.

## How to Run
```
python/generate_wirecast_files.py -f dec-results.txt
python/generate_wirecast_files.py -h
```

## Format Reports
The report needs very specific formatting options for this program to work.

## Meet Program
![program column/format](img/program_options_columns.png )

![program include](img/program_options_include.png )





## Results

Its best to create a memorized repor for results as you will have to run it after every event.

![results column/format](img/results_options_columns.png )

* Column: Single
* 1 Event Per Page
* Top How Many 24 (results must fit on single page)

![results Include](img/results_options_include.png )

* DeSelect
    * results
* Include
    * Entry Times
    * Athlete / Relay Points

![results splits](img/results_options_splits.png )
* Splits: None



## Save Report

![Save as Text](img/report_saveas_text.png )

Save as Text to the default input file directory for the generate script. 

Default directory: 
```C:\Users\SetonSwimTeam\mmreports```