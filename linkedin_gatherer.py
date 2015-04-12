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
parser.add_argument('-u', '--url', help='URL of the search')
parser.add_argument('-o', '--output', help='Output file')
args = parser.parse_args()

def get_search():
    r = requests.get(search, cookies=cookies)
    regex = re.compile("{\"content\":{\"i18n.*?\"ok\"}")
    pagejson = regex.findall(r.text)[0].replace('\u002d1','-1')
    content = json.loads(pagejson)
    people = []
    try:
        pages = content['content']['page']['voltron_unified_search_json']['search']['baseData']['resultPagination']['pages']
        print "[Info] Search found %d page(s)" % len(pages)
        if len(pages) > 0:
            for p in pages:
                print "[Info] Gathering connections from page %d" % p['pageNum']
                people = get_people(search,str(p['pageNum']))
    except:
        print "[Warning] No pagination data found"
        people = get_people(search,str(1))
    return people

def get_people(search,p):
    search += "&page_num="+str(p)
    r = requests.get(search, cookies=cookies)
    regex = re.compile("{\"content\":{\"i18n.*?\"ok\"}")
    pagejson = regex.findall(r.text)[0].replace('\u002d1','-1')
    try:
        content = json.loads(pagejson)
        people = content['content']['page']['voltron_unified_search_json']['search']['results']
    except:
        people = []
    print "[Info] Found %d people" % len(people)
    if len(people) > 0:
        for pl in people:
            firstname = pl['person']['firstName'].encode('utf-8')
            lastname = pl['person']['lastName'].encode('utf-8')
            #if len(lastname) < 3:
                #find = raw_input("Find lastname for %s %s? (Y/n)" % (firstname,lastname))
                #if find == "Y":
                    #lastname = find_lastname(firstname,lastname,company)
            if not firstname=="":
                data = [
                    pl['person']['id'],
                    firstname,
                    lastname,
                    company
                ]
                writer.writerow(data)

def find_lastname(f,l,c):
    searchstring = yahoo_url+"site%slinkedin.com+%s+%s+%s" % ("%3A",f,l,c)
    r = requests.get(searchstring)
    regex = re.compile("1\"><b>(.*?)</a>")
    results = regex.findall(r.text)
    for r in results:
        print "[Found] %s" % r
    lastname = raw_input("Enter the correct last name\n")
    return lastname

def authenticate():
    try:
        session = subprocess.Popen(['python', 'linkedin_login.py'], stdout=subprocess.PIPE).communicate()[0]
        print "[Info] Obtained new session: %s" % session
        cookies = dict(li_at=session)
    except Exception, e:
        sys.exit("[Fatal] Could not authenticate to linkedin. %s" % e)
    return cookies

if __name__ == '__main__':
    base_url = "https://www.linkedin.com"
    yahoo_url = "https://search.yahoo.com/search?p="
    search = args.url if args.url!=None else raw_input("Enter search URL\n")
    company = raw_input("Enter Company Name\n")
    outfile = args.output if args.output!=None else raw_input("Enter filename for output\n")
    cookies = authenticate()
    output = open(outfile,'a+')
    writer = csv.writer(output,quoting=csv.QUOTE_MINIMAL)
    skillset = []
    urls = []
    ## Initialize
    get_search()
