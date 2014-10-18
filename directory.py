'''
directory.py
DevX, 10/18/2014

This python script goes over the current stalkernet database and then scrapes the information from each page,
placing the information into a .csv file.

You will need to install the requests python library in order to use this program. Get pip and do the following command to get the program:

$ pip install requests

Make sure to create a stalkernet_images directory in the same directory as this file when you run the commands below in order to get
the pictures and avoid errors.

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
re_nofo = '<p class="location">.*?Northfield MN?.*</p>'
re_email = '<div class="email">.*?<a .*?>(.*?)</a>'
re_status = '<p class="status">(.*?)</p>'
re_photo = 'src="/stock/ldapimage.php\?id=(.*?)&source=campus_directory"'


def main():
    global d, m
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
    get_people(d)

def get_people(d):
    m = defaultdict(int)
    for k in d.iterkeys():
        name = d[k]['name']
        majors = ' / '.join(d[k]['major'])
        year = d[k]['year']
        dorm = d[k]['dorm']
        floor = d[k]['floor']
        photo = d[k]['photo']
        urllib.urlretrieve("https://apps.carleton.edu/stock/ldapimage.php?id=%s&source=campus_directory" %photo, "stalkernet_images/%s.jpg" %photo)
        #I think you need this? I forget how I did it before
        print "%s, %s, %d, %s, %d, %s.jpg" %(name, majors, year, dorm, floor, photo)

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
    year = int(year.groups()[0]) if year else None
    dorm = re.search(re_dorm, x)
    if dorm:
        dorm = dorm.groups()[0]
        floor = int(dorm.split()[-1][0])
        dorm = (' ').join(dorm.split()[:-1])
    elif re.match(re_nofo, x) != None:
        dorm = "Northfield Option"
        floor = -1
    else:
        return None
    email = re.search(re_email, x)
    email = email.groups()[0] if email else None
    photo = re.search(re_photo, x)
    photo = photo.groups()[0] if photo else None

    return {
        'name': name,
        'major': major,
        'year': year,
        'dorm': dorm,
        'floor': floor,
        'photo': photo
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
        if data_of(x) != None:
            d[name_of(x)] = data_of(x)


if __name__ == "__main__":
    main()
