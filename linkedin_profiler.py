#!/usr/bin/python

__author__ = 'Danny Chrastil'
__email__ = 'danny.chrastil@hp.com'
__version__ = '0.1'

import sys
import re
import time
import csv
import json
import argparse
import requests
import subprocess
from thready import threaded

""" Setup Argument Parameters """
parser = argparse.ArgumentParser(description='Discovery LinkedIn')
parser.add_argument('-d', '--data', help='Input data file')
parser.add_argument('-o', '--output', help='Output file')
args = parser.parse_args()

def get_profile(lid,fname,lname,comp,tcount,ccount):
    ## Grab the target profile
    global rID, targetname
    profile = base_url+"/profile/view?id=%s" % lid
    r = requests.get(profile, cookies=cookies)
    #regex1 = re.compile("fmt__skill_name\":\"(.*?)\"") # Skill Names
    regex1 = re.compile("endorse-item-name-text\">(.*?)<") # Skill Names
    regex2 = re.compile("recipientId:(.*?),") # Recipient ID
    regex3 = re.compile("<title[^>]*>(.*?)\s\|") # Target Name
    print "\r[Info] Gathering data for %s %s (%d/%d)" % (fname,lname,ccount,tcount)
    try:
        ## Get RequestorID and Name of target
        rID = regex2.search(r.text).groups()[0]
        targetname = regex3.search(r.text).groups()[0]
    except:
        ## Target is outside of your network. Grabbing authToken value
        print "[Info] Target is outside your network. Optaining auth token."
        authToken = get_authToken(fname,lname,comp)
        targetname = fname + " " + lname
        ## Resend request with authToken
        profile2 = profile + "&authType=NAME_SEARCH&authToken=%s" % authToken
        r = requests.get(profile2, cookies=cookies)
        try:
            rID = regex2.search(r.text).groups()[0]
        except:
            print "\n[Error] Skipping %s %s" % (fname,lname)
            print "[Error] Unable to view the targets full profile\n"
    print targetname
    ## Get the skills of the target
    rID = rID.replace("'","")
    skills = set(regex1.findall(r.text))
    if skills:
        for s in skills:
            skillset.append(s)
            #get_endorsements(s)
    else:
        print "\n[Error] Could not find skill names. Check that the session is still valid"

    ## Send requests to the threading engine
    threaded(skillset, get_endorsements, num_threads=10)

def get_authToken(f,l,c):
    global cookies
    ## Peforms a NAMED_SEARCH to obtain an authToken
    auth_url = base_url + "/vsearch/p?firstName=%s&lastName=%s&company=%s" % (f,l,c)
    r = requests.get(auth_url, cookies=cookies)
    regex = re.compile("authToken\":\"(.*?)\"")
    try:
        authToken = regex.findall(r.text)[0].replace('\u002d','-')
        print "Found auth token: %s" % authToken
    except:
        print "\n[Warning] Session has been terminated. Attempting to get a new session..."
        print "[Info] Sleeping for %d seconds" % timeout
        time.sleep(timeout)
        cookies = authenticate()
        authToken = get_authToken(f,l,c)
    return authToken

def get_endorsements(skill):
    ## Grab all endorsement data to determine connections
    skill_url = base_url + "/profile/endorser-info-dialog?recipientId=%s&isV2Dialog=true&skillName=%s" % (rID, skill)
    r = requests.get(skill_url, cookies=cookies)
    sys.exit
    endorsements = json.loads(r.text)['content']['endorser_info_dialog']['endorsers']
    if len(endorsements) > 0:
        print "Gathering connections for %s: (found %s)" % (skill,len(endorsements))
        for e in endorsements:
            headline = e['headline'].split(' at ')
            title = headline[0] if headline[0]!=None else ""
            company = headline[1] if len(headline)>1 else ""
            data = [
                targetname.encode('utf-8'),
                e['fullName'].encode('utf-8'),
                title.encode('utf-8'),
                company.encode('utf-8'),
                e['profileURL'],
                e['locationString'].encode('utf-8'),
                e['memberID']
            ]
            ## Write to CSV output
            writer.writerow(data)

def authenticate():
    try:
        session = subprocess.Popen(['python', 'linkedin_login.py'], stdout=subprocess.PIPE).communicate()[0]
        print "[Info] Obtained new session: %s" % session
        cookies = dict(li_at=session)
    except:
        sys.exit("[Fatal] Could not authenticate to linkedin.")
    return cookies

if __name__ == '__main__':
    base_url = "https://www.linkedin.com"
    datafile = args.data if args.data!=None else raw_input("Input data file\n")
    outfile = args.output if args.output!=None else raw_input("Enter filename for output\n")
    cookies = authenticate()
    output = open(outfile,'a+')
    timeout = 20
    writer = csv.writer(output,quoting=csv.QUOTE_MINIMAL)
    skillset = []
    urls = []
    ## Initialize
    try:
        f = open(datafile)
    except Exception, e:
        print "[Error] %s" % str(e)
    else:
        data = [line.rstrip() for line in f]

    count = 0
    people = sorted(set(data))
    for person in people:
        count += 1
        person = person.split(',')
        if len(person[2]) > 2:
            get_profile(person[0],person[1],person[2],person[3],len(people),count)
        else:
            print "\n[Info] Skipped %s %s" % (person[1],person[2])
        print "[Info] - Sleeping for 60 seconds"
        time.sleep(60)
