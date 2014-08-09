import sys
import os
import time
import datetime

import requests
from bs4 import BeautifulSoup

def page_has_listings(listings_page):
	soup = BeautifulSoup(listings_page)

	print soup.prettify

	status = False
	return status

def main(listings_dir):

	# Make dir for listing pages.
	if not os.path.exists(listings_dir):
		os.makedirs(listings_dir)

	today_date = datetime.date.today().strftime('%d%m%Y')
	for page_id in range(10000,100000):

		# Paginate from earliest date to today.
		listings_page_url = 'http://www.cubisima.com/casas/anuncios/%s/?fdate=08072010&sdate=%s' % (page_id, today_date)

		# Fetch listings page.
		print >> sys.stderr, 'Fetching %s' % listings_page_url
		listings_page = requests.get(listings_page_url)

		# Save HTML to disk.
		with open(listings_dir + 'file.txt', 'w') as f:
			f.write(listings_page.encode('utf-8'))


		if page_has_listings(listings_page):
			break

		time.sleep(1)

if __name__ == '__main__':
	main(sys.argv[1])