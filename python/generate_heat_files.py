#!/usr/local/bin/python3

def main():
    # Define input file
    heat_sheet_file = "../data/mm8heatsheetdefault1col.txt"
    output_dir ="../output"

    schoolNameDict = { "Seton Swimming":"SST", 
                       "SOUTH":"S" } 
    
    headerLine = "Lane  Name                    Year School      Seed Time"

    with open(heat_sheet_file, "r") as heat_sheet_file:
        for line in heat_sheet_file:

            eventLine = ""
            ## Remove all the blank lines
            if line != '\n':

                ## Remove the extra newline
                line = line.strip()

                ## Ignore these lines
                if line.lower().startswith(("seton", "meet", "lane")):
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
                    eventNum = {eventStr[1]}


                # Remove "Timed Finals" from Heat line
                if line.lower().startswith(("heat")):
                    line = line.replace("Timed Finals", "")
                    
                ## Replace long school name with short name
                for k,v in schoolNameDict.items():
                    line = line.replace(k, v)

                print(  f"{line}" )
                if line.lower().startswith(("heat")):
                    print(  f"{headerLine}" )







if __name__ == "__main__":
    main()