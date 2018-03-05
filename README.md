# lausd-website-cleanup
This script will check for existence of a link in a given webpage from user input.

## To Run Script
### Ensure Python >3 is installed 

```
> git clone https://github.com/Christriane/lausd-website-cleanup.git
> cd url_check.py
> python3 url_check.py [parameters]
``` 

## Available Parameters
1. -id : will attempt to find DomainId of a webpage. Only available on Achieve webpages. 
2. -d  : will attempt to retrieve the last modified value from header. 
### To use parameter 
```
> python3 url_check.py -id -d
```

## Execution
The script has a prompt that you can follow. It will generate a csv file with headings BrokenLink, LinkedFromURL, 
Domain, Proposed Owner, Owner Home Page. Add the information to this csv file, save and close. Then press any key
on the prompt to continue.
1. BrokenLink: Mandatory. Place link to be searched in the html
2. LinkedFromURL: Mandatory. Place link with html to be searched.
3. Domain: Optional. Place originating source. e.g. K12, Achieve, Home.
4. Proposed Owner: Optional. If known, place owner name. Intended for data we already manually added.
5. Ownder Homepage: Optional. If known, place owner homepage. Intended for data we already manually added.

Once the script has finished executing, you will be presented with a summary of results and a new csv file with the 
name provided earlier will appear. this file will be named: nameProvided_master.csv This file contains the generated data.

## Note
This script is lacking in validation checks on the user end. Plans to add this are set but in the mean time, 
If an error is thrown, make sure that all mandatory fields are provided. 

