#!/usr/bin/env python

"""Fetch all real estate listing pages from Cubisima.com"""

import sys
import os
import time
import datetime
import logging
logging.basicConfig(filename='scraper.log',level=logging.INFO)

import requests
from bs4 import BeautifulSoup

def page_has_listings(listings_page):
	"""
	Detect if a Cubisima listing page actually has listings.

	If you paginate to a page with no listings on Cubisima.com, 
	you don't get a 404. You get a real page, but with no listings
	 on it. This helps you catch those situations.
	"""
	# divs with class "casa_repeater" wrap listings in the main listings table.
	listings = BeautifulSoup(listings_page).find_all(class_='casa_repeater')

	if len(listings) > 0:
		return True
	else:
		return False

def main(listings_dir):

	# Make dir for listing pages.
	if not os.path.exists(listings_dir):
		print 'making %s' % listings_dir
		os.makedirs(listings_dir)

	today_date = datetime.date.today().strftime('%d%m%Y')
	for page_id in range(0,100000):

		# Paginate from earliest date to today.
		listings_page_url = 'http://www.cubisima.com/casas/anuncios/%s/?fdate=08072010&sdate=%s' % (page_id, today_date)

		# Fetch listings page.
		logging.info('Fetching %s' % listings_page_url)
		listings_page = requests.get(listings_page_url).text

		# Save HTML to disk.
		filename = listings_page_url.replace('http://', '').replace('/', '_')
		with open(listings_dir + '/' + filename, 'w') as f:
			f.write(listings_page.encode('utf-8'))

		# Stop fetching pages when you hit on with no listings.
		# New listings are added every day, so older listings 
		# are pushed to higher-numbered pages. 
		if not page_has_listings(listings_page):
			logging.info('This page has no listings. Stopping the fetch.')
			break

		# Don't be a sociopath.
		time.sleep(2)

if __name__ == '__main__':
	main(sys.argv[1])