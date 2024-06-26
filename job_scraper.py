# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup as BS
import re
from datetime import date
import os
import webbrowser
import shutil
import web_tools as webt
import db_tools
import interface_tools


# Ask user whether to open search results in a webbrowser or to finish the programme
def open_results(city):
    user_input = input('>>> Do you want to open the search results in your web browser? Type "1" for yes. Type "2" to finish.\n')
    if user_input == "1":
        webbrowser.open('file://' + os.getcwd() + f'/results/jobs_{city}.html')
        exit()
    elif user_input == "2":
        exit()
    else:
        os.system('clear') 
        print('''>>> Wrong input!\n''')
        open_results(city)


interface = interface_tools.InterfaceTools()
city = interface.get_city()
print(f'>>> Searching for new jobs in {city}\n')

ads = []
ad_date = date.today().strftime('%Y-%m-%d')

db = db_tools.DbTools()
db.db_connection()
db.create_table()


# KULTtweet
url = 'https://www.kultweet.de/jobs.php'
method = 'post'
payload = {
    'data' : city,
    'Suchen' : 'Jobs+finden'
}
content = webt.post(url=url, payload=payload)
if content:
    jobs = content.find_all('li', class_=re.compile(r'row'))  # Look for 'li' tags. They contain the job ad text and link.
    for job in jobs:
        job.a.string = job.a.text.replace('\n', ' ')
        job.a['href'] = job.a['href'].replace(' ', '+')
        ads.append(webt.create_ad(job=job, city=city, entry_date=ad_date))

db.insert_data(data=ads)

db.get_new_entries(entry_date=ad_date)

exit()

# Jobforum Kultur
payload = {'s': city}
content = open_html('https://jobforum-kultur.eu/', 'get', payload)
jobs = content.find_all(r'article')  # Look for 'article' tags. They contain the job ad text and link.
for job in jobs:
    write_file()


# GoodJobs / link= set filter to 100 results
payload = {
    'search': None,
    'search_type': None,
    'places': city,
    'distance': '10',
    'places_type': None,
    'countrycode': None,
    'state': None,
    'latlng': None,
    'num': '100'  # Set to 100 results per page.
}
content = open_html('https://goodjobs.eu/jobs', 'get', payload)
jobs = content.find_all('a', class_='jobcard')  # Look for 'a' tags with 'class='jobcard'' attribute. They contain the job ad text and link.

for job in jobs:
    job = job.parent  # Return parent tag of 'a' tag. Necessary to make write_file() work, because it expects a format where a is not the parent tag.

    tags = job.a.find_all('p', class_=re.compile('label-text'))  # The ad text is spread across various attributes. Appends all text fragments to the 'h3' tag.
    for tag in tags:
        job.h3.append(', ' + tag.text.strip())  # The ad text is spread across various attributes. Appends all text fragments to the 'h3' tag.
        tag.decompose()

    tags = job.find_all('span')  # Delete 'span' attributes that contain unwanted text.
    for tag in tags:
        tag.decompose()
    write_file()


# epojobs / Infos zum Arbeitgeber fehlen
payload = {
	"filter-search": "Köln",
	"limit": "30",
	"filter_order": "",
	"filter_order_Dir": "",
	"limitstart": "",
	"task": ""
}
content = open_html('https://www.epojobs.de/', 'post', payload)
jobs = content.find_all(class_=re.compile('cat-list-row'))
for job in jobs:
    full_text = job.text
    replace_tag = job.a
    replace_tag.string = full_text
    link = job.a['href']
    job.a['href'] = 'https://epojobs.de'+link  
    write_file()


# Wila Arbeitsmarkt
for x in range(1,11):  # How to not hard code '11'?
    content = open_html('https://www.wila-arbeitsmarkt.de/stellenanzeigen/?sortby=angebote_plz&sort=ASC&page='+str(x), 'get')
    jobs = content.find_all('td', string = re.compile('^50|^510|^511'))
    for job in jobs:
        job = job.find_parent('tr')
        full_text = job.text
        replace_tag = job.a
        replace_tag.string = full_text
        link = job.a['href']
        job.a['href'] = 'https://www.wila-arbeitsmarkt.de' + link
        write_file()


# Stadt Koeln
content = open_html('https://www.stadt-koeln.de/politik-und-verwaltung/ausbildung-karriere-bei-der-stadt/stellenangebote/wissenschaft-kultur', 'get')
jobs = content.find_all('ul', id=re.compile('ziel'))
for job in jobs:
    jobs = job.find_all('li')
    for job in jobs:
        link = job.a['href']
        job.a['href'] = 'https://www.stadt-koeln.de/'+link  
        write_file()

 
print('>>> New file created...\n')
        
open_results(city)