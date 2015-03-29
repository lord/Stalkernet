'''
directory.py
DevX, last updated 10/19/2014

This python script goes over the current stalkernet database (as of 10/19/2014) and then scrapes the
information from each page, placing the information into a .csv file.

You will need to install the requests python library in order to use this program.

Get pip and do the following command to get the library:

$ pip install requests

Run the commands below in the terminal to run the file, and make sure this file is alone in the directory.
It creates everything it will need for operation.

$ cd path/to/this/file
$ python directory.py
'''


# yearless, majorless:
# [u'Michael Shin', u'Jake Reardon', u'Woosik Koong', u'Sipho Mhlanga', u'Chessy Cantrell']


import pickle
import re
import requests
import string
import urllib
import os
from collections import defaultdict

# Global constants.
url = 'http://apps.carleton.edu/campus/directory/'
years = [2015, 2016, 2017, 2018]


# Regular expressions to capture data elements from HTML.
re_person = '<li class="person">(.*?)</li>'
re_name = '<h2>(.*?)</h2>'
re_name_profile = '<h2>[<a href="/profiles/[a-z]+[0-9]?/">]?(.*?)[</a>]*</h2>'
re_year = '<span class="affiliation">(.*?)</span>'
re_major = '<span class="major">(.*?)</span>'
re_concentration = '<span class="concentration">(.*?)</span>'
re_dorm = '<p class="location">.*?<a .*?>(.*?)</a>'
re_email = '<div class="email">.*?<a .*?>(.*?)</a>'
re_phone = '<div class="telephone">.*?<a .*?>(.*?)</a>'
re_address = '<div class="homeAddress">(.*?)</div>'
re_emailcheck = '[a-z]+[0-9]?@carleton.edu'
re_status = '<p class="status">(.*?)</p>'
# this was causing problems for me, but you said it was okay so we shall see
re_photo = 'src="/stock/ldapimage.php?\?id=(.*?)&source=campus_directory"'


def main():
    global d, m, output_file
    try:
        f = open('directory.pickle', 'r')
        d = pickle.load(f)
        f.close()
        print "Directory data loaded."
    except IOError:
        print "Directory data not found, beginning scrape."
        d = get_directory()
        f = open('directory.pickle', 'w')
        pickle.dump(d, f)
        f.close()
        print "Directory data saved."
    if not os.path.exists('stalkernet_images'):
         os.makedirs('stalkernet_images')
    output_file = open('stalkernet_data.csv', 'w')
    get_people(d)
    output_file.close()

def get_people(d):
    m = defaultdict(int)
    counter = 0
    for k in d.iterkeys():
        counter += 1
        name = d[k]['name']
        majors = ' / '.join(d[k]['major'])
        year = d[k]['year']
        dorm = d[k]['dorm']
        floor = d[k]['floor']
        roomNumber = d[k]['roomNumber']
        email = d[k]['photo']
        address = d[k]['address']
        urllib.urlretrieve("https://apps.carleton.edu/stock/ldapimage.php?id=%s&source=campus_directory" %email, "stalkernet_images/%s.jpg" %email)
        output_file.write("%s,%s,%d,%s,%d,%s,%s,\"%s\"\n" %(name, majors, year, dorm, floor, roomNumber, email, address))


def name_of(x):
    name = re.search(re_name, x).groups()[0]
    return re.sub('<.*?>', '', name)


def data_of(x):
    lives_in_dorm = True
    name = re.search(re_name_profile, x)
    if name:
        name = name.groups()[0]
    else:
        name = re.search(re_name, x)
        name = name.groups()[0] if name else None
    major = re.findall(re_major, x)
    concentration = re.findall(re_concentration, x)
    year = re.search(re_year, x)
    try:
      year = int(year.groups()[0]) if year else None
    except ValueError:
      year = None
      
    dorm = re.search(re_dorm, x)
    if dorm:
        dorm = dorm.groups()[0]
    else:
        dorm = re.search(re_status, x)
        if dorm:
            dorm = dorm.groups()[0]
        else:
            dorm = "Unknown"
    if re.match(re_emailcheck, dorm) != None:
        dorm = "Northfield Option"
        lives_in_dorm = False
    email = re.search(re_email, x)
    email = email.groups()[0] if email else None
    phone = re.search(re_phone, x)
    phone = phone.groups()[0] if phone else None
    phone = re.sub('<.*?>', '', phone) if phone else None
    address = re.search(re_address, x)
    address = address.groups()[0] if address else None
    photo = re.search(re_photo, x)
    photo = photo.groups()[0] if photo else None
    if dorm in ["Off Campus Program", "On Leave", "Unknown", "Early Finish"]:
        return None
    if lives_in_dorm:
        # this was crashing because Carleton has some Northfiled option
        # students listed differently. Temporary fix.
        try:
            floor = int(dorm.split()[-1][0])
        except:
            return None
        roomNumber = dorm.split()[-1]
        dorm = (' ').join(dorm.split()[:-1])

    else:
        floor = -1
        roomNumber = "-1"

    return {
        'name': name,
        'major': major,
        'year': year,
        'dorm': dorm,
        'floor': floor,
        'roomNumber': roomNumber,
        'photo': photo,
        'address': address,
    }


def get_directory():
    d = {}
    for y in years:
        for c in string.ascii_lowercase:
            print "Looking up students from the class of %i whose names begin with %s" % (y, c.upper())
            payload = {
                'search_for': 'student',
                'year': y,
                'first_name': c
            }
            add_results(d, payload)
    return d


def add_results(d, payload):
    r = requests.get(url, params=payload)
    s = r.text.replace('\n', '')
    p = re.findall(re_person, s)
    for x in p:
        data = data_of(x)
        if data != None:
            d[name_of(x)] = data


if __name__ == "__main__":
    main()
