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
