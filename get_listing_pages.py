#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Fetch all real estate listing pages from Cubisima.com.
"""

import sys
import os
import time
import datetime
import requests
from bs4 import BeautifulSoup
import logging


def page_has_listings(listings_page):
    """
    Detect if a Cubisima listing page actually has listings.

    If you paginate to a page with no listings on Cubisima.com,
    you don't get a 404. You get a real page, but with no listings
    on it. This helper function catches those situations.
    """
    # divs with class "casa_repeater" wrap individual listings
    # in main listings table.
    listings = BeautifulSoup(listings_page).find_all(class_='casa_repeater')
    if len(listings) > 0:
        return True
    else:
        return False


def main(listings_dir_base):
    # Make logs and dirs for listing pages using today's date.
    today_date = datetime.date.today().strftime('%d%m%Y')
    listings_dir = listings_dir_base + today_date + '/'
    logging.basicConfig(filename='logs/%s_listing_pages.log' % today_date,
                        level=logging.INFO)
    # Make path for listing pages, if it doesn't exist.
    os.makedirs(listings_dir, exist_ok=True)

    for page_id in range(531, 100000):
        # Paginate from earliest date to today.
        listings_page_url = 'http://www.cubisima.com/casas/anuncios/' \
                            + '%s/?fdate=08072010&sdate=%s' \
                            % (page_id, today_date)

        # Fetch listings page.
        logging.info('Fetching %s' % listings_page_url)
        response = requests.get(listings_page_url)
        listings_page = response.text
        response.connection.close()

        # Save HTML to disk.
        filename = listings_page_url.replace('http://', '').replace('/', '_')
        with open(listings_dir + filename, mode='w', encoding='utf-8') as f:
            f.write(listings_page)

        # Stop fetching pages when you hit one with no listings.
        # New listings are added every day to the page with 0,
        # so older listings are pushed to higher-numbered pages.
        if not page_has_listings(listings_page):
            logging.info('This page has no listings. Stopping the fetch.')
            break

        # Don't be a sociopath.
        time.sleep(5)

if __name__ == '__main__':
    main(sys.argv[1])
