
#Portions of a python script written to call the Logrythm API from the command line. 

#!/usr/bin/env python3

import requests
import json
import time
import os


from datetime import date

#This Script is for running LogRhythm searches from the command line


#This suppresses noisy warnings produced by requests.post. verify=False is currently set to avoid SSL verification but that should probably be addressed at some point :)
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



#These lines read in the API Auth key. kept in a plaintext file that is not included in the repository
with open('[REDACTED](filename)', 'r') as apikey:
        API_key = apikey.read().replace('\n', '')



#This function takes as input a taskid as a string, and returns a list of python dectionaries, each dictionary being a log
def get_response(taskid):

        resultURL = "[REDACTED](URL)"
        #dict of headers
        headers = {"Accept": "application/json", "Content-Type": "application/json;charset=utf-8", "Authorization": API_key}

        #I've split the json object into two strings that can be "wrapped around" the task id (as a string) to create a json object to send
        json1 = '{ "data": { "searchGuid": "'
        json2 = '", "search": {"sort": [],"groupBy": null,"fields": []},"paginator": {"origin": 1,"page_size": 100}}}'
        jsonstr = json1 + taskid + json2

        #make the call
        response = requests.post( resultURL, headers=headers, verify=False, json=jsonstr )

        response_json = json.loads(response.text) #turns raw data into a dictionary


        #loop to wait untill the search has completed, the loop waits 5 seconds before trying again
        while response_json['TaskStatus'] == 'Searching' or response_json['TaskStatus'] == 'First Results':
                print('Search Status: ' + response_json['TaskStatus'])
                time.sleep(5)
                response = requests.post( resultURL, verify=False, headers=headers, json=jsonstr )
                response_json = json.loads(response.text) #turns raw data into a dictionary


        #There are a few different fields that seem like they should give the "task status" I think this one (TaskStatus) gives the most useful info
        print('Task status: ' + response_json['TaskStatus'])
        status = response_json["StatusCode"]

        #200 exit code means the search was succesfull, otherwise print a message and the exit code
        if int(status) == 200:
                return response_json['Items']

        else:
                warning_message = "The search was not succesfull, status code:  "
                print(warning_message + str(status))
                return 0



#method for creating a filter Item, this is a "sub-method" of create_json.
def make_filterItem( identikey = None, Port = None , IP = None):

        values_list = []

        #values that shouldn't change between filters
        filterItemType = 0 #options are 0: filter, 1: group, 2: Polylist. Not sure what this changes
        fieldOperator = 2 #Logical Operator to be applied between fields, (by fields I think it means values in the values list). 0=None, 1=AND, 2=OR
        filterMode = 1  # 1 = filterIn, 2 = FilterOut

        if identikey:

                email = identikey + '@colorado.edu'
                filterType = 29
                valueType = 4

                #Value objects, are added to values list
                value_dict1 = { 'value': identikey, 'matchType': 0 }

                value_dict2 = { 'value': email, 'matchType': 0 }

                name = "User (Origin or Impacted)"

                values_list.append( { "filterType": filterType, "valueType": valueType, "value": value_dict1, "displayValue": identikey } )
                values_list.append( { "filterType": filterType, "valueType": valueType, "value": value_dict2, "displayValue": email } )

        #have not got the json syntax for these yet
        if Port:
                pass
        if IP:
                pass

        ret_dict = { "filterItemType": filterItemType, "fieldOperator": fieldOperator, "filterMode": filterMode, "filterType": filterType, "values": values_list, "name": name }

        return ret_dict

#method for creating a json search object with the given parameters.
#NOTE: port and IP have not been implimented
#INPUTS formats:
# identikey, dateMin, dateMax = string
# IntervalUnit, IntervalValue, Port = int
#
def create_json( identikey = None, dateMin = None, dateMax = None, IntervalUnit = 4, IntervalValue = 3, Port = None, IP = None ):


        #Parameters       Parameters that shouldn't need to be changed ever are hard-coded (based on my best guess)
        #Outermost json layer parameters
        maxMsgsToQuery = 3000
        queryTimeout = 60
        queryRawLog = "true"

        #parameters used in queryFilter (second to outermost layer)
        msgFilterType = "Grouped"

        #parameters used in filterGroup (third to outermost layer)
        fieldOperator = "AND"
        filterGroupOperator = "AND"


        #initialize lists
        #for filterItems, ideally you could just append whatever search criteria filterItems( created with make_filterItem() ) you want to this list and they would be ANDed together
        datelst = []
        queryLogSources = []
        filterItems = []


        # create date criteria, if using daterange you must provide both dateMin and dateMax. If no date criteria are given as input it defaults to the last 3 days
        if dateMin and dateMax:
                dateCriteria = { "dateMin": dateMin, "dateMax": dateMax, "useInsertedDate": true }
        else:
                dateCriteria = { "lastIntervalValue": IntervalValue,"lastIntervalUnit": IntervalUnit }




        #NOTE This searches for both the plain identikey aswell as the email corresponding to the identikey
        if identikey:
                filterItems.append( make_filterItem(identikey= identikey) )

        #These don't work as i havent found the right json syntax
        if Port:
                filterItems.append( make_filterItem( Port= Port ) )

        if IP:
                filterItems.append( make_filterItem( IP = IP ) )


        #third highest level json obj
        filterGroup = { "filterItemType": "Group", "fieldOperator": fieldOperator, "filterMode": "FilterIn", "filterGroupOperator": filterGroupOperator, "filterItems": filterItems, "name": "filterGroup" }

        #second highest level json obj ( tied with date criteria)
        queryFilter = { "msgFilterType": msgFilterType, "filterGroup": filterGroup }

        #highest level json obj
        json_obj = { "maxMsgsToQuery": maxMsgsToQuery, "queryTimeout": queryTimeout, "queryRawLog": queryRawLog, "queryEventManager": "false", "includeDiagnosticEvents": "true", "searchMode": "pagedSortedDateAsc", "dateCriteria": dateCriteria, "queryLogSources": queryLogSources, "queryFilter": queryFilter }

        return json_obj

#method for completing a search given a json object as a python dictionary
def do_search(jsonobj, saveOutput = False):

        requestURL = "[REDACTED](URL)"

        headers = {"Accept": "application/json", "Content-Type": "application/json;charset=utf-8", "Authorization": API_key}

        response = requests.post( requestURL, headers=headers, verify=False, json = json.dumps(jsonobj) )

        #format json response from text -> dictionary
        search_status = json.loads(response.text)

        #extract task id
        taskid = search_status['TaskId']

        #call get_response method to get log results from taskid
        results = get_response(taskid)

        print('Number of logs returned by search:  ' + str(len(results)))

        #For saving the output
        #NOTE this saves only the logs from the output and not the whole json obj ( because thats what get_response returns)

        out_file_name = date.today().strftime("%Y-%m-%d") + '-outputLogs.json'
        file_counter = 0
        if os.path.isfile(out_file_name):
                while(os.path.isfile(out_file_name)):
                        file_counter += 1
                        out_file_name = date.today().strftime("%Y-%m-%d") + '-outputLogs' + str(file_counter) + '.json'
        print(out_file_name)

        if saveOutput:
                with open( out_file_name, "w" ) as output_file:
                        output_file.write( str(json.dumps(results)) )
        return results

def main():


        testid = '4253696e-40d0-4126-9046-c3a2876558c0'

        #responselst = get_response(testid)

        #print('type check 2:  ' + str(type(responselst)))

        #print('Number of logs returned by search:  ' + str(len(responselst)))

        user_identikey = "[REDACTED]"

        response = do_search( create_json( identikey= user_identikey ), saveOutput= True )




if '__main__' == '__main__':
    main()







#Script for taking cred dumps and checking user passwords to see if the account is now compramised.







#!/usr/bin/env python3
import subprocess
import re
import csv
import os
import codecs
import time
import shlex
import sys
#==INFO===
#this script will takes in a csv with user credentials and runs ldapsearch to determine their validity
#the csv filename should be the first argument eg /home/giol2710exc/ldap_csv/input
#
#IMPORTANT: this script assumes no header in the input csv
#
#the second argument governs which results are logged in the output file. Any input containing a Y will cause only valid credentials to be stored. Leaving this second argument blank or putting somethinig without a y will cause all results to be logged
#12/2 fixed: failure to process passwords with quotes/spaces, failure to process first line of file, crashing when lines are left blank
#
#


email=('email@colorado.edu')
password=('password1!')
identikey=('4letter4number_unless_your_old')
valid=('yes')
csv1=0
time2 = time.strftime('%Y-%m-%d')
valids=False

#this function tests an emails validity and extracts the identikey
def email2identikey(email,password):
    print("Testing email validity and extracting identikey:", email)
    output = subprocess.check_output(['ldapsearch -x -H [REDACTED](URL) -b "ou=users,dc=colorado,dc=edu" mailalternateaddress=' + email], universal_newlines=True, stderr = subprocess.STDOUT, shell=True)
    data1=re.search("uid=(.*),ou",output)
    #searches for username in ldapsearch output, if not found username just set to invalid user
    global identikey
    try:
        identikey=data1.group(1)
    except:
        identikey='invalid_user'
    print("Login:",identikey)


#this function takes an identikey and password and outputs a boolean var for validity
def identikey_password_check(identikey,password):
        print("Testing credentials for uid:" + identikey)
        #creates list of commands to feed into check_output to run ldap
        searchstrlst = [REDACTED]
        #try/except statement circumvents ldapsearch's non 0 exit status, which otherwise creates an exception. So in practice i think this raises the exception everytime, could definately be improved
        try:
                output=subprocess.check_output(searchstrlst, universal_newlines=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
                output = e.output
        data1=re.search("result: 50 Insufficient access", output)
        #output searched for string which appears only when creds are valid
        if data1:
                valid=('yes')
                localvalid = True
        else:
                valid=('no')
                localvalid = False
        print('Is the user valid?', valid)
        #function returns boolean validity var
        return localvalid

def write2csv(identikey,email,password,tfvalid,valids):
        global csv1
        global time2
        #print("before csv:", csv1)
        with open(time2+'_resultstest.csv', 'a', newline='') as outputfile:
                fieldnames = ['identikey', 'email','password', 'valid']
                output = csv.DictWriter(outputfile, fieldnames=fieldnames)
                output.writerow({'identikey': identikey, 'email': email, 'password':password, 'valid': tfvalid})
                outputfile.close()

def main():
        global valids
        #try statement to handle csv as first argument
        try:
                csvfilename = sys.argv[1]
        except:
                print('please include the csv name as the first argument')

        #try statement to check existance/validity of second argument, must only include a y to trigger valid-user-only logging
        try:
                if (re.search('y', sys.argv[2]) or re.search('Y', sys.argv[2])):
                        print('logging only valid credentials')
                        valids = True
                else:
                        print('logging all results')
                        valids = False
        except:
                print('logging all results')

        with codecs.open(csvfilename,'r','UTF-8') as csvfile:
                #use csv parser
                reader=csv.reader(csvfile)
                #skip the header row - 12/2 commenting this out as I don't think these csvs will ever have header rows.
                #next(reader)
                for row in reader:
                        #this try statement is for if a row is left empty in the input csv, the except simply skips this iteration
                        try:
                                row[0]
                        except:
                                continue
                        email=row[0]
                        password=row[1]
                        email2identikey(email,password)
                        idenvalidity = identikey_password_check(identikey,password)
                        if valids and idenvalidity:
                                write2csv(identikey,email,password,idenvalidity,valids)
                        elif not(valids):
                                write2csv(identikey,email,password,idenvalidity,valids)

if '__main__' == '__main__':
    main()
