#!/usr/local/bin/python3

def main():
    # Define input file
    heat_sheet_file = "../data/mm8heatsheetdefault1col.txt"
    output_dir ="../output/"

    schoolNameDict = { "Seton Swimming":"SST", 
                       "SOUTH":"S" } 
    
    headerLine = "Lane  Name                    Year School      Seed Time"

    eventNum = 0
    heatNum = 0

    with open(heat_sheet_file, "r") as heat_sheet_file:
        for line in heat_sheet_file:

            eventLine = ""
            ## Remove all the blank lines
            if line != '\n':

                ## Remove the extra newline
                line = line.strip()

                ## Ignore these lines
                if line.lower().startswith((" seton", "seton", "meet", "lane")):
                    #headerLine = line
                    continue

                ## Start with Event
                if line.lower().startswith(("event")):
                    eventLine = line

                    ## Remove all those extra spaces in the line
                    cleanEventStr = eventLine.split()
                    cleanEventStr = " ".join(cleanEventStr)
                    # Get the line number
                    eventStr = cleanEventStr.split(' ', 4)
                    eventNum = int(eventStr[1].strip())


                # Remove "Timed Finals" from Heat line
                if line.lower().startswith(("heat")):
                    line = line.replace("Timed Finals", "")
                    ## Remove all those extra spaces in the line
                    splitHeatStr = line.split()
                    splitHeatStr = " ".join(splitHeatStr)
                    # Get the heat number
                    splitHeatStr = splitHeatStr.split(' ', 4)
                    heatNum = int(splitHeatStr[1])

                    ## Open New file for Event/Heat info
                    print( f"Event {eventNum}: Heat {heatNum}" )
                    newFileName = output_dir + f"Entry_Event{eventNum:0>2}_Heat{heatNum:0>2}.txt"
                    print(f"output_dir {newFileName}")
                    eventHeatFile = open( newFileName, "w+" )
                    eventHeatFile.write( eventLine  + '\n')

                    
                ## Replace long school name with short name
                for k,v in schoolNameDict.items():
                    line = line.replace(k, v)

                if eventNum > 0 and heatNum > 0:
                    print(  f"{line}" )
                    eventHeatFile.write( line  + '\n')

                if line.lower().startswith(("heat")):
                    print(  f"{headerLine}" )
                    eventHeatFile.write( line + '\n')








if __name__ == "__main__":
    main()