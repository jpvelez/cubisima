#!/usr/bin/env python

"""Get all individual listings pages from every listings page.""" 

import sys
import os
import time
import logging
logging.getLogger().setLevel(logging.INFO)

import requests
from bs4 import BeautifulSoup

domain = 'http://www.cubisima.com'

def listing_already_downloaded(listings_dir, listing_url):
	"""Check if the listing page has already been downloaded."""

	filename = listing_url.replace('/', '_')
	if os.path.exists(listings_dir + '/' + filename):
		return True
	else:
		return False


def fetch_listing(listings_dir, listing_url):
	"""Fetch individual listing page html."""

	logging.info("Fetching %s" % listing_url)
	listing = requests.get(listing_url)

	# If you successfully get the file, save it to disk.
	if listing.status_code == 200:
		filename = listing_url.replace('/', '_')
		with open(listings_dir + '/' + filename, 'w') as f:
			f.write(listing.text.encode('utf-8'))
	else:
		logging.warning("No page at this url: %s" % listing_url)

	# Be compasionate.
	time.sleep(2)


def get_listings_on_page(listings_dir, listing_page):
	"""Fetch all individual listings on a listing page, if you don't already have them."""

	# Loop through listings table rows in listings html table.
	for listing_table_row in listing_page.find_all(class_='casa_repeater'):
		
		# Extract individual listing page url.
		listing_address = listing_table_row.find(class_='renta_descripcion').a['href']
		listing_url = domain + listing_address

		# If file has already been downloaded, do nothing.
		if listing_already_downloaded(listings_dir, listing_url):
			logging.info("Already downloaded file: %s" % listing_url)

		# If not, download it!
		else:
			fetch_listing(listings_dir, listing_url)
			

def main(listing_pages_dir, listings_dir, listing_page_files):

	# Loop through listing page files.
	for listing_page_file in listing_page_files:

		# Parse HTML of given listings page.
		listing_page = BeautifulSoup(open(listing_pages_dir + '/' + listing_page_file, 'r'))
		
		# Get listings on that page.
		get_listings_on_page(listings_dir, listing_page)


if __name__ == '__main__':
	main(sys.argv[1], sys.argv[2], sys.argv[3:])	# Listing page files passed in through xargs.