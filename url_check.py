# import libraries required for script
# csv used to read/write csv files
# requests issues get request to return html contents
# beautiful soup makes html contents human friendly readable, for testing
import csv
import requests
import time
import os, sys, subprocess
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup

# starting point of script
# calls parse_csv_file to grab urls to be checked
def main():
    create_csv_file()

# create a new csv file, overwrite if it exists
# prompt user to add links to csv file
def create_csv_file():
    file_name = input('What shall this report be named?: ')
    print('creating '+file_name+'_checked.csv file.')
    # open path to csv file
    with open(file_name+'_checked.csv', "w") as f:
        writer = csv.writer(f)
        header = ['BrokenLinks', 'LinkedFromURL']
        writer.writerow(header)

    input('\t1. Add links to corresponding column in '+file_name+'_checked.csv.\n\t2. Save and Close.\n\tPress any key to open csv.file.')
    subprocess.call(['open', file_name+'_checked.csv'])
    input('Press any key to begin checking links')

    parse_csv_file(file_name)

# open url_check.csv and parse data into absolute_url and linked_from_url
# absolute_url contains list of AbsoluteURL from url_check.csv
# linked_from_url contains list of LinkedFromURL from url_check.csv
# pass this data into check_url
def parse_csv_file(file_name):
    # variable declarations
    broken_links_url = []
    linked_from_url = []
    #open the url_check.csv file and store contents in csv_file_contents
    with open(file_name+'_checked.csv', newline='',  encoding='utf-8-sig') as csv_file:
        csv_file_contents = csv.DictReader(csv_file)
        #parse through sv_file_contents and store AbsoluteURL/LinkedFromURL in
        #absolute_url, linked_from_url
        for row in csv_file_contents:
            broken_links_url.append(row['BrokenLinks'])
            linked_from_url.append(row['LinkedFromURL'])
    #call get_url_html and pass url lists as parameters
    #get_url_html issues get requests for linked_from_url
    get_url_html(file_name, broken_links_url,linked_from_url)

# issue get requests on linked_from_url links
# pass html content into
def get_url_html(file_name, broken_links_url, linked_from_url):
    # Variables declarations
    url_results = []
    url_status = []
    url_message = []
    url_response_code = []
    url_time_elapsed = []

    url_metadata = {
        'rows_examined': 0,
        'links_processed': 0,
        'empty_links': 0,
        'connection_errors': 0,
        'time_out_errors': 0,
        'invalid_schema_errors': 0,
        'missing_schema_errors': 0,
        'inactive': 0,
        'unavailable': 0,
        'page_moved': 0,
        'response_code_changes': 0,
        'pdf_links': 0,
        'unknown_errors': 0
    }
    false_negatives = ['Sorry, the page is inactive or protected.', 'This page is currently unavailable.', 'This page has moved.']

    # set a user_agent to include for get request
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.90 Safari/537.36'}
    # loop through list of linked_from_url and issue get requests
    for broken_url, linked_url in zip(broken_links_url, linked_from_url):
        # metadata - increment rows checked
        url_metadata['rows_examined'] +=1
        print(str(url_metadata['rows_examined'])+'. ', end='')
        #start time get request completion
        start = time.time()
        # if absolute_url/linked_from_url are empty
        # update url_status to False
        # increment url_metadata['empty_links']
        # add missing link message
        if not broken_url or not linked_url:
            print("BrokenLinks/LinkedFromURL is empty")
            url_status.append('No')
            url_response_code.append('n/a')
            url_metadata['empty_links'] +=1
            url_message.append('BrokenLinks/LinkedFromURL is empty')
        # else attempt to issue get request
        else:
            try:
                # issue get request with a timeout of 5 seconds
                # if success call check_url_html and append result to
                # if fails hopefully exception catches it
                response = requests.get(linked_url, headers=headers, timeout=5)
                # add response.status_code to url_response_code list
                url_response_code.append(response.status_code)
                # call check_url_html with arguments:
                # response.text contains url html url_contents
                # abs_url contains link to be searched for in response.text
                # append results to url_status
                url_status.append(check_url_html([response.text, broken_url, linked_url]))
                # if check_url_html returns no then check to see if html contents of the LinkedFromURL contains inactive/unavailable/moved content
                # if yes then update the response.status code to c404
                # increment inactive/unavailable fields
                if (url_status[-1] is 'no'):
                    if (false_negatives[0].lower() in response.text.lower()):
                        url_response_code[-1] = 'c404'
                        url_metadata['inactive'] +=1
                        url_metadata['response_code_changes'] +=1
                        url_message.append('LinkedFromURL reports inactive')
                    elif (false_negatives[1].lower() in response.text.lower()):
                        url_response_code[-1] = 'c404'
                        url_metadata['unavailable'] += 1
                        url_metadata['response_code_changes'] +=1
                        url_message.append('LinkedFromURL reports unavailable')
                    elif (false_negatives[2].lower() in response.text.lower()):
                        url_response_code[-1] = 'c404'
                        url_metadata['page_moved'] += 1
                        url_metadata['response_code_changes'] +=1
                        url_message.append('LinkedFromURL reports page moved.')
                elif (url_status[-1] is 'yes'):
                    if('DomainID = ' in response.text):
                        print('DomainID was found')
                    else:
                        print('DomainID')
                else:
                    url_message.append('LinkedFromURL successfully processed')

                print('Found:', url_status[-1], 'Status code:',url_response_code[-1], 'BrokenLinks:', broken_url, 'LinkedFromURL:', response.url)
                # increment url_metadata['links_processed']
                # add LinkedFromURL successfully processed message
                url_metadata['links_processed'] +=1


            #throws connectionError exception when get LinkedFromURL fails
            # increment metadata error counter
            # update url_status
            # add error message
            except requests.exceptions.ConnectionError:
                print("BrokenLinks:", url_status[-1],'Connection error. Check LinkedFromURL on web browser. LinkedFromURL:',linked_url)
                url_status.append('No')
                url_response_code.append('n/a')
                url_metadata['connection_errors'] +=1
                url_message.append('Connection error. Check LinkedFromURL on web browser.')
            #throws invalidSchema exception when LinkedFromURL protocol is invalid
            # increment metadata error counter
            # update url_status
            # add error message
            except requests.exceptions.InvalidSchema:
                print("BrokenLinks:", url_status[-1],'Invalid schema error. Check LinkedFromURL protocol/format. LinkedFromURL:',linked_url)
                url_status.append('No')
                url_response_code.append('n/a')
                url_metadata['invalid_schema_errors'] +=1
                url_message.append('Invalid schema error. Check LinkedFromURL protocol/format.')
            #throws missingSchema exception when LinkedFromURL schema is invalidSchema
            # increment metadata error counter
            # update url_status
            # add error message
            except requests.exceptions.MissingSchema:
                print("BrokenLinks:", url_status[-1],'Missing schema error. Check LinkedFromURL format, might be empty. LinkedFromURL:',linked_url)
                url_status.append('No')
                url_response_code.append('n/a')
                url_metadata['missing_schema_errors'] +=1
                url_message.append('Missing schema error. Check LinkedFromURL format, might be empty.')
            #throws retryError exception when a get takes longer than specified timeout field.
            # increment metadata error counter
            # update url_status
            # add error message
            except requests.exceptions.RequestException:
                print("BrokenLinks:", url_status[-1],'Read Timeout error. The connection timed out after waiting 10 seconds LinkedFromURL:',linked_url)
                url_status.append('No')
                url_response_code.append('n/a')
                url_metadata['time_out_errors'] +=1
                url_message.append('Read Timeout error. The connection timed out after waiting 10 seconds.')

            # throws catch all exception for all other errors
            # increment metadata error counter
            # update url_status
            # add error message
            except Exception as e:
                print("BrokenLinks:", url_status[-1],'Caught unknown error.', e, 'LinkedFromURL:',linked_url)
                url_status.append('No')
                url_response_code.append('n/a')
                url_metadata['unknown_errors'] +=1
                url_message.append('Unkown error occured, check LinkedFromURL.')

        # end time get request completion
        # append time elapsed to url_time_elapsed
        end = time.time()
        url_time_elapsed.append(end-start)

    # FOR TESTING PURPOSES
    # call display_results to print the status of processed urls with argument url_status
    # url_status contains results of absolute_url comparison in linked_from_url html
    # url_metadata contains metadata regarding errors raised during attempted get request
    # url_time_elapsed contains time to complete get request for links
    display_results(url_status, url_metadata, sum(url_time_elapsed), url_response_code)

    # call write_reports to generate csv file with results of processed links_processed
    # absolute_url contains list of AbsoluteURL obtained from csv_file
    # linked_from_url contains list of LinkedFromURL obtained from csv_file
    # url_status contains list of True/False fields for abs_url Found
    # url_response_code contains list of http response codes
    # url_message contains list of messages about processing of LinkedFromURL
    # url_time_elapsed contains list of time to completion for get request of LinkedFromURL
    write_reports(file_name, broken_links_url, linked_from_url, url_status, url_response_code, url_message, url_time_elapsed)

# compare html content of the processes linked_from_url to the absolute_url
# url_contents[0] contains html contents
# url_contents[1] contains broken_url
# url_contents[2] contains linked_from_url
# if broken_link exists then flag as yes linked found
# if broken_link does not exist then do detailed checked:
#   1. check if broken_link text exists anywhere on page, if yes flag no
#   2. check if broken_link contains & symbol. if yes replace with html friendly amp; and recheck
def check_url_html(url_contents):
    if(url_contents[1].lower() in url_contents[0].lower()):
        print('FIRST CHECK')
        return 'yes'
    elif('&' in url_contents[1].lower()):
        if(url_contents[1].replace('&', '&amp;').lower() in url_contents[0].lower()):
            return 'yes'

    elif('../' in url_contents[0].lower() or '..\\' in url_contents[0].lower()):
        print('DOUBLECHECK')
        # split linked_from_url by '/' delimeter
        # loop through list of href that are relative path for each href
        # noramlize the urls
        # store results in broken_relative_url list
        broken_relative_url = []
        soup = BeautifulSoup(url_contents[0], 'html.parser').findAll('a')
        for link in soup:
            if link.get('href'):
                if('../' in link.get('href') or '..\\' in link.get('href')):
                    normalized_url = link.get('href').replace('\\','/')
                    broken_relative_url.append(normalized_url)

        # build absolute url of broken_links_url
        # get levels of url by examining number of '../'
        # remove relative reference in url
        # use directory_level determined to go up directory of LinkedFromURL
        absolute_urls = []
        for url in broken_relative_url:
            linked_from_url = url_contents[2].lower().split('/')
            directory_level = url.count('../') +1
            url = url.split('/')
            url = [i for i in url if i != '..']
            linked_from_url = linked_from_url[0:len(linked_from_url)-directory_level]
            linked_from_url = [i for i in linked_from_url if i]
            linked_from_url[0] += '/'
            absolute_urls.append('/'.join(linked_from_url+url).lower())

        if(url_contents[1].lower() in absolute_urls):
            return 'yes'

    elif('/' not in BeautifulSoup(url_contents[0], 'html.parser').findAll('a')):
        print('THIRD CHECK')
        broken_relative_url = []
        soup = BeautifulSoup(url_contents[0], 'html.parser').findAll('a')

        for link in soup:
            if link.get('href'):
                if '/' not in link.get('href'):
                    broken_relative_url.append(link.get('href'))

        absolute_urls = []

        domain_url = url_contents[2].split('/')[0:-1]

        for url in broken_relative_url:
            built_absolute_url = ('/'.join(domain_url)+'/'+url)
            absolute_urls.append(built_absolute_url.lower())

        if url_contents[1].lower() in absolute_urls:
            return 'yes'
    return 'no'

def display_results(url_status, url_metadata, total_time_elapsed, url_response_code):
    print('\nResults')
    print('========================================================')
    print('Time elapsed: %.2f seconds' % (total_time_elapsed))
    print('Total Links Examined:', url_metadata['rows_examined'])
    print('Links processed:', url_metadata['links_processed'])
    print('\tNumber of Links found:', url_status.count('yes'))
    print('\tNumber of Links NOT found:', (url_status.count('no')+url_status.count('n/a')))
    print('\tNumber of ACTUAL 404 Links:', url_response_code.count(404))
    print('\tNumber of CHANGED 404 Links:', url_response_code.count('c404'))
    print('\tPercent of Links found:', '{:.2%}'.format(url_status.count('yes')/len(url_status)))
    print('\tPercent of ACTUAL 404 Links:', '{:.2%}'.format(url_response_code.count(404)/len(url_status)))
    print('\tPercent of CHANGED 404 Links:', '{:.2%}'.format(url_response_code.count('c404')/len(url_status)))
    print('\tPercent of Links NOT found (errors/empty):', '{:.2%}'.format(url_response_code.count('n/a')/len(url_status)))
    print('Connection errors processed:', url_metadata['connection_errors'])
    print('Read timeout errors processed:', url_metadata['time_out_errors'])
    print('Invalid schema errors processed:', url_metadata['invalid_schema_errors'])
    print('Missing schema errors processed:', url_metadata['missing_schema_errors'])
    print('Unknown errors processed:', url_metadata['unknown_errors'])
    print('Empty Links processed:', url_metadata['empty_links'])
    print('Page Inactive Links processed:', url_metadata['inactive'])
    print('Page Unavailable Links processed:', url_metadata['unavailable'])
    print('Page Moved Links processed:', url_metadata['page_moved'])
    print('\tTotal Number of Inactive/Unavailable Links processed:', url_metadata['response_code_changes'])
    print('\tPercent Link response codes changed:', '{:.2%}'.format(url_metadata['response_code_changes']/len(url_status)))
    print('========================================================')

# write report to csv file
# absolute_url contains list of AbsoluteURL obtained from csv_file
# linked_from_url contains list of LinkedFromURL obtained from csv_file
# url_status contains list of True/False fields for abs_url Found
# url_response_code contains list of http response codes
# url_message contains list of messages about processing of LinkedFromURL
# url_time_elapsed contains list of time to completion for get request of LinkedFromURL
def write_reports(file_name, broken_links_url, linked_urls, url_status, url_response_code, url_message, url_time_elapsed,):
    print('generating reports:'+file_name+'_report.csv')
    # format time elapsed to 2 decimal points
    time_elapsed = ["%.2f" % time for time in url_time_elapsed]
    rows = zip(broken_links_url, linked_urls, url_status, url_response_code, url_message, time_elapsed)
    # open path to csv file
    with open(file_name+'_report.csv', "w") as f:
        writer = csv.writer(f)
        header = ['BrokenLinks', 'LinkedFromURL', 'BrokenLinks Found?', 'Response Code', 'Details', 'Time Elapsed(sec)']
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)

# main method
if __name__ == '__main__':
    main()